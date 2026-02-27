"""
AI Interview models module.

This module re-exports the current interview ORM models so the AI Interview
application can be separated without breaking existing behavior.
"""

from app.models.interview_models import (  # noqa: F401
    CandidateProfile,
    InterviewSession,
    InterviewStatus,
    InterviewTurn,
    JobDescription,
    ScoreReport,
)

