from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import InterviewSession, InterviewTurn
from ..schemas import (
    AnswerResponse,
    AnswerSubmit,
    EligibilityResponse,
    ReportResponse,
    SessionCreate,
    SessionResponse,
)

router = APIRouter(prefix="/api/v1/interview", tags=["AI Interview"])

# ─── Question Banks ───────────────────────────────────────────────
MOCK_QUESTIONS = [
    "Explain a production incident you handled and how you restored service.",
    "How do you design CI/CD for both speed and safe rollback?",
    "How would you secure Kubernetes workloads in a multi-tenant cluster?",
    "Describe your approach for cloud cost optimization without reducing reliability.",
    "How do you define SLOs and use observability to improve system resilience?",
]

REAL_QUESTIONS = [
    "Walk through how you would architect a zero-downtime deployment pipeline for a financial-grade microservices platform.",
    "You discover a lateral-movement attempt in your cluster. Walk us through your incident response playbook, from detection through post-mortem.",
    "Your CTO asks you to cut cloud spend by 30 % while maintaining 99.95 % availability. Describe your FinOps strategy in detail.",
    "Explain how you would migrate a monolith to event-driven microservices, covering data consistency, observability, and rollback concerns.",
    "Design a multi-region disaster-recovery strategy for a SaaS product that processes real-time payments. Include RTO / RPO targets.",
    "Describe how you would implement a comprehensive DevSecOps pipeline that balances security scanning, developer velocity, and compliance.",
    "You must onboard 50 microservices to a service mesh. Walk us through your technical approach, organisational buy-in, and risk mitigation.",
]


def _get_question_bank(mode: str) -> list[str]:
    return REAL_QUESTIONS if mode == "real" else MOCK_QUESTIONS


def _score_answer(answer: str) -> float:
    words = len(answer.split())
    if words >= 120:
        return 9.0
    if words >= 80:
        return 8.0
    if words >= 50:
        return 7.0
    if words >= 30:
        return 6.0
    return 4.5


def _feedback_for(score: float) -> str:
    if score >= 8.5:
        return "Strong answer with clear structure, practical depth, and production awareness."
    if score >= 7.0:
        return "Good answer. Add more metrics, risk controls, and trade-off details."
    if score >= 6.0:
        return "Decent baseline. Improve with clearer architecture decisions and concrete examples."
    return "Response is too shallow. Add operational details, constraints, and outcomes."


def _real_discount_percent(package_interviews: int) -> int:
    if package_interviews >= 20:
        return 50
    if package_interviews >= 10:
        return 30
    if package_interviews >= 5:
        return 10
    if package_interviews >= 2:
        return 5
    return 0


# ─── Check Free Mock Eligibility ──────────────────────────────────
@router.get("/eligibility", response_model=EligibilityResponse)
def check_eligibility(email: str, db: Session = Depends(get_db)):
    mock_count = db.scalar(
        select(func.count(InterviewSession.id)).where(
            InterviewSession.candidate_email == email,
            InterviewSession.interview_mode.in_(["mock_free", "mock_paid"]),
        )
    ) or 0
    real_count = db.scalar(
        select(func.count(InterviewSession.id)).where(
            InterviewSession.candidate_email == email,
            InterviewSession.interview_mode == "real",
        )
    ) or 0

    free_mock_used = mock_count > 0
    return EligibilityResponse(
        eligible=True,
        free_mock_used=free_mock_used,
        mock_count=int(mock_count),
        real_count=int(real_count),
        next_mock_charge_rupees=50 if free_mock_used else 0,
    )


