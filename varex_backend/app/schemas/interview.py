from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
import enum

class InterviewRound(str, enum.Enum):
    ai_interview = "ai_interview"
    hr_round = "hr_round"
    tech_round = "tech_round"

class JobDescriptionBase(BaseModel):
    title: str
    company: Optional[str] = None
    description: str
    skills: Optional[List[str]] = None

class JobDescriptionCreate(JobDescriptionBase):
    pass

class JobDescriptionResponse(JobDescriptionBase):
    id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    is_active: bool = True
    model_config = {"from_attributes": True}

class CandidateCreate(BaseModel):
    job_id: UUID
    name: str
    email: str

class CandidateResponse(BaseModel):
    id: UUID
    job_id: UUID
    name: str
    email: str
    resume_text: Optional[str] = None
    resume_s3_key: Optional[str] = None
    ats_score: Optional[float] = None
    ats_feedback: Optional[Any] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class ATSScanRequest(BaseModel):
    candidate_id: UUID

class ATSScanResponse(BaseModel):
    candidate_id: UUID
    score: float
    feedback: Any

class SessionCreate(BaseModel):
    candidate_id: UUID
    job_description_id: UUID
    scheduled_at: Optional[datetime] = None
    video_recording_enabled: bool = False

class SessionResponse(BaseModel):
    id: UUID
    job_id: UUID
    candidate_id: UUID
    status: str
    total_score: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class TurnAnswerRequest(BaseModel):
    candidate_answer: str

class TurnResponse(BaseModel):
    id: UUID
    session_id: UUID
    turn_number: int
    question: str
    answer: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class ScoreReportResponse(BaseModel):
    id: UUID
    session_id: UUID
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    communication: Optional[float] = None
    summary: Optional[str] = None
    recommendation: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    model_config = {"from_attributes": True}
