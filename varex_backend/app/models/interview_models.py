# PATH: varex_backend/app/models/interview_models.py
# FIX: Separated ORM models from API router (Bug 1.2, 1.9, 1.10)
# DELETE varex_backend/app/models/interview.py after placing this file

import uuid
import enum
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, Float, Boolean, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class InterviewStatus(str, enum.Enum):
    pending    = "pending"
    active     = "active"
    completed  = "completed"
    cancelled  = "cancelled"


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title       = Column(String(500), nullable=False)
    company     = Column(String(255), nullable=True)
    description = Column(Text,        nullable=False)
    skills      = Column(JSONB,       nullable=True)   # list of required skills
    created_by  = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    sessions   = relationship("InterviewSession", back_populates="job_description")
    candidates = relationship("CandidateProfile",  back_populates="job_description")


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id          = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    name            = Column(String(255), nullable=False)
    email           = Column(String(255), nullable=False)
    resume_text     = Column(Text,        nullable=True)
    resume_s3_key   = Column(Text,        nullable=True)
    ats_score       = Column(Float,       nullable=True)
    ats_feedback    = Column(JSONB,       nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    job_description = relationship("JobDescription", back_populates="candidates")
    sessions        = relationship("InterviewSession", back_populates="candidate")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id         = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id",  ondelete="CASCADE"), nullable=False)
    candidate_id   = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    status         = Column(Enum(InterviewStatus), default=InterviewStatus.pending, nullable=False)
    total_score    = Column(Float,   nullable=True)
    started_at     = Column(DateTime(timezone=True), nullable=True)
    completed_at   = Column(DateTime(timezone=True), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    job_description = relationship("JobDescription",  back_populates="sessions")
    candidate       = relationship("CandidateProfile", back_populates="sessions")
    turns           = relationship("InterviewTurn",    back_populates="session", cascade="all, delete-orphan")
    report          = relationship("ScoreReport",      back_populates="session",  uselist=False)


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id  = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    question    = Column(Text,    nullable=False)
    answer      = Column(Text,    nullable=True)
    score       = Column(Float,   nullable=True)
    feedback    = Column(Text,    nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="turns")


class ScoreReport(Base):
    __tablename__ = "score_reports"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id      = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    overall_score   = Column(Float,  nullable=True)
    technical_score = Column(Float,  nullable=True)
    communication   = Column(Float,  nullable=True)
    summary         = Column(Text,   nullable=True)
    recommendation  = Column(String(50), nullable=True)   # hire / reject / consider
    details         = Column(JSONB,  nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="report")
