"""
AI-Powered Interview Routes — v2
─────────────────────────────────
Full interview lifecycle with:
  - 7-phase AI interview flow
  - Difficulty level selection
  - Async background evaluation
  - Anti-cheat event recording
  - Per-question + total timers
  - Status FSM: scheduled → in_progress → evaluating → completed
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai import engine as ai_engine
from ..ai.resume_parser import extract_text, parse_resume_with_llm
from ..auth.jwt_handler import create_interview_token, decode_access_token
from ..auth.deps import get_optional_user
from ..config import settings
from ..database import get_db
from ..models import InterviewSession, InterviewTurn, User
from ..schemas import (
    AntiCheatEventCreate,
    AnswerResponse,
    AnswerSubmit,
    EligibilityResponse,
    PricingRequest,
    PricingResponse,
    ReportResponse,
    ResumeUploadResponse,
    ScoreBreakdown,
    SessionCreate,
    SessionResponse,
)
from ..services.email_verification import (
    is_email_verified,
    issue_verification_token,
    normalize_email,
    send_verification_email,
)
from ..services.anti_cheat import (
    BROWSER_EVENT_TYPES,
    check_proctor_health,
    get_session_anti_cheat_summary,
    record_event,
    record_proctor_heartbeat,
)
from ..services.evaluation import evaluate_answer_background
from ..services.interview_timer import (
    check_question_timeout,
    check_total_interview_timeout,
    get_question_time_limit,
    get_total_time_limit,
)
from ..services.pricing import calculate_pricing

router = APIRouter(prefix="/api/v1/interview", tags=["AI Interview"])

QUESTION_COUNTS = ai_engine.QUESTION_COUNTS


def _require_proctor_secret(
    x_proctor_secret: str | None = Header(default=None, alias="X-Proctor-Secret"),
):
    """Require shared secret for proctor-agent endpoints when enabled."""
    if not settings.PROCTOR_SHARED_SECRET:
        return
    if x_proctor_secret != settings.PROCTOR_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid proctor credentials.")


def _require_interview_token(
    session_id: str,
    x_interview_token: str | None = Header(default=None, alias="X-Interview-Token"),
) -> dict:
    if not x_interview_token:
        raise HTTPException(status_code=401, detail="Interview session token is required.")

    payload = decode_access_token(x_interview_token)
    if not payload or payload.get("type") != "interview" or payload.get("sub") != session_id:
        raise HTTPException(status_code=401, detail="Invalid or expired interview session token.")
    return payload


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
    return [
        {
            "turn": t.turn_number,
            "question": t.question,
            "answer": t.answer,
            "score": t.score,
        }
        for t in turns
    ]


# ═══════════════════════════════════════════════════════════════════
#  PRICING CALCULATOR
# ═══════════════════════════════════════════════════════════════════

@router.post("/pricing", response_model=PricingResponse)
def calculate_price(
    payload: PricingRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Calculate interview pricing with discounts."""
    free_mock_used = False
    if user:
        free_mock_used = user.free_mock_used
    elif payload.interview_mode == "mock_free":
        # For unauthenticated users, check by email later in create_session
        free_mock_used = False

    result = calculate_pricing(
        interview_mode=payload.interview_mode,
        package_interviews=payload.package_interviews,
        free_mock_used=free_mock_used,
    )

    return PricingResponse(
        interview_mode=result.interview_mode,
        package_interviews=result.package_interviews,
        base_price_per_interview=result.base_price_per_interview,
        discount_percent=result.discount_percent,
        base_total_rupees=result.base_total_rupees,
        discount_amount_rupees=result.discount_amount_rupees,
        final_charge_rupees=result.final_charge_rupees,
    )


# ═══════════════════════════════════════════════════════════════════
#  ELIGIBILITY CHECK
# ═══════════════════════════════════════════════════════════════════

@router.get("/eligibility", response_model=EligibilityResponse)
def check_eligibility(email: str, db: Session = Depends(get_db)):
    """Return a generic eligibility response without exposing candidate history."""
    return EligibilityResponse(
        eligible=True,
        free_mock_used=False,
        mock_count=0,
        enterprise_count=0,
        next_mock_charge_rupees=0,
    )


