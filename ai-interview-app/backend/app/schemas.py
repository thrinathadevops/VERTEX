from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class SessionCreate(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=150)
    candidate_email: EmailStr
    target_role: str = Field(min_length=2, max_length=150)
    interview_mode: str = Field(default="mock_free", pattern="^(mock_free|mock_paid|real)$")
    company_name: str | None = Field(default=None, max_length=180)
    company_interview_code: str | None = Field(default=None, max_length=80)
    package_interviews: int = Field(default=1, ge=1, le=1000)


class SessionResponse(BaseModel):
    id: str
    status: str
    interview_mode: str
    package_interviews: int
    discount_percent: int
    base_total_rupees: int
    charge_rupees: int
    payment_required: bool
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
    next_mock_charge_rupees: int