# ─── Create Session ───────────────────────────────────────────────
@router.post("/session", response_model=SessionResponse)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    mode = payload.interview_mode

    # Enforce: only one free mock per email
    if mode == "mock_free":
        existing_free = db.scalar(
            select(func.count(InterviewSession.id)).where(
                InterviewSession.candidate_email == payload.candidate_email,
                InterviewSession.interview_mode == "mock_free",
            )
        ) or 0
        if existing_free > 0:
            raise HTTPException(
                status_code=403,
                detail="Free mock interview already used. Please select Paid Mock (₹50) to continue.",
            )

    if mode == "real":
        if not payload.company_name or not payload.company_name.strip():
            raise HTTPException(status_code=422, detail="Company name is required for real company interviews.")
        if not payload.company_interview_code or not payload.company_interview_code.strip():
            raise HTTPException(status_code=422, detail="Company interview code is required for real company interviews.")

    package_interviews = 1
    discount_percent = 0
    base_total_rupees = 0
    charge_rupees = 0
    if mode == "mock_paid":
        charge_rupees = 50
    elif mode == "real":
        package_interviews = payload.package_interviews
        discount_percent = _real_discount_percent(package_interviews)
        base_total_rupees = package_interviews * 500
        charge_rupees = int(base_total_rupees * (100 - discount_percent) / 100)

    session = InterviewSession(
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        target_role=payload.target_role,
        company_name=payload.company_name.strip() if payload.company_name else None,
        company_interview_code=payload.company_interview_code.strip() if payload.company_interview_code else None,
        interview_mode=mode,
        package_interviews=package_interviews,
        discount_percent=discount_percent,
        charge_rupees=charge_rupees,
        is_paid=mode in ("mock_paid", "real"),
        status="active",
    )
    db.add(session)
    db.flush()

    question_bank = _get_question_bank(mode)
    first_question = question_bank[0]

    db.add(InterviewTurn(session_id=session.id, turn_number=1, question=first_question))
    db.commit()

    return SessionResponse(
        id=session.id,
        status="active",
        interview_mode=mode,
        package_interviews=package_interviews,
        discount_percent=discount_percent,
        base_total_rupees=base_total_rupees if mode == "real" else charge_rupees,
        charge_rupees=charge_rupees,
        payment_required=mode in ("mock_paid", "real"),
        first_question=first_question,
    )


# ─── Submit Answer ────────────────────────────────────────────────
@router.post("/session/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(session_id: str, payload: AnswerSubmit, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    question_bank = _get_question_bank(session.interview_mode)

    pending_turn = db.scalar(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id, InterviewTurn.answer.is_(None))
        .order_by(InterviewTurn.turn_number.asc())
        .limit(1)
    )
    if not pending_turn:
        raise HTTPException(status_code=409, detail="No pending question in this session.")

    score = _score_answer(payload.answer)
    feedback = _feedback_for(score)
    pending_turn.answer = payload.answer
    pending_turn.score = score
    pending_turn.feedback = feedback

    next_question = None
    if pending_turn.turn_number < len(question_bank):
        next_turn_number = pending_turn.turn_number + 1
        next_question = question_bank[next_turn_number - 1]
        db.add(InterviewTurn(session_id=session_id, turn_number=next_turn_number, question=next_question))
    else:
        session.status = "completed"

    db.commit()

    return AnswerResponse(
        score=score,
        feedback=feedback,
        next_question=next_question,
        status=session.status,
        turn_number=pending_turn.turn_number,
        total_questions=len(question_bank),
    )


# ─── Get Report ───────────────────────────────────────────────────
@router.get("/session/{session_id}/report", response_model=ReportResponse)
def get_report(session_id: str, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    question_bank = _get_question_bank(session.interview_mode)

    answered_turns = db.scalar(
        select(func.count(InterviewTurn.id)).where(
            InterviewTurn.session_id == session_id, InterviewTurn.answer.is_not(None)
        )
    ) or 0
    average_score = db.scalar(
        select(func.coalesce(func.avg(InterviewTurn.score), 0.0)).where(
            InterviewTurn.session_id == session_id, InterviewTurn.score.is_not(None)
        )
    ) or 0.0

    recommendation = "Reject"
    if average_score >= 8.5:
        recommendation = "Shortlist"
    elif average_score >= 7.0:
        recommendation = "Review"

    return ReportResponse(
        session_id=session_id,
        status=session.status,
        interview_mode=session.interview_mode,
        answered_turns=int(answered_turns),
        total_questions=len(question_bank),
        average_score=round(float(average_score), 2),
        recommendation=recommendation,
        generated_at=datetime.now(timezone.utc),
    )
