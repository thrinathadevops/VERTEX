from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import InterviewSession, InterviewTurn
from ..schemas import AnswerResponse, AnswerSubmit, ReportResponse, SessionCreate, SessionResponse


router = APIRouter(prefix="/api/v1/interview", tags=["AI Interview"])

QUESTION_BANK = [
    "Explain a production incident you handled and how you restored service.",
    "How do you design CI/CD for both speed and safe rollback?",
    "How would you secure Kubernetes workloads in a multi-tenant cluster?",
    "Describe your approach for cloud cost optimization without reducing reliability.",
    "How do you define SLOs and use observability to improve system resilience?",
]


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


@router.post("/session", response_model=SessionResponse)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    session = InterviewSession(
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        target_role=payload.target_role,
        status="active",
    )
    db.add(session)
    db.flush()

    first_question = QUESTION_BANK[0]
    first_turn = InterviewTurn(
        session_id=session.id,
        turn_number=1,
        question=first_question,
    )
    db.add(first_turn)
    db.commit()

    return SessionResponse(id=session.id, status="active", first_question=first_question)


@router.post("/session/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(session_id: str, payload: AnswerSubmit, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

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
    if pending_turn.turn_number < len(QUESTION_BANK):
        next_turn_number = pending_turn.turn_number + 1
        next_question = QUESTION_BANK[next_turn_number - 1]
        db.add(
            InterviewTurn(
                session_id=session_id,
                turn_number=next_turn_number,
                question=next_question,
            )
        )
    else:
        session.status = "completed"

    db.commit()

    return AnswerResponse(
        score=score,
        feedback=feedback,
        next_question=next_question,
        status=session.status,
    )


@router.get("/session/{session_id}/report", response_model=ReportResponse)
def get_report(session_id: str, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

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
        answered_turns=int(answered_turns),
        average_score=round(float(average_score), 2),
        recommendation=recommendation,
        generated_at=datetime.now(timezone.utc),
    )
