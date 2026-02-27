from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class SessionCreate(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=150)
    candidate_email: EmailStr
    target_role: str = Field(min_length=2, max_length=150)
    interview_mode: str = Field(default="mock_free", pattern="^(mock_free|mock_paid|real)$")


class SessionResponse(BaseModel):
    id: str
    status: str
    interview_mode: str
    first_question: str


class AnswerSubmit(BaseModel):
    answer: str = Field(min_length=5)


class AnswerResponse(BaseModel):
    score: float
    feedback: str
    next_question: str | None
    status: str
    turn_number: int
    total_questions: int


class ReportResponse(BaseModel):
    session_id: str
    status: str
    interview_mode: str
    answered_turns: int
    total_questions: int
    average_score: float
    recommendation: str
    generated_at: datetime


class EligibilityResponse(BaseModel):
    eligible: bool
    free_mock_used: bool
    mock_count: int
    real_count: int
