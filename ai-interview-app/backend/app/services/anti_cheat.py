"""
Anti-Cheat Detection Service — v2 (Multi-Layer)
─────────────────────────────────────────────────
5 protection layers:

  Layer 1 — BROWSER LEVEL (client-side)
    Tab switches, window blur, copy/paste, right-click
    → Detected by frontend JavaScript

  Layer 2 — OS-LEVEL PROCTOR AGENT (desktop app)
    Running AI apps, active window monitoring, network connections
    → Detected by proctor_agent.py running on candidate's machine

  Layer 3 — AI TEXT DETECTION (server-side)
    Linguistic patterns, paste detection, style consistency
    → Detected by ai_text_detector.py analyzing answers

  Layer 4 — PROCTOR HEARTBEAT MONITORING
    Verify proctor agent is running throughout the interview
    → Heartbeat gaps = proctor disconnected or killed

  Layer 5 — INTEGRITY SCORING (aggregation)
    Combine all layers into a 0-100 integrity score
    → Score-based penalties and report flags
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import AntiCheatEvent, InterviewSession

logger = logging.getLogger(__name__)


# ─── Integrity score deductions ──────────────────────────────────
INTEGRITY_DEDUCTIONS = {
    # Browser-level events
    "tab_switch": 3,
    "window_blur": 2,
    "copy_paste": 5,
    "right_click": 1,
    # OS-level proctor events (CRITICAL)
    "ai_app_detected": 25,          # ChatGPT, Copilot, etc. detected
    "ai_network_connection": 20,    # Connection to AI API detected
    "non_browser_window": 5,        # Switched to non-browser app
    "ai_browser_tab": 15,           # AI service in browser tab
    "virtual_machine_detected": 15, # Running in VM
    "remote_desktop_detected": 15,  # Remote desktop session
    "multiple_monitors_detected": 0,  # Info only, not a deduction
    # AI text detection events
    "ai_text_detected": 20,         # Answer flagged as AI-generated
    "paste_detected": 10,           # Answer was pasted
    # Proctor events
    "proctor_started": 0,           # Info only
    "proctor_stopped": 10,          # Proctor was closed early
    "proctor_disconnected": 15,     # Heartbeat gap detected
}

# Severity mapping
EVENT_SEVERITY = {
    "tab_switch": "warning",
    "window_blur": "info",
    "copy_paste": "warning",
    "right_click": "info",
    "ai_app_detected": "critical",
    "ai_network_connection": "critical",
    "non_browser_window": "warning",
    "ai_browser_tab": "critical",
    "virtual_machine_detected": "critical",
    "remote_desktop_detected": "critical",
    "multiple_monitors_detected": "info",
    "ai_text_detected": "critical",
    "paste_detected": "warning",
    "proctor_started": "info",
    "proctor_stopped": "warning",
    "proctor_disconnected": "critical",
    "proctor_heartbeat": "info",
}


def record_event(
    db: Session,
    session_id: str,
    event_type: str,
    details: str | None = None,
) -> dict:
    """
    Record an anti-cheat event (from browser, proctor agent, or AI detection).
    Updates session integrity score and counters.
    """
    session = db.get(InterviewSession, session_id)
    if session is None:
        return {"error": "Session not found"}

    severity = EVENT_SEVERITY.get(event_type, "warning")

    # Record the event
    event = AntiCheatEvent(
        session_id=session_id,
        event_type=event_type,
        severity=severity,
        details=details,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(event)

    # ── Update counters ───────────────────────────────────────
    if event_type == "tab_switch":
        session.tab_switch_count += 1

    if event_type in ("ai_app_detected", "ai_network_connection",
                       "ai_browser_tab", "ai_text_detected"):
        session.ai_violations_count += 1

    # ── Update integrity score ────────────────────────────────
    deduction = INTEGRITY_DEDUCTIONS.get(event_type, 0)
    if deduction > 0:
        session.integrity_score = max(0, session.integrity_score - deduction)

    # ── Flag as suspicious ────────────────────────────────────
    if (
        session.tab_switch_count >= settings.MAX_TAB_SWITCHES_BEFORE_FLAG
        or session.ai_violations_count >= 1
        or session.integrity_score < 70
    ):
        session.suspicious_activity = True

    # ── Build response ────────────────────────────────────────
    warning = session.suspicious_activity
    warning_message = None

    if severity == "critical":
        if event_type in ("ai_app_detected", "ai_network_connection"):
            warning_message = (
                "🚨 CRITICAL: AI assistance tool detected on your system. "
                "This has been logged and WILL be included in your interview report. "
                "Please close all AI tools immediately."
            )
        elif event_type == "ai_browser_tab":
            warning_message = (
                "🚨 CRITICAL: AI service detected in your browser. "
                "This has been logged and will significantly impact your integrity score."
            )
        elif event_type == "ai_text_detected":
            warning_message = (
                "⚠️ Your answer has been flagged for potential AI-generated content. "
                "Answers should reflect YOUR actual experience."
            )
    elif warning:
        warning_message = (
            "⚠️ Suspicious activity detected. This will be noted in your interview report."
        )

    db.commit()

    return {
        "recorded": True,
        "event_type": event_type,
        "severity": severity,
        "tab_switch_count": session.tab_switch_count,
        "ai_violations_count": session.ai_violations_count,
        "integrity_score": session.integrity_score,
        "warning": warning,
        "warning_message": warning_message,
    }


def record_proctor_heartbeat(
    db: Session,
    session_id: str,
    heartbeat_data: dict,
) -> dict:
    """
    Process a heartbeat from the desktop proctor agent.
    Updates proctor connectivity status and processes any violations.
    """
    session = db.get(InterviewSession, session_id)
    if session is None:
        return {"error": "Session not found"}

    # ── Update proctor status ─────────────────────────────────
    session.proctor_connected = True
    session.proctor_heartbeat_count += 1
    session.proctor_last_heartbeat = datetime.now(timezone.utc)

    # ── Store environment info (first heartbeat only) ─────────
    if session.proctor_heartbeat_count == 1:
        env_info = heartbeat_data.get("scan_results", {})
        session.proctor_environment = json.dumps(
            heartbeat_data.get("environment", env_info), default=str
        )

    # ── Process violations from this heartbeat ────────────────
    violations = heartbeat_data.get("scan_results", {}).get("violations", [])
    for v in violations:
        # Record each violation as a separate event
        record_event(
            db=db,
            session_id=session_id,
            event_type=v.get("type", "ai_app_detected"),
            details=v.get("details", ""),
        )

    # ── Check if interview should be stopped ──────────────────
    stop_interview = session.integrity_score <= 20 or session.ai_violations_count >= 5

    total_violations = heartbeat_data.get("total_violations", 0)

    db.commit()

    return {
        "acknowledged": True,
        "heartbeat_number": session.proctor_heartbeat_count,
        "integrity_score": session.integrity_score,
        "stop_interview": stop_interview,
        "stop_reason": (
            "Too many integrity violations detected. Interview terminated."
            if stop_interview else None
        ),
    }


def check_proctor_health(
    db: Session,
    session_id: str,
) -> dict:
    """
    Check if the proctor agent is still connected.
    Called periodically from the frontend or backend.
    """
    session = db.get(InterviewSession, session_id)
    if session is None:
        return {"error": "Session not found"}

    proctor_alive = False
    gap_seconds = None

    if session.proctor_last_heartbeat:
        now = datetime.now(timezone.utc)
        gap = (now - session.proctor_last_heartbeat).total_seconds()
        gap_seconds = int(gap)
        # Proctor sends heartbeats every 10 seconds
        # If gap > 30 seconds → proctor is disconnected
        proctor_alive = gap < 30

        if not proctor_alive and session.proctor_connected:
            # Proctor was connected but now disconnected
            session.proctor_connected = False
            record_event(
                db=db,
                session_id=session_id,
                event_type="proctor_disconnected",
                details=f"Proctor heartbeat gap: {gap_seconds} seconds",
            )
            db.commit()
    else:
        if session.proctor_connected:
            proctor_alive = True

    return {
        "proctor_connected": session.proctor_connected,
        "proctor_alive": proctor_alive,
        "heartbeat_count": session.proctor_heartbeat_count,
        "last_heartbeat_gap_seconds": gap_seconds,
        "integrity_score": session.integrity_score,
    }


def get_session_anti_cheat_summary(db: Session, session_id: str) -> dict:
    """Get comprehensive anti-cheat summary for a session."""
    session = db.get(InterviewSession, session_id)
    if session is None:
        return {"error": "Session not found"}

    events = db.scalars(
        select(AntiCheatEvent)
        .where(AntiCheatEvent.session_id == session_id)
        .order_by(AntiCheatEvent.timestamp.asc())
    ).all()

    # Group events by severity
    critical_events = [e for e in events if e.severity == "critical"]
    warning_events = [e for e in events if e.severity == "warning"]

    # Parse proctor environment
    proctor_env = None
    if session.proctor_environment:
        try:
            proctor_env = json.loads(session.proctor_environment)
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "session_id": session_id,
        # Browser-level
        "tab_switch_count": session.tab_switch_count,
        # OS-level
        "proctor_connected": session.proctor_connected,
        "proctor_heartbeat_count": session.proctor_heartbeat_count,
        "proctor_environment": proctor_env,
        "ai_violations_count": session.ai_violations_count,
        # Aggregated
        "integrity_score": session.integrity_score,
        "integrity_grade": _integrity_grade(session.integrity_score),
        "suspicious": session.suspicious_activity,
        "total_events": len(events),
        "critical_events": len(critical_events),
        "warning_events": len(warning_events),
        "events": [
            {
                "type": e.event_type,
                "severity": e.severity,
                "details": e.details,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ],
    }


def _integrity_grade(score: int) -> str:
    """Convert integrity score to human-readable grade."""
    if score >= 90:
        return "A — Clean"
    if score >= 75:
        return "B — Minor Concerns"
    if score >= 50:
        return "C — Significant Concerns"
    if score >= 25:
        return "D — Major Integrity Issues"
    return "F — Interview Integrity Compromised"
