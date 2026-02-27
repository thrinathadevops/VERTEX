from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class SessionCreate(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=150)
    candidate_email: EmailStr
    target_role: str = Field(min_length=2, max_length=150)


class SessionResponse(BaseModel):
    id: str
    status: str
    first_question: str


class AnswerSubmit(BaseModel):
    answer: str = Field(min_length=5)


class AnswerResponse(BaseModel):
    score: float
    feedback: str
    next_question: str | None
    status: str


class ReportResponse(BaseModel):
    session_id: str
    status: str
    answered_turns: int
    average_score: float
    recommendation: str
    generated_at: datetime
