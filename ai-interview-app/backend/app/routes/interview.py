"""
AI-Powered Interview Routes
────────────────────────────
All question generation, answer evaluation, and reporting is
handled by the AI engine. Falls back gracefully if LLM is unreachable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai import engine as ai_engine
from ..ai.resume_parser import extract_text, parse_resume_with_llm
from ..config import settings
from ..database import get_db
from ..models import InterviewSession, InterviewTurn
from ..schemas import (
    AnswerResponse,
    AnswerSubmit,
    EligibilityResponse,
    ReportResponse,
    ResumeUploadResponse,
    SessionCreate,
    SessionResponse,
)

router = APIRouter(prefix="/api/v1/interview", tags=["AI Interview"])

QUESTION_COUNTS = ai_engine.QUESTION_COUNTS


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


def _get_resume_summary(session: InterviewSession) -> str | None:
    """Return the parsed resume summary string for AI prompts."""
    if session.resume_parsed:
        try:
            parsed = json.loads(session.resume_parsed)
            return parsed.get("summary", "")
        except (json.JSONDecodeError, TypeError):
            pass
    if session.resume_text:
        return session.resume_text[:2000]
    return None


def _get_previous_turns(db: Session, session_id: str) -> list[dict]:
    """Load answered turns for context injection."""
    turns = db.scalars(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id)
        .order_by(InterviewTurn.turn_number.asc())
    ).all()
    result = []
    for t in turns:
        result.append({
            "turn": t.turn_number,
            "question": t.question,
            "answer": t.answer,
            "score": t.score,
        })
    return result


# ─── Eligibility ──────────────────────────────────────────────────
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


# ─── Resume Upload ───────────────────────────────────────────────
@router.post("/session/{session_id}/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(session_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # Validate file size
    contents = await file.read()
    max_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Resume must be under {settings.MAX_RESUME_SIZE_MB}MB.")

    filename = file.filename or "resume.pdf"

    # Extract text
    try:
        resume_text = extract_text(contents, filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if len(resume_text.strip()) < 50:
        raise HTTPException(status_code=422, detail="Could not extract enough text from the resume. Please upload a valid PDF, DOCX, or TXT file.")

    session.resume_text = resume_text

    # Parse with LLM
    parsed = await parse_resume_with_llm(resume_text)
    session.resume_parsed = json.dumps(parsed, default=str)
    db.commit()

    return ResumeUploadResponse(
        session_id=session_id,
        resume_parsed=True,
        skills=parsed.get("key_skills", []),
        summary=parsed.get("summary", ""),
    )


# ─── Create Session ──────────────────────────────────────────────
@router.post("/session", response_model=SessionResponse)
async def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
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
                detail="Your complimentary Practice Interview has already been used. Please select Pro Practice (₹50) to continue.",
            )

    if mode == "real":
        if not payload.company_name or not payload.company_name.strip():
            raise HTTPException(status_code=422, detail="Company name is required for Enterprise Assessments.")
        if not payload.company_interview_code or not payload.company_interview_code.strip():
            raise HTTPException(status_code=422, detail="Interview code is required for Enterprise Assessments.")

    # Pricing
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

    # Create session
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

    # Generate AI introduction
    introduction = await ai_engine.generate_introduction(
        candidate_name=payload.candidate_name,
        target_role=payload.target_role,
        interview_mode=mode,
        resume_summary=None,  # Resume uploaded separately
    )
    session.ai_introduction = introduction

    # Generate first question via AI
    total_q = QUESTION_COUNTS.get(mode, 5)
    first_question = await ai_engine.generate_question(
        candidate_name=payload.candidate_name,
        target_role=payload.target_role,
        interview_mode=mode,
        turn_number=1,
        resume_summary=None,
    )

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
        ai_introduction=introduction,
        first_question=first_question,
        resume_uploaded=False,
    )


# ─── Regenerate Introduction (after resume upload) ───────────────
@router.post("/session/{session_id}/regenerate-intro")
async def regenerate_introduction(session_id: str, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    resume_summary = _get_resume_summary(session)

    introduction = await ai_engine.generate_introduction(
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        interview_mode=session.interview_mode,
        resume_summary=resume_summary,
    )
    session.ai_introduction = introduction

    # Also regenerate the first question if unanswered
    first_turn = db.scalar(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id, InterviewTurn.turn_number == 1)
    )
    if first_turn and first_turn.answer is None:
        new_question = await ai_engine.generate_question(
            candidate_name=session.candidate_name,
            target_role=session.target_role,
            interview_mode=session.interview_mode,
            turn_number=1,
            resume_summary=resume_summary,
        )
        first_turn.question = new_question
        db.commit()
        return {"ai_introduction": introduction, "first_question": new_question, "resume_contextualized": True}

    db.commit()
    return {"ai_introduction": introduction, "first_question": None, "resume_contextualized": True}


# ─── Submit Answer ───────────────────────────────────────────────
@router.post("/session/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, payload: AnswerSubmit, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    total_q = QUESTION_COUNTS.get(session.interview_mode, 5)

    pending_turn = db.scalar(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id, InterviewTurn.answer.is_(None))
        .order_by(InterviewTurn.turn_number.asc())
        .limit(1)
    )
    if not pending_turn:
        raise HTTPException(status_code=409, detail="No pending question in this session.")

    resume_summary = _get_resume_summary(session)

    # ── AI-powered evaluation ────────────────────────────────
    evaluation = await ai_engine.evaluate_answer(
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        interview_mode=session.interview_mode,
        turn_number=pending_turn.turn_number,
        total_questions=total_q,
        question=pending_turn.question,
        answer=payload.answer,
        resume_summary=resume_summary,
    )

    pending_turn.answer = payload.answer
    pending_turn.score = evaluation.overall_score
    pending_turn.feedback = evaluation.feedback
    pending_turn.dimension_scores = json.dumps({
        "technical_accuracy": evaluation.technical_accuracy,
        "depth_detail": evaluation.depth_detail,
        "practical_experience": evaluation.practical_experience,
        "communication": evaluation.communication,
        "problem_solving": evaluation.problem_solving,
    })
    pending_turn.improvement_tips = json.dumps(evaluation.improvement_tips)
    pending_turn.strengths = json.dumps(evaluation.strengths)

    # ── Generate next question or complete ───────────────────
    next_question = None
    if pending_turn.turn_number < total_q:
        previous_turns = _get_previous_turns(db, session_id)
        next_turn_number = pending_turn.turn_number + 1

        next_question = await ai_engine.generate_question(
            candidate_name=session.candidate_name,
            target_role=session.target_role,
            interview_mode=session.interview_mode,
            turn_number=next_turn_number,
            resume_summary=resume_summary,
            previous_turns=previous_turns,
        )
        db.add(InterviewTurn(session_id=session_id, turn_number=next_turn_number, question=next_question))
    else:
        session.status = "completed"

    db.commit()

    # Determine what detail to expose based on mode
    show_detail = session.interview_mode in ("mock_paid", "real")

    return AnswerResponse(
        score=evaluation.overall_score,
        feedback=evaluation.feedback,
        next_question=next_question,
        status=session.status,
        turn_number=pending_turn.turn_number,
        total_questions=total_q,
        dimension_scores={
            "technical_accuracy": evaluation.technical_accuracy,
            "depth_detail": evaluation.depth_detail,
            "practical_experience": evaluation.practical_experience,
            "communication": evaluation.communication,
            "problem_solving": evaluation.problem_solving,
        } if show_detail else None,
        improvement_tips=evaluation.improvement_tips if show_detail else None,
        strengths=evaluation.strengths if show_detail else None,
    )


# ─── Get Report ──────────────────────────────────────────────────
@router.get("/session/{session_id}/report", response_model=ReportResponse)
async def get_report(session_id: str, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    total_q = QUESTION_COUNTS.get(session.interview_mode, 5)

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

    # Generate AI report for paid modes
    ai_report_data = None
    if session.interview_mode in ("mock_paid", "real"):
        turns_data = _get_previous_turns(db, session_id)
        ai_report_data = await ai_engine.generate_report(
            candidate_name=session.candidate_name,
            target_role=session.target_role,
            interview_mode=session.interview_mode,
            turns=turns_data,
        )
        session.ai_report = json.dumps(ai_report_data, default=str)
        db.commit()

    # Determine recommendation
    recommendation = "Reject"
    if ai_report_data and "recommendation" in ai_report_data:
        recommendation = ai_report_data["recommendation"]
    elif average_score >= 8.5:
        recommendation = "Shortlist"
    elif average_score >= 7.0:
        recommendation = "Review"

    return ReportResponse(
        session_id=session_id,
        status=session.status,
        interview_mode=session.interview_mode,
        answered_turns=int(answered_turns),
        total_questions=total_q,
        average_score=round(float(average_score), 2),
        recommendation=recommendation,
        generated_at=datetime.now(timezone.utc),
        ai_report=ai_report_data,
    )
