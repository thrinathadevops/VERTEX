"""
AI Interview core service module.

This module re-exports session orchestration functions from the current
implementation while the app is being modularized.
"""

from app.services.interview_service import (  # noqa: F401
    get_current_turn,
    start_session,
    submit_answer,
)

