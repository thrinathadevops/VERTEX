"""
Enterprise Dashboard Routes
────────────────────────────
B2B features for companies to track candidate performance:
  - Candidate ranking by score
  - Average score analytics
  - Skill gap analysis
  - CSV report download
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user, require_role
from ..database import get_db
from ..models import InterviewSession, InterviewTurn, User
from ..schemas import CandidateRanking, EnterpriseDashboard, ScoreBreakdown
from ..services.report_generator import generate_csv_report

router = APIRouter(prefix="/api/v1/enterprise", tags=["Enterprise Dashboard"])


@router.get("/dashboard", response_model=EnterpriseDashboard)
def get_enterprise_dashboard(
    user: User = Depends(require_role("enterprise_admin", "super_admin")),
    db: Session = Depends(get_db),
):
    """Get enterprise dashboard with candidate rankings and analytics."""
    if not user.company_name:
        raise HTTPException(
            status_code=400,
            detail="No company associated with your account.",
        )

    company = user.company_name

    # Get all enterprise sessions for this company
    sessions = db.scalars(
        select(InterviewSession)
        .where(
            InterviewSession.company_name == company,
            InterviewSession.interview_mode == "enterprise",
        )
        .order_by(InterviewSession.created_at.desc())
    ).all()

    candidates: list[CandidateRanking] = []
    total_score = 0.0
    scored_count = 0

    for s in sessions:
        avg_score = db.scalar(
            select(func.coalesce(func.avg(InterviewTurn.score), 0.0)).where(
                InterviewTurn.session_id == s.id,
                InterviewTurn.score.is_not(None),
            )
        ) or 0.0

        # Score breakdown
        breakdown = None
        if s.score_weighted_total is not None:
            breakdown = ScoreBreakdown(
                technical_depth=s.score_technical_depth or 0.0,
                scenario_handling=s.score_scenario_handling or 0.0,
                communication=s.score_communication or 0.0,
                confidence=s.score_confidence or 0.0,
                weighted_total=s.score_weighted_total or 0.0,
            )

        # Recommendation
        recommendation = "Pending"
        if s.ai_report:
            try:
                report = json.loads(s.ai_report)
                recommendation = report.get("recommendation", "Pending")
            except (json.JSONDecodeError, TypeError):
                pass
        elif s.status == "completed":
            if avg_score >= 8.5:
                recommendation = "Shortlist"
            elif avg_score >= 7.0:
                recommendation = "Review"
            else:
                recommendation = "Reject"

        candidates.append(CandidateRanking(
            candidate_name=s.candidate_name,
            candidate_email=s.candidate_email,
            session_id=s.id,
            target_role=s.target_role,
            difficulty_level=s.difficulty_level,
            average_score=round(float(avg_score), 2),
            score_breakdown=breakdown,
            recommendation=recommendation,
            status=s.status,
            completed_at=s.completed_at,
        ))

        if avg_score > 0:
            total_score += float(avg_score)
            scored_count += 1

    # Sort candidates by score (highest first)
    candidates.sort(key=lambda c: c.average_score, reverse=True)

    completed = sum(1 for s in sessions if s.status == "completed")
    avg = round(total_score / scored_count, 2) if scored_count > 0 else 0.0

    # ── Skill gap analytics ───────────────────────────────────
    skill_gaps = _compute_skill_gaps(db, [s.id for s in sessions])

    return EnterpriseDashboard(
        company_name=company,
        total_interviews=len(sessions),
        completed_interviews=completed,
        average_score=avg,
        candidates=candidates,
        skill_gap_analytics=skill_gaps,
    )


@router.get("/report/csv")
def download_csv_report(
    user: User = Depends(require_role("enterprise_admin", "super_admin")),
    db: Session = Depends(get_db),
):
    """Download CSV report of all company interviews."""
    if not user.company_name:
        raise HTTPException(status_code=400, detail="No company associated.")

    csv_content = generate_csv_report(
        db=db,
        company_name=user.company_name,
        company_code=user.company_code,
    )

    filename = f"varex_report_{user.company_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _compute_skill_gaps(db: Session, session_ids: list[str]) -> dict:
    """Analyze skill gaps across all enterprise interviews."""
    if not session_ids:
        return {"note": "No completed interviews to analyze"}

    # Collect dimension scores across all sessions
    tech_scores = []
    scenario_scores = []
    comm_scores = []
    confidence_scores = []

    for sid in session_ids:
        session = db.get(InterviewSession, sid)
        if session and session.score_weighted_total is not None:
            if session.score_technical_depth is not None:
                tech_scores.append(session.score_technical_depth)
            if session.score_scenario_handling is not None:
                scenario_scores.append(session.score_scenario_handling)
            if session.score_communication is not None:
                comm_scores.append(session.score_communication)
            if session.score_confidence is not None:
                confidence_scores.append(session.score_confidence)

    def avg(lst: list[float]) -> float:
        return round(sum(lst) / len(lst), 1) if lst else 0.0

    def identify_gap(score: float) -> str:
        if score >= 8.0:
            return "Strong"
        if score >= 6.0:
            return "Adequate"
        if score >= 4.0:
            return "Needs Improvement"
        return "Critical Gap"

    result = {
        "technical_depth": {
            "average": avg(tech_scores),
            "status": identify_gap(avg(tech_scores)),
            "sample_size": len(tech_scores),
        },
        "scenario_handling": {
            "average": avg(scenario_scores),
            "status": identify_gap(avg(scenario_scores)),
            "sample_size": len(scenario_scores),
        },
        "communication": {
            "average": avg(comm_scores),
            "status": identify_gap(avg(comm_scores)),
            "sample_size": len(comm_scores),
        },
        "confidence": {
            "average": avg(confidence_scores),
            "status": identify_gap(avg(confidence_scores)),
            "sample_size": len(confidence_scores),
        },
    }

    # Find the weakest area
    areas = {
        "Technical Depth": avg(tech_scores),
        "Scenario Handling": avg(scenario_scores),
        "Communication": avg(comm_scores),
        "Confidence": avg(confidence_scores),
    }
    weakest = min(areas, key=areas.get) if areas else None
    result["weakest_area"] = weakest
    result["recommendation"] = (
        f"Focus training on '{weakest}' — it's the most common gap among your candidates."
        if weakest
        else "Not enough data."
    )

    return result
