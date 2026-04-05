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

from ..ai import engine as ai_engine
from ..auth.deps import require_role
from ..database import get_db
from ..models import AntiCheatEvent, InterviewSession, InterviewTurn, User
from ..schemas import (
    CandidateRanking,
    EnterpriseDashboard,
    LiveControlCenterDetail,
    LiveControlCenterResponse,
    LiveControlCenterSession,
    ManualReviewStopRequest,
    ScoreBreakdown,
)
from ..services.anti_cheat import check_proctor_health, get_session_anti_cheat_summary
from ..services.report_generator import generate_csv_report

router = APIRouter(prefix="/api/v1/enterprise", tags=["Enterprise Dashboard"])
QUESTION_COUNTS = ai_engine.QUESTION_COUNTS


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


@router.get("/live-control-center", response_model=LiveControlCenterResponse)
def get_live_control_center(
    user: User = Depends(require_role("enterprise_admin", "super_admin")),
    db: Session = Depends(get_db),
):
    sessions = _get_scoped_enterprise_sessions(db, user)
    live_sessions = [_build_live_session_card(db, session) for session in sessions if session.status in ("scheduled", "in_progress", "evaluating")]
    recent_sessions = [_build_live_session_card(db, session) for session in sessions[:12]]

    return LiveControlCenterResponse(
        company_name=user.company_name if user.role != "super_admin" or user.company_name else None,
        active_sessions=live_sessions,
        recent_sessions=recent_sessions,
    )


@router.get("/session/{session_id}/live-control-center", response_model=LiveControlCenterDetail)
def get_live_control_center_detail(
    session_id: str,
    user: User = Depends(require_role("enterprise_admin", "super_admin")),
    db: Session = Depends(get_db),
):
    session = _get_scoped_session(db, user, session_id)
    summary = get_session_anti_cheat_summary(db, session_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])

    return LiveControlCenterDetail(
        session=_build_live_session_card(db, session, summary=summary),
        event_feed=summary["events"][-30:][::-1],
    )


@router.post("/session/{session_id}/stop")
def stop_enterprise_session(
    session_id: str,
    payload: ManualReviewStopRequest,
    user: User = Depends(require_role("enterprise_admin", "super_admin")),
    db: Session = Depends(get_db),
):
    session = _get_scoped_session(db, user, session_id)

    if session.status == "completed":
        return {"message": "Interview already completed.", "status": session.status}

    answered = db.scalar(
        select(func.count(InterviewTurn.id)).where(
            InterviewTurn.session_id == session_id,
            InterviewTurn.answer.is_not(None),
        )
    ) or 0

    event = AntiCheatEvent(
        session_id=session.id,
        event_type="reviewer_manual_stop",
        severity="warning",
        details=(payload.reason or f"Interview manually stopped by reviewer {user.full_name}.")[:500],
        timestamp=datetime.now(timezone.utc),
    )
    db.add(event)

    session.suspicious_activity = True
    session.status = "evaluating" if answered > 0 else "completed"
    if session.status == "completed":
        session.completed_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Interview stopped by reviewer.",
        "status": session.status,
        "reason": event.details,
    }


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


def _get_scoped_enterprise_sessions(db: Session, user: User) -> list[InterviewSession]:
    query = select(InterviewSession).where(InterviewSession.interview_mode == "enterprise")
    if user.role != "super_admin" or user.company_name:
        if not user.company_name:
            raise HTTPException(status_code=400, detail="No company associated with your account.")
        query = query.where(InterviewSession.company_name == user.company_name)

    return db.scalars(query.order_by(InterviewSession.created_at.desc())).all()


def _get_scoped_session(db: Session, user: User, session_id: str) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if not session or session.interview_mode != "enterprise":
        raise HTTPException(status_code=404, detail="Enterprise interview session not found.")

    if user.role != "super_admin" or user.company_name:
        if session.company_name != user.company_name:
            raise HTTPException(status_code=403, detail="You do not have access to this interview session.")

    return session


def _build_live_session_card(
    db: Session,
    session: InterviewSession,
    *,
    summary: dict | None = None,
) -> LiveControlCenterSession:
    if summary is None:
        summary = get_session_anti_cheat_summary(db, session.id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])

    health = check_proctor_health(db, session.id)
    if "error" in health:
        raise HTTPException(status_code=404, detail=health["error"])

    answered = db.scalar(
        select(func.count(InterviewTurn.id)).where(
            InterviewTurn.session_id == session.id,
            InterviewTurn.answer.is_not(None),
        )
    ) or 0
    evaluated = db.scalar(
        select(func.count(InterviewTurn.id)).where(
            InterviewTurn.session_id == session.id,
            InterviewTurn.evaluation_status == "evaluated",
        )
    ) or 0
    current_turn = db.scalar(
        select(func.max(InterviewTurn.turn_number)).where(
            InterviewTurn.session_id == session.id,
        )
    ) or 0

    reviewer_alert = None
    if summary.get("risk_level") == "critical":
        reviewer_alert = "Integrity is critically low. Reviewer attention is required."
    elif summary.get("suspicious"):
        reviewer_alert = "Suspicious activity threshold has been crossed."
    elif health.get("proctor_connected") and not health.get("proctor_alive"):
        reviewer_alert = "Proctor heartbeat was lost during the interview."

    return LiveControlCenterSession(
        session_id=session.id,
        candidate_name=session.candidate_name,
        candidate_email=session.candidate_email,
        target_role=session.target_role,
        company_name=session.company_name,
        company_interview_code=session.company_interview_code,
        interview_mode=session.interview_mode,
        difficulty_level=session.difficulty_level,
        status=session.status,
        current_turn=int(current_turn),
        answered=int(answered),
        evaluated=int(evaluated),
        total_questions=QUESTION_COUNTS.get(session.interview_mode, 5),
        integrity_score=session.integrity_score,
        integrity_grade=summary.get("integrity_grade", "Unknown"),
        risk_level=summary.get("risk_level", "watch"),
        suspicious_activity=session.suspicious_activity,
        tab_switch_count=session.tab_switch_count,
        ai_violations_count=session.ai_violations_count,
        total_events=summary.get("total_events", 0),
        critical_events=summary.get("critical_events", 0),
        warning_events=summary.get("warning_events", 0),
        proctor_connected=health.get("proctor_connected", False),
        proctor_alive=health.get("proctor_alive", False),
        proctor_heartbeat_count=health.get("heartbeat_count", 0),
        last_heartbeat_gap_seconds=health.get("last_heartbeat_gap_seconds"),
        last_event_type=summary.get("recent_event_type"),
        last_event_at=datetime.fromisoformat(summary["recent_event_at"]) if summary.get("recent_event_at") else None,
        reviewer_alert=reviewer_alert,
        started_at=session.started_at,
        created_at=session.created_at,
    )
