"""
Interview Timer Service
───────────────────────
Manages per-question and total interview timers.

Timer rules:
  - Each question has a time limit (default 5 min, configurable by difficulty)
  - Total interview has a time limit (default 45 min)
  - If question timer expires → auto-advance to next question
  - If total timer expires → interview completes
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import settings


# Time limits by difficulty level (seconds per question)
QUESTION_TIME_LIMITS = {
    "junior": 240,     # 4 min
    "mid": 300,        # 5 min
    "senior": 360,     # 6 min
    "architect": 420,  # 7 min
}

# Total interview time limits by difficulty (seconds)
TOTAL_TIME_LIMITS = {
    "junior": 1800,    # 30 min
    "mid": 2700,       # 45 min
    "senior": 3600,    # 60 min
    "architect": 4500, # 75 min
}


def get_question_time_limit(difficulty_level: str) -> int:
    """Get time limit for a single question based on difficulty."""
    return QUESTION_TIME_LIMITS.get(difficulty_level, settings.DEFAULT_QUESTION_TIME_SECONDS)


def get_total_time_limit(difficulty_level: str) -> int:
    """Get total interview time limit based on difficulty."""
    return TOTAL_TIME_LIMITS.get(difficulty_level, settings.DEFAULT_TOTAL_TIME_SECONDS)


def check_question_timeout(
    time_taken_seconds: int | None,
    time_limit_seconds: int,
) -> dict:
    """
    Check if a question answer exceeded the time limit.

    Returns:
        dict with timeout status and penalty info.
    """
    if time_taken_seconds is None:
        return {"timed_out": False, "penalty": 0}

    timed_out = time_taken_seconds > time_limit_seconds
    # Penalty: reduce score weight by 10% for timeout
    penalty = 0.10 if timed_out else 0

    return {
        "timed_out": timed_out,
        "time_taken": time_taken_seconds,
        "time_limit": time_limit_seconds,
        "penalty": penalty,
        "message": (
            "⏰ Time limit exceeded. A small penalty has been applied."
            if timed_out
            else None
        ),
    }


def check_total_interview_timeout(
    started_at: datetime | None,
    total_time_limit_seconds: int,
) -> dict:
    """
    Check if the total interview time has been exceeded.

    Returns:
        dict with timeout status and remaining time.
    """
    if started_at is None:
        return {"expired": False, "remaining_seconds": total_time_limit_seconds}

    now = datetime.now(timezone.utc)
    elapsed = (now - started_at).total_seconds()
    remaining = max(0, total_time_limit_seconds - elapsed)

    return {
        "expired": remaining <= 0,
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "total_limit_seconds": total_time_limit_seconds,
    }
