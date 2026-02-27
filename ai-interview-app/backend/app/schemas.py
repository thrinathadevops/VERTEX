"""
Pydantic Schemas
────────────────
All request / response schemas for the VAREX AI Interview Platform.
Covers: Auth, Sessions, Answers, Reports, Pricing, Anti-Cheat,
Enterprise Dashboard, and Admin Analytics.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════════════
#  AUTH SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="candidate", pattern="^(candidate|enterprise_admin|super_admin)$")
    company_name: str | None = Field(default=None, max_length=180)
    company_code: str | None = Field(default=None, max_length=80)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    full_name: str


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company_name: str | None = None
    free_mock_used: bool
    is_active: bool
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════
#  INTERVIEW SESSION SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class SessionCreate(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=150)
    candidate_email: EmailStr
    target_role: str = Field(min_length=2, max_length=150)
    interview_mode: str = Field(
        default="mock_free",
        pattern="^(mock_free|mock_paid|enterprise)$",
    )
    difficulty_level: str = Field(
        default="mid",
        pattern="^(junior|mid|senior|architect)$",
    )
    company_name: str | None = Field(default=None, max_length=180)
    company_interview_code: str | None = Field(default=None, max_length=80)
    package_interviews: int = Field(default=1, ge=1, le=1000)


class SessionResponse(BaseModel):
    id: str
    status: str
    interview_mode: str
    difficulty_level: str
    package_interviews: int
    discount_percent: int
    base_total_rupees: int
    charge_rupees: int
    payment_required: bool
    ai_introduction: str
    first_question: str
    first_question_phase: str
    resume_uploaded: bool
    total_questions: int
    total_time_limit_seconds: int
    question_time_limit_seconds: int


# ═══════════════════════════════════════════════════════════════════
#  ANSWER SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class AnswerSubmit(BaseModel):
    answer: str = Field(min_length=5)
    time_taken_seconds: int | None = Field(default=None, ge=0)


class AnswerResponse(BaseModel):
    turn_number: int
    total_questions: int
    status: str
    # Scores are NOT shown during interview (evaluated async in background)
    evaluation_status: str  # "pending" | "evaluating" | "evaluated"
    next_question: str | None = None
    next_question_phase: str | None = None
    next_question_time_limit: int | None = None
    # Detail only visible AFTER interview completes
    score: float | None = None
    feedback: str | None = None
    dimension_scores: dict | None = None
    improvement_tips: list[str] | None = None
    strengths: list[str] | None = None


# ═══════════════════════════════════════════════════════════════════
#  REPORT SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class ScoreBreakdown(BaseModel):
    technical_depth: float  # 40% weight
    scenario_handling: float  # 25% weight
    communication: float  # 20% weight
    confidence: float  # 15% weight
    weighted_total: float


class ReportResponse(BaseModel):
    session_id: str
    status: str
    interview_mode: str
    difficulty_level: str
    answered_turns: int
    total_questions: int
    average_score: float
    score_breakdown: ScoreBreakdown | None = None
    recommendation: str
    generated_at: datetime
    # AI-generated deep report (paid modes)
    ai_report: dict | None = None
    anti_cheat_summary: dict | None = None


# ═══════════════════════════════════════════════════════════════════
#  ELIGIBILITY & PRICING SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class EligibilityResponse(BaseModel):
    eligible: bool
    free_mock_used: bool
    mock_count: int
    enterprise_count: int
    next_mock_charge_rupees: int


class PricingRequest(BaseModel):
    interview_mode: str = Field(pattern="^(mock_free|mock_paid|enterprise)$")
    package_interviews: int = Field(default=1, ge=1, le=1000)


class PricingResponse(BaseModel):
    interview_mode: str
    package_interviews: int
    base_price_per_interview: int
    discount_percent: int
    base_total_rupees: int
    discount_amount_rupees: int
    final_charge_rupees: int


# ═══════════════════════════════════════════════════════════════════
#  RESUME SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class ResumeUploadResponse(BaseModel):
    session_id: str
    resume_parsed: bool
    skill_profile: dict | None = None
    skills: list[str]
    summary: str


# ═══════════════════════════════════════════════════════════════════
#  ANTI-CHEAT SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class AntiCheatEventCreate(BaseModel):
    event_type: str = Field(
        pattern=(
            "^(tab_switch|window_blur|copy_paste|right_click"
            "|ai_app_detected|ai_network_connection|non_browser_window"
            "|ai_browser_tab|virtual_machine_detected|remote_desktop_detected"
            "|multiple_monitors_detected|proctor_started|proctor_stopped"
            "|proctor_disconnected|ai_text_detected|paste_detected)$"
        )
    )
    details: str | None = None


class AntiCheatSummary(BaseModel):
    session_id: str
    # Browser-level
    tab_switch_count: int
    # OS-level proctor
    proctor_connected: bool
    proctor_heartbeat_count: int
    proctor_environment: dict | None = None
    ai_violations_count: int
    # Aggregated
    integrity_score: int
    integrity_grade: str
    suspicious: bool
    total_events: int
    critical_events: int
    warning_events: int
    events: list[dict]


# ═══════════════════════════════════════════════════════════════════
#  ENTERPRISE DASHBOARD SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class CandidateRanking(BaseModel):
    candidate_name: str
    candidate_email: str
    session_id: str
    target_role: str
    difficulty_level: str
    average_score: float
    score_breakdown: ScoreBreakdown | None = None
    recommendation: str
    status: str
    completed_at: datetime | None = None


class EnterpriseDashboard(BaseModel):
    company_name: str
    total_interviews: int
    completed_interviews: int
    average_score: float
    candidates: list[CandidateRanking]
    skill_gap_analytics: dict | None = None


# ═══════════════════════════════════════════════════════════════════
#  ADMIN ANALYTICS SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class AdminAnalytics(BaseModel):
    total_users: int
    total_sessions: int
    sessions_by_status: dict[str, int]
    sessions_by_mode: dict[str, int]
    sessions_by_difficulty: dict[str, int]
    average_score: float
    total_revenue_rupees: int
    revenue_by_mode: dict[str, int]
    top_roles: list[dict]
    recent_sessions: list[dict]
