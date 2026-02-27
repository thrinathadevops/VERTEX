"""
AI Interview schemas module.

This module re-exports the current interview schema contracts so API clients
remain unchanged while the codebase is split into a dedicated application.
"""

from app.schemas.interview import (  # noqa: F401
    ATSScanRequest,
    ATSScanResponse,
    CandidateCreate,
    CandidateResponse,
    InterviewRound,
    JobDescriptionCreate,
    JobDescriptionResponse,
    ScoreReportResponse,
    SessionCreate,
    SessionResponse,
    TurnAnswerRequest,
    TurnResponse,
)

