"""
Admin Analytics Routes
──────────────────────
Platform-wide analytics for super admins.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth.deps import require_role
from ..database import get_db
from ..models import InterviewSession, InterviewTurn, User
from ..schemas import AdminAnalytics

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Analytics"])


@router.get("/analytics", response_model=AdminAnalytics)
def get_analytics(
    _user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db),
):
    """Get platform-wide analytics. Super admin only."""

    # ── Total users ───────────────────────────────────────────
    total_users = db.scalar(select(func.count(User.id))) or 0

    # ── Total sessions ────────────────────────────────────────
    total_sessions = db.scalar(select(func.count(InterviewSession.id))) or 0

    # ── Sessions by status ────────────────────────────────────
    status_rows = db.execute(
        select(
            InterviewSession.status,
            func.count(InterviewSession.id),
        ).group_by(InterviewSession.status)
    ).all()
    sessions_by_status = {row[0]: row[1] for row in status_rows}

    # ── Sessions by mode ──────────────────────────────────────
    mode_rows = db.execute(
        select(
            InterviewSession.interview_mode,
            func.count(InterviewSession.id),
        ).group_by(InterviewSession.interview_mode)
    ).all()
    sessions_by_mode = {row[0]: row[1] for row in mode_rows}

    # ── Sessions by difficulty ────────────────────────────────
    diff_rows = db.execute(
        select(
            InterviewSession.difficulty_level,
            func.count(InterviewSession.id),
        ).group_by(InterviewSession.difficulty_level)
    ).all()
    sessions_by_difficulty = {row[0]: row[1] for row in diff_rows}

    # ── Average score ─────────────────────────────────────────
    average_score = db.scalar(
        select(func.coalesce(func.avg(InterviewTurn.score), 0.0)).where(
            InterviewTurn.score.is_not(None)
        )
    ) or 0.0

    # ── Revenue ───────────────────────────────────────────────
    total_revenue = db.scalar(
        select(func.coalesce(func.sum(InterviewSession.charge_rupees), 0))
    ) or 0

    revenue_by_mode = {}
    rev_rows = db.execute(
        select(
            InterviewSession.interview_mode,
            func.coalesce(func.sum(InterviewSession.charge_rupees), 0),
        ).group_by(InterviewSession.interview_mode)
    ).all()
    for row in rev_rows:
        revenue_by_mode[row[0]] = row[1]

    # ── Top roles ─────────────────────────────────────────────
    role_rows = db.execute(
        select(
            InterviewSession.target_role,
            func.count(InterviewSession.id).label("count"),
        )
        .group_by(InterviewSession.target_role)
        .order_by(func.count(InterviewSession.id).desc())
        .limit(10)
    ).all()
    top_roles = [{"role": row[0], "count": row[1]} for row in role_rows]

    # ── Recent sessions ───────────────────────────────────────
    recent = db.scalars(
        select(InterviewSession)
        .order_by(InterviewSession.created_at.desc())
        .limit(10)
    ).all()
    recent_sessions = [
        {
            "id": s.id,
            "candidate_name": s.candidate_name,
            "target_role": s.target_role,
            "mode": s.interview_mode,
            "difficulty": s.difficulty_level,
            "status": s.status,
            "charge": s.charge_rupees,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in recent
    ]

    return AdminAnalytics(
        total_users=total_users,
        total_sessions=total_sessions,
        sessions_by_status=sessions_by_status,
        sessions_by_mode=sessions_by_mode,
        sessions_by_difficulty=sessions_by_difficulty,
        average_score=round(float(average_score), 2),
        total_revenue_rupees=total_revenue,
        revenue_by_mode=revenue_by_mode,
        top_roles=top_roles,
        recent_sessions=recent_sessions,
    )
