"""
Report Generator Service
────────────────────────
Generates downloadable CSV reports for enterprise dashboards.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import InterviewSession, InterviewTurn


def generate_csv_report(
    db: Session,
    company_name: str | None = None,
    company_code: str | None = None,
) -> str:
    """
    Generate a CSV report of all interview sessions for a company.

    Returns:
        CSV string content.
    """
    query = select(InterviewSession).order_by(
        InterviewSession.created_at.desc()
    )

    if company_name:
        query = query.where(InterviewSession.company_name == company_name)
    if company_code:
        query = query.where(InterviewSession.company_interview_code == company_code)

    sessions = db.scalars(query).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Session ID",
        "Candidate Name",
        "Candidate Email",
        "Target Role",
        "Difficulty Level",
        "Interview Mode",
        "Status",
        "Questions Answered",
        "Average Score",
        "Technical Depth (40%)",
        "Scenario Handling (25%)",
        "Communication (20%)",
        "Confidence (15%)",
        "Weighted Total",
        "Recommendation",
        "Suspicious Activity",
        "Tab Switches",
        "Duration (min)",
        "Created At",
        "Completed At",
    ])

    for s in sessions:
        # Count answered turns
        answered = db.scalar(
            select(func.count(InterviewTurn.id)).where(
                InterviewTurn.session_id == s.id,
                InterviewTurn.answer.is_not(None),
            )
        ) or 0

        avg_score = db.scalar(
            select(func.coalesce(func.avg(InterviewTurn.score), 0.0)).where(
                InterviewTurn.session_id == s.id,
                InterviewTurn.score.is_not(None),
            )
        ) or 0.0

        # Recommendation from AI report
        recommendation = "N/A"
        if s.ai_report:
            try:
                report = json.loads(s.ai_report)
                recommendation = report.get("recommendation", "N/A")
            except (json.JSONDecodeError, TypeError):
                pass

        # Duration
        duration_min = ""
        if s.started_at and s.completed_at:
            duration_min = round((s.completed_at - s.started_at).total_seconds() / 60, 1)

        writer.writerow([
            s.id,
            s.candidate_name,
            s.candidate_email,
            s.target_role,
            s.difficulty_level,
            s.interview_mode,
            s.status,
            answered,
            round(float(avg_score), 2),
            s.score_technical_depth or "",
            s.score_scenario_handling or "",
            s.score_communication or "",
            s.score_confidence or "",
            s.score_weighted_total or "",
            recommendation,
            "Yes" if s.suspicious_activity else "No",
            s.tab_switch_count,
            duration_min,
            s.created_at.isoformat() if s.created_at else "",
            s.completed_at.isoformat() if s.completed_at else "",
        ])

    return output.getvalue()
