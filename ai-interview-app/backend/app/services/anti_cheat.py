"""
Anti-Cheat Detection Service
─────────────────────────────
Detects and records suspicious activity during interviews:
  - Tab switching
  - Window blur (leaving the browser)
  - Copy/paste attempts
  - Right-click (context menu)

The frontend sends events via API; this service records them
and flags sessions that exceed thresholds.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import AntiCheatEvent, InterviewSession

logger = logging.getLogger(__name__)


def record_event(
    db: Session,
    session_id: str,
    event_type: str,
    details: str | None = None,
) -> dict:
    """
    Record an anti-cheat event and update session counters.

    Returns:
        Summary dict including warning status.
    """
    session = db.get(InterviewSession, session_id)
    if session is None:
        return {"error": "Session not found"}

    # Record the event
    event = AntiCheatEvent(
        session_id=session_id,
        event_type=event_type,
        details=details,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(event)

    # Update counters
    if event_type == "tab_switch":
        session.tab_switch_count += 1

    # Check thresholds
    total_events = db.scalar(
        select(func.count(AntiCheatEvent.id)).where(
            AntiCheatEvent.session_id == session_id
        )
    ) or 0

    # Flag as suspicious if threshold exceeded
    warning = False
    if session.tab_switch_count >= settings.MAX_TAB_SWITCHES_BEFORE_FLAG:
        session.suspicious_activity = True
        warning = True
        logger.warning(
            f"Session {session_id}: flagged as suspicious "
            f"({session.tab_switch_count} tab switches)"
        )

    db.commit()

    return {
        "recorded": True,
        "event_type": event_type,
        "tab_switch_count": session.tab_switch_count,
        "total_events": total_events + 1,
        "warning": warning,
        "warning_message": (
            "⚠️ Multiple tab switches detected. This will be noted in your interview report."
            if warning
            else None
        ),
    }


def get_session_anti_cheat_summary(db: Session, session_id: str) -> dict:
    """Get anti-cheat summary for a session."""
    session = db.get(InterviewSession, session_id)
    if session is None:
        return {"error": "Session not found"}

    events = db.scalars(
        select(AntiCheatEvent)
        .where(AntiCheatEvent.session_id == session_id)
        .order_by(AntiCheatEvent.timestamp.asc())
    ).all()

    return {
        "session_id": session_id,
        "tab_switch_count": session.tab_switch_count,
        "total_events": len(events),
        "suspicious": session.suspicious_activity,
        "events": [
            {
                "type": e.event_type,
                "details": e.details,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ],
    }
