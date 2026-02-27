"""
Database Models
───────────────
Complete domain model for the VAREX AI Interview Platform.

Models:
  - User (JWT auth, role-based access, free mock tracking)
  - InterviewSession (full interview lifecycle with status FSM)
  - InterviewTurn (per-question data with weighted scoring)
  - AntiCheatEvent (tab switches, window changes)
  - InterviewTimer (per-question + total timers)
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# ═══════════════════════════════════════════════════════════════════
#  USER MODEL
# ═══════════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Role: "candidate" | "enterprise_admin" | "super_admin"
    role: Mapped[str] = mapped_column(
        String(30), default="candidate", nullable=False
    )

    # Company association (for enterprise users)
    company_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    company_code: Mapped[str | None] = mapped_column(String(80), nullable=True)

    # ── Pricing / Free mock tracking ──────────────────────────
    free_mock_used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    sessions = relationship(
        "InterviewSession", back_populates="user", cascade="all, delete-orphan"
    )


# ═══════════════════════════════════════════════════════════════════
#  INTERVIEW SESSION MODEL
# ═══════════════════════════════════════════════════════════════════

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    # ── Owner ─────────────────────────────────────────────────
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    candidate_name: Mapped[str] = mapped_column(String(150), nullable=False)
    candidate_email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    target_role: Mapped[str] = mapped_column(String(150), nullable=False)

    # ── Enterprise fields ─────────────────────────────────────
    company_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    company_interview_code: Mapped[str | None] = mapped_column(
        String(80), nullable=True
    )

    # ── Interview Mode ────────────────────────────────────────
    # "mock_free" | "mock_paid" | "enterprise"
    interview_mode: Mapped[str] = mapped_column(
        String(20), default="mock_free", nullable=False
    )

    # ── Difficulty Level ──────────────────────────────────────
    # "junior" | "mid" | "senior" | "architect"
    difficulty_level: Mapped[str] = mapped_column(
        String(20), default="mid", nullable=False
    )

    # ── Pricing ───────────────────────────────────────────────
    package_interviews: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    discount_percent: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    charge_rupees: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Status FSM ────────────────────────────────────────────
    # "scheduled" → "in_progress" → "evaluating" → "completed"
    status: Mapped[str] = mapped_column(
        String(20), default="scheduled", nullable=False
    )

    # ── AI-powered fields ─────────────────────────────────────
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_parsed: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    skill_profile: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    ai_introduction: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_report: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # ── Weighted Score Breakdown ──────────────────────────────
    # Technical Depth – 40% | Scenario Handling – 25%
    # Communication – 20% | Confidence – 15%
    score_technical_depth: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_scenario_handling: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_communication: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_weighted_total: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Timer / Duration fields ───────────────────────────────
    total_time_limit_seconds: Mapped[int] = mapped_column(
        Integer, default=2700, nullable=False  # 45 min default
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Anti-Cheat ────────────────────────────────────────────
    tab_switch_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    suspicious_activity: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Timestamps ────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="sessions")
    turns = relationship(
        "InterviewTurn",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    anti_cheat_events = relationship(
        "AntiCheatEvent",
        back_populates="session",
        cascade="all, delete-orphan",
    )


# ═══════════════════════════════════════════════════════════════════
#  INTERVIEW TURN MODEL
# ═══════════════════════════════════════════════════════════════════

class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Question metadata ─────────────────────────────────────
    # "ice_breaker" | "resume_validation" | "technical_deep_dive"
    # "scenario_based" | "behavioral" | "closing"
    question_phase: Mapped[str] = mapped_column(
        String(30), default="technical_deep_dive", nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Evaluation ────────────────────────────────────────────
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Detailed scoring (per-dimension) ──────────────────────
    dimension_scores: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    improvement_tips: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # ── Evaluation status ─────────────────────────────────────
    # "pending" | "evaluating" | "evaluated"
    evaluation_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )

    # ── Timer ─────────────────────────────────────────────────
    time_limit_seconds: Mapped[int] = mapped_column(
        Integer, default=300, nullable=False  # 5 min per question default
    )
    time_taken_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Timestamps ────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session = relationship("InterviewSession", back_populates="turns")


# ═══════════════════════════════════════════════════════════════════
#  ANTI-CHEAT EVENT MODEL
# ═══════════════════════════════════════════════════════════════════

class AntiCheatEvent(Base):
    __tablename__ = "anti_cheat_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        index=True,
    )

    # "tab_switch" | "window_blur" | "copy_paste" | "right_click"
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session = relationship("InterviewSession", back_populates="anti_cheat_events")
