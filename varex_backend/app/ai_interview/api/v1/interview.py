"""
AI Interview API router entrypoint.

This module exposes the interview router from the dedicated AI Interview app
namespace while preserving existing endpoint behavior and paths.
"""

from app.api.v1.interview import router  # noqa: F401