# ═══════════════════════════════════════════════════════════════════
#  RESUME UPLOAD
# ═══════════════════════════════════════════════════════════════════

@router.post("/session/{session_id}/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(
    session_id: str,
    file: UploadFile = File(...),
    _session_claims: dict = Depends(_require_interview_token),
    db: Session = Depends(get_db),
):
    """Upload and parse resume for an interview session."""
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    contents = await file.read()
    max_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Resume must be under {settings.MAX_RESUME_SIZE_MB}MB.",
        )

    filename = file.filename or "resume.pdf"

    try:
        resume_text = extract_text(contents, filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if len(resume_text.strip()) < 50:
        raise HTTPException(
            status_code=422,
            detail="Could not extract enough text. Upload a valid PDF, DOCX, or TXT.",
        )

    session.resume_text = resume_text

    # Parse with LLM
    parsed = await parse_resume_with_llm(resume_text)
    session.resume_parsed = json.dumps(parsed, default=str)

    # Generate structured skill profile
    skill_profile = {
        "experience": parsed.get("years_experience", 0),
        "primary_skills": parsed.get("primary_skills", parsed.get("key_skills", []))[:5],
        "secondary_skills": parsed.get("secondary_skills", [])[:5],
    }
    session.skill_profile = json.dumps(skill_profile)
    db.commit()

    return ResumeUploadResponse(
        session_id=session_id,
        resume_parsed=True,
        skill_profile=skill_profile,
        skills=skill_profile["primary_skills"] + skill_profile["secondary_skills"],
        summary=parsed.get("summary", ""),
    )


# ═══════════════════════════════════════════════════════════════════
#  CREATE SESSION
# ═══════════════════════════════════════════════════════════════════

@router.post("/session", response_model=SessionResponse)
async def create_session(
    payload: SessionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Create a new interview session with pricing, difficulty, and AI intro."""
    mode = payload.interview_mode
    difficulty = payload.difficulty_level
    normalized_email = normalize_email(payload.candidate_email)
    prior_mock_sessions = db.scalar(
        select(func.count(InterviewSession.id)).where(
            InterviewSession.candidate_email == normalized_email,
            InterviewSession.interview_mode.in_(["mock_free", "mock_paid"]),
        )
    ) or 0

    # ── Enforce free mock limit ───────────────────────────────
    if mode == "mock_free":
        # Check via user model first
        if user and user.free_mock_used:
            raise HTTPException(
                status_code=403,
                detail="Your free Practice Interview has been used. Select Pro Practice (₹50) to continue.",
            )
        # Fallback: check by email
        existing_free = db.scalar(
            select(func.count(InterviewSession.id)).where(
                InterviewSession.candidate_email == normalized_email,
                InterviewSession.interview_mode == "mock_free",
            )
        ) or 0
        if existing_free > 0:
            raise HTTPException(
                status_code=403,
                detail="Your free Practice Interview has been used. Select Pro Practice (₹50) to continue.",
            )

    if mode != "enterprise" and prior_mock_sessions > 0 and not is_email_verified(db, normalized_email):
        token = issue_verification_token(db, normalized_email)
        background_tasks.add_task(send_verification_email, normalized_email, token)
        raise HTTPException(
            status_code=403,
            detail="Please verify your email to continue. A verification link has been sent if the email can be verified.",
        )

    # ── Enterprise validation ─────────────────────────────────
    if mode == "enterprise":
        if not payload.company_name or not payload.company_name.strip():
            raise HTTPException(status_code=422, detail="Company name is required for Enterprise Assessments.")
        if not payload.company_interview_code or not payload.company_interview_code.strip():
            raise HTTPException(status_code=422, detail="Interview code is required for Enterprise Assessments.")

    # ── Calculate pricing ─────────────────────────────────────
    free_mock_used = False
    if user:
        free_mock_used = user.free_mock_used

    pricing = calculate_pricing(
        interview_mode=mode,
        package_interviews=payload.package_interviews,
        free_mock_used=free_mock_used,
    )

    # ── Timer settings ────────────────────────────────────────
    total_time = get_total_time_limit(difficulty)
    question_time = get_question_time_limit(difficulty)
    total_q = QUESTION_COUNTS.get(mode, 5)

    # ── Create session ────────────────────────────────────────
    session = InterviewSession(
        user_id=user.id if user else None,
        candidate_name=payload.candidate_name,
        candidate_email=normalized_email,
        target_role=payload.target_role,
        company_name=payload.company_name.strip() if payload.company_name else None,
        company_interview_code=payload.company_interview_code.strip() if payload.company_interview_code else None,
        interview_mode=mode,
        difficulty_level=difficulty,
        package_interviews=pricing.package_interviews,
        discount_percent=pricing.discount_percent,
        charge_rupees=pricing.final_charge_rupees,
        is_paid=mode in ("mock_paid", "enterprise"),
        status="scheduled",
        total_time_limit_seconds=total_time,
    )
    db.add(session)
    db.flush()

    # ── Mark free mock as used ────────────────────────────────
    if mode == "mock_free" and user:
        user.free_mock_used = True

    # ── Generate AI introduction (Phase 1) ────────────────────
    introduction = await ai_engine.generate_introduction(
        candidate_name=payload.candidate_name,
        target_role=payload.target_role,
        interview_mode=mode,
        difficulty_level=difficulty,
        resume_summary=None,  # Resume uploaded separately
    )
    session.ai_introduction = introduction

    # ── Generate first question via AI (Phase 2: ice_breaker) ─
    first_question, first_phase = await ai_engine.generate_question(
        candidate_name=payload.candidate_name,
        target_role=payload.target_role,
        interview_mode=mode,
        turn_number=1,
        difficulty_level=difficulty,
        resume_summary=None,
    )

    db.add(InterviewTurn(
        session_id=session.id,
        turn_number=1,
        question=first_question,
        question_phase=first_phase,
        time_limit_seconds=question_time,
    ))

    # Mark session as in_progress
    session.status = "in_progress"
    session.started_at = datetime.now(timezone.utc)
    db.commit()
    session_token = create_interview_token(session.id, session.candidate_email)

    return SessionResponse(
        id=session.id,
        session_token=session_token,
        status=session.status,
        interview_mode=mode,
        difficulty_level=difficulty,
        package_interviews=pricing.package_interviews,
        discount_percent=pricing.discount_percent,
        base_total_rupees=pricing.base_total_rupees,
        charge_rupees=pricing.final_charge_rupees,
        payment_required=mode in ("mock_paid", "enterprise"),
        ai_introduction=introduction,
        first_question=first_question,
        first_question_phase=first_phase,
        resume_uploaded=False,
        total_questions=total_q,
        total_time_limit_seconds=total_time,
        question_time_limit_seconds=question_time,
    )


# ═══════════════════════════════════════════════════════════════════
#  REGENERATE INTRODUCTION (after resume upload)
# ═══════════════════════════════════════════════════════════════════

@router.post("/session/{session_id}/regenerate-intro")
async def regenerate_introduction(
    session_id: str,
    _session_claims: dict = Depends(_require_interview_token),
    db: Session = Depends(get_db),
):
    """Regenerate AI introduction and first question using resume context."""
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    resume_summary = _get_resume_summary(session)

    introduction = await ai_engine.generate_introduction(
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        interview_mode=session.interview_mode,
        difficulty_level=session.difficulty_level,
        resume_summary=resume_summary,
    )
    session.ai_introduction = introduction

    # Regenerate first question if unanswered
    first_turn = db.scalar(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id, InterviewTurn.turn_number == 1)
    )
    if first_turn and first_turn.answer is None:
        new_question, new_phase = await ai_engine.generate_question(
            candidate_name=session.candidate_name,
            target_role=session.target_role,
            interview_mode=session.interview_mode,
            turn_number=1,
            difficulty_level=session.difficulty_level,
            resume_summary=resume_summary,
        )
        first_turn.question = new_question
        first_turn.question_phase = new_phase
        db.commit()
        return {
            "ai_introduction": introduction,
            "first_question": new_question,
            "first_question_phase": new_phase,
            "resume_contextualized": True,
        }

    db.commit()
    return {"ai_introduction": introduction, "first_question": None, "resume_contextualized": True}


# ═══════════════════════════════════════════════════════════════════
#  SUBMIT ANSWER (with async background evaluation)
# ═══════════════════════════════════════════════════════════════════

@router.post("/session/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    session_id: str,
    payload: AnswerSubmit,
    background_tasks: BackgroundTasks,
    _session_claims: dict = Depends(_require_interview_token),
    db: Session = Depends(get_db),
):
    """
    Submit an answer. The answer is saved immediately.
    Evaluation runs in the background — scores are NOT shown during the interview.
    The next question is generated immediately so the candidate isn't waiting.
    """
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    if session.status not in ("in_progress", "scheduled"):
        raise HTTPException(status_code=409, detail=f"Interview is {session.status}. Cannot submit answers.")

    total_q = QUESTION_COUNTS.get(session.interview_mode, 5)

    # ── Enterprise: enforce continuous proctor heartbeat ─────
    if session.interview_mode == "enterprise" and settings.PROCTOR_REQUIRE_FOR_ENTERPRISE:
        health = check_proctor_health(db, session_id)
        grace_elapsed = 0.0
        if session.started_at:
            grace_elapsed = (datetime.now(timezone.utc) - session.started_at).total_seconds()
        grace_over = grace_elapsed >= settings.PROCTOR_START_GRACE_SECONDS

        if health.get("heartbeat_count", 0) == 0 and grace_over:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Proctor agent heartbeat not detected. Enterprise interviews require "
                    "the proctor agent to be running."
                ),
            )
        if health.get("heartbeat_count", 0) > 0 and not health.get("proctor_alive", False):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Proctor agent disconnected. Resume proctor monitoring before "
                    "submitting the next answer."
                ),
            )

    # ── Check total interview timeout ─────────────────────────
    timer_check = check_total_interview_timeout(
        session.started_at, session.total_time_limit_seconds
    )
    if timer_check["expired"]:
        session.status = "evaluating"
        db.commit()
        raise HTTPException(
            status_code=409,
            detail="Interview time has expired. Your answers are being evaluated.",
        )

    # ── Find pending turn ─────────────────────────────────────
    pending_turn = db.scalar(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id, InterviewTurn.answer.is_(None))
        .order_by(InterviewTurn.turn_number.asc())
        .limit(1)
    )
    if not pending_turn:
        raise HTTPException(status_code=409, detail="No pending question in this session.")

    # ── Save answer immediately ───────────────────────────────
    pending_turn.answer = payload.answer
    pending_turn.time_taken_seconds = payload.time_taken_seconds
    pending_turn.evaluation_status = "evaluating"  # Will be evaluated in background

    resume_summary = _get_resume_summary(session)

    # ── Queue background evaluation ───────────────────────────
    background_tasks.add_task(
        _run_background_evaluation,
        db_url=str(settings.DATABASE_URL),
        turn_id=pending_turn.id,
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        interview_mode=session.interview_mode,
        difficulty_level=session.difficulty_level,
        turn_number=pending_turn.turn_number,
        total_questions=total_q,
        question=pending_turn.question,
        answer=payload.answer,
        resume_summary=resume_summary,
    )

    # ── Generate next question or complete ────────────────────
    next_question = None
    next_phase = None
    next_time_limit = None

    if pending_turn.turn_number < total_q:
        previous_turns = _get_previous_turns(db, session_id)
        next_turn_number = pending_turn.turn_number + 1
        question_time = get_question_time_limit(session.difficulty_level)

        next_question, next_phase = await ai_engine.generate_question(
            candidate_name=session.candidate_name,
            target_role=session.target_role,
            interview_mode=session.interview_mode,
            turn_number=next_turn_number,
            difficulty_level=session.difficulty_level,
            resume_summary=resume_summary,
            previous_turns=previous_turns,
        )
        next_time_limit = question_time

        db.add(InterviewTurn(
            session_id=session_id,
            turn_number=next_turn_number,
            question=next_question,
            question_phase=next_phase,
            time_limit_seconds=question_time,
        ))
    else:
        # All questions answered → move to evaluating
        session.status = "evaluating"

    db.commit()

    return AnswerResponse(
        turn_number=pending_turn.turn_number,
        total_questions=total_q,
        status=session.status,
        evaluation_status="evaluating",
        next_question=next_question,
        next_question_phase=next_phase,
        next_question_time_limit=next_time_limit,
        # Scores NOT shown during interview
        score=None,
        feedback=None,
        dimension_scores=None,
        improvement_tips=None,
        strengths=None,
    )


async def _run_background_evaluation(**kwargs):
    """Wrapper to run async background evaluation."""
    await evaluate_answer_background(**kwargs)


# ═══════════════════════════════════════════════════════════════════
#  ANTI-CHEAT EVENT
# ═══════════════════════════════════════════════════════════════════

@router.post("/session/{session_id}/anti-cheat")
def record_anti_cheat_event(
    session_id: str,
    payload: AntiCheatEventCreate,
    _session_claims: dict = Depends(_require_interview_token),
    db: Session = Depends(get_db),
):
    """Record an anti-cheat event (tab switch, window blur, etc.)."""
    if payload.event_type not in BROWSER_EVENT_TYPES:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only browser-level anti-cheat events are accepted on this endpoint. "
                "OS-level events must come from proctor-heartbeat."
            ),
        )
    result = record_event(
        db=db,
        session_id=session_id,
        event_type=payload.event_type,
        details=payload.details,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/session/{session_id}/anti-cheat")
def get_anti_cheat_summary(
    session_id: str,
    _session_claims: dict = Depends(_require_interview_token),
    db: Session = Depends(get_db),
):
    """Get comprehensive anti-cheat summary for a session."""
    result = get_session_anti_cheat_summary(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ═════════════════════════════════════════════════════════════════
#  PROCTOR AGENT ENDPOINTS (OS-Level Anti-Cheat)
# ═════════════════════════════════════════════════════════════════

@router.post("/session/{session_id}/proctor-heartbeat")
def proctor_heartbeat(
    session_id: str,
    payload: dict,
    _auth: None = Depends(_require_proctor_secret),
    db: Session = Depends(get_db),
):
    """
    Receive heartbeat from the desktop proctoring agent.
    The agent sends scan results (running processes, network connections,
    active windows) every 10 seconds.
    """
    result = record_proctor_heartbeat(
        db=db,
        session_id=session_id,
        heartbeat_data=payload,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/session/{session_id}/proctor-health")
def proctor_health(
    session_id: str,
    _session_claims: dict = Depends(_require_interview_token),
    db: Session = Depends(get_db),
):
    """
    Check if the proctoring agent is still connected.
    Called by frontend to show proctor status badge.
    If proctor stops sending heartbeats, it's flagged.
    """
    result = check_proctor_health(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ═══════════════════════════════════════════════════════════════════
#  INTERVIEW STATUS
# ═══════════════════════════════════════════════════════════════════

@router.get("/session/{session_id}/status")
def get_session_status(
    session_id: str,
    _session_claims: dict = Depends(_require_interview_token),
    db: Session = Depends(get_db),
):
    """Get current session status and evaluation progress."""
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    total_q = QUESTION_COUNTS.get(session.interview_mode, 5)

    turns = db.scalars(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id)
        .order_by(InterviewTurn.turn_number.asc())
    ).all()

    answered = sum(1 for t in turns if t.answer is not None)
    evaluated = sum(1 for t in turns if t.evaluation_status == "evaluated")

    # Timer info
    timer = check_total_interview_timeout(
        session.started_at, session.total_time_limit_seconds
    )

    return {
        "session_id": session_id,
        "status": session.status,
        "total_questions": total_q,
        "answered": answered,
        "evaluated": evaluated,
        "all_evaluated": evaluated == answered and answered > 0,
        "timer": timer,
        # Anti-cheat status
        "suspicious_activity": session.suspicious_activity,
        "tab_switch_count": session.tab_switch_count,
        "ai_violations_count": session.ai_violations_count,
        "integrity_score": session.integrity_score,
        # Proctor agent status
        "proctor_connected": session.proctor_connected,
        "proctor_heartbeat_count": session.proctor_heartbeat_count,
    }


# ═══════════════════════════════════════════════════════════════════
#  GET REPORT
# ═══════════════════════════════════════════════════════════════════

@router.get("/session/{session_id}/report", response_model=ReportResponse)
async def get_report(
    session_id: str,
    _session_claims: dict = Depends(_require_interview_token),
    db: Session = Depends(get_db),
):
    """Get the final interview report. Only available after completion."""
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    if session.status not in ("completed", "evaluating"):
        raise HTTPException(
            status_code=409,
            detail=f"Interview is {session.status}. Report available after completion.",
        )

    total_q = QUESTION_COUNTS.get(session.interview_mode, 5)

    answered_turns = db.scalar(
        select(func.count(InterviewTurn.id)).where(
            InterviewTurn.session_id == session_id,
            InterviewTurn.answer.is_not(None),
        )
    ) or 0

    average_score = db.scalar(
        select(func.coalesce(func.avg(InterviewTurn.score), 0.0)).where(
            InterviewTurn.session_id == session_id,
            InterviewTurn.score.is_not(None),
        )
    ) or 0.0

    # ── Score breakdown ───────────────────────────────────────
    breakdown = None
    if session.score_weighted_total is not None:
        breakdown = ScoreBreakdown(
            technical_depth=session.score_technical_depth or 0.0,
            scenario_handling=session.score_scenario_handling or 0.0,
            communication=session.score_communication or 0.0,
            confidence=session.score_confidence or 0.0,
            weighted_total=session.score_weighted_total or 0.0,
        )

    # ── AI report ─────────────────────────────────────────────
    ai_report_data = None
    if session.ai_report:
        try:
            ai_report_data = json.loads(session.ai_report)
        except (json.JSONDecodeError, TypeError):
            pass

    # If report not yet generated (still evaluating), trigger generation
    if ai_report_data is None and session.status == "evaluating":
        # Check if all turns are evaluated
        all_evaluated = db.scalar(
            select(func.count(InterviewTurn.id)).where(
                InterviewTurn.session_id == session_id,
                InterviewTurn.evaluation_status != "evaluated",
                InterviewTurn.answer.is_not(None),
            )
        ) or 0

        if all_evaluated == 0 and answered_turns > 0:
            # All evaluated, generate report now
            turns_data = _get_previous_turns(db, session_id)
            if session.interview_mode in ("mock_paid", "enterprise"):
                ai_report_data = await ai_engine.generate_report(
                    candidate_name=session.candidate_name,
                    target_role=session.target_role,
                    interview_mode=session.interview_mode,
                    turns=turns_data,
                )
                session.ai_report = json.dumps(ai_report_data, default=str)

            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            db.commit()

    # Recommendation
    recommendation = "Reject"
    if ai_report_data and "recommendation" in ai_report_data:
        recommendation = ai_report_data["recommendation"]
    elif average_score >= 8.5:
        recommendation = "Shortlist"
    elif average_score >= 7.0:
        recommendation = "Review"

    # Anti-cheat summary (enhanced with proctor + AI detection)
    anti_cheat = None
    if session.suspicious_activity or session.tab_switch_count > 0 or session.ai_violations_count > 0:
        anti_cheat = {
            "tab_switches": session.tab_switch_count,
            "ai_violations": session.ai_violations_count,
            "integrity_score": session.integrity_score,
            "suspicious": session.suspicious_activity,
            "proctor_was_connected": session.proctor_connected or session.proctor_heartbeat_count > 0,
            "proctor_heartbeats": session.proctor_heartbeat_count,
        }

    return ReportResponse(
        session_id=session_id,
        status=session.status,
        interview_mode=session.interview_mode,
        difficulty_level=session.difficulty_level,
        answered_turns=int(answered_turns),
        total_questions=total_q,
        average_score=round(float(average_score), 2),
        score_breakdown=breakdown,
        recommendation=recommendation,
        generated_at=datetime.now(timezone.utc),
        ai_report=ai_report_data,
        anti_cheat_summary=anti_cheat,
    )
