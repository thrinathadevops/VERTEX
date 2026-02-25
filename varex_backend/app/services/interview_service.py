"""
AI Interview Service
Manages the 30-minute AI-driven interview session.

The AI:
  1. Generates questions based on JD + candidate profile
  2. Listens to candidate answers
  3. Sends a polite acknowledgement reply
  4. Scores each answer
  5. Generates a final score report

Replace _call_llm_question / _call_llm_score / _call_llm_report
with real LLM calls (OpenAI, Gemini, etc.) in production.
"""
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.interview import (
    InterviewSession, InterviewTurn, ScoreReport, InterviewStatus, CandidateProfile, JobDescription
)


MAX_TURNS = 8   # ~30 min at ~4 min per turn


from app.core.config import settings
from app.services.llm_service import generate_interview_question, score_answer, generate_score_report

# ── LLM Integration (with fallbacks) ──────────────────────────────────────────

async def _call_llm_question(
    jd_text: str,
    resume_text: str,
    history: list[dict],
    turn_number: int,
) -> str:
    """Generate the next interview question based on JD + conversation history."""
    if not settings.GEMINI_API_KEY:
        openers = [
            "Tell me about yourself and what drew you to this role.",
            "Can you walk me through a challenging project you have led recently?",
            "How do you approach system design for a high-traffic API?",
            "Describe how you handle disagreements with team members.",
            "What's your experience with asynchronous programming in Python?",
            "How do you ensure code quality in a fast-moving team?",
            "Describe a time you had to optimise a slow database query.",
            "Where do you see yourself in three years?",
        ]
        return openers[min(turn_number - 1, len(openers) - 1)]

    # Note: `resume_text` isn't strictly required by our llm_service right now, 
    # but could be passed if we update generate_interview_question.
    skills = [] # Optionally parse from jd_text or pass securely.
    # To keep it simple, we pass jd_text as is.
    return await generate_interview_question(
        job_title="Role", 
        job_description=jd_text, 
        skills=skills, 
        turn_number=turn_number, 
        previous_qa=history
    )


async def _call_llm_score(
    question: str,
    answer: str,
    jd_text: str,
) -> tuple[float, str]:
    """Score the candidate's answer (0–10) and return a polite reply."""
    if not settings.GEMINI_API_KEY:
        word_count = len(answer.split())
        score = min(10.0, round(word_count / 20, 1))  # naive word-count proxy
        reply = (
            "Thank you for sharing that — very insightful. Let's move to the next question."
            if score >= 5
            else "Thank you for your response. I appreciate your honesty. Let's continue."
        )
        return score, reply

    res = await score_answer(question, answer, job_title="Role", skills=[])
    score = float(res.get("score", 5))
    reply = res.get("feedback", "Thank you for your response. Let's continue.")
    return score, reply


async def _call_llm_report(
    turns: list[InterviewTurn],
    candidate_name: str,
    jd_title: str,
) -> dict:
    """Generate the final score report narrative."""
    if not settings.GEMINI_API_KEY:
        avg_score = round(
            sum(t.answer_score or 0 for t in turns) / max(len(turns), 1) * 10, 1
        )  # scale to 100
        return {
            "overall_score": avg_score,
            "communication_score": round(avg_score / 10 * 10, 1),
            "technical_score": round(avg_score / 10 * 9, 1),
            "problem_solving_score": round(avg_score / 10 * 8.5, 1),
            "confidence_score": round(avg_score / 10 * 9.5, 1),
            "strengths": ["Clear communication", "Relevant experience"],
            "areas_to_improve": ["Depth on distributed systems", "Quantify achievements"],
            "recommendation": "Shortlist" if avg_score >= 70 else "Review" if avg_score >= 40 else "Reject",
            "ai_summary": (
                f"{candidate_name} completed the AI interview for {jd_title}. "
                f"Overall score: {avg_score}/100. "
                "Candidate demonstrated reasonable communication skills. "
                "Recommend proceeding to the human panel round."
            ),
        }

    history = [
        {"question": t.ai_question, "answer": t.candidate_answer, "score": t.answer_score}
        for t in turns
    ]
    res = await generate_score_report(jd_title, candidate_name, history)
    
    overall_score = float(res.get("overall_score", 5)) * 10
    
    return {
        "overall_score": overall_score,
        "communication_score": float(res.get("communication", 5)) * 10,
        "technical_score": float(res.get("technical_score", 5)) * 10,
        "problem_solving_score": float(res.get("overall_score", 5)) * 10,
        "confidence_score": float(res.get("overall_score", 5)) * 10,
        "strengths": res.get("details", {}).get("strengths", []),
        "areas_to_improve": res.get("details", {}).get("weaknesses", []),
        "recommendation": "Shortlist" if overall_score >= 70 else "Review" if overall_score >= 40 else "Reject",
        "ai_summary": res.get("summary", "Interview completed."),
    }


# ── Core session management ───────────────────────────────────────────────────

async def start_session(db: AsyncSession, session_id: UUID) -> InterviewSession:
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise ValueError("Session not found")
    if session.status != InterviewStatus.scheduled:
        raise ValueError(f"Session is already {session.status}")

    session.status = InterviewStatus.in_progress
    session.started_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)

    # Generate and persist first question
    await _next_turn(db, session)
    return session


async def _next_turn(db: AsyncSession, session: InterviewSession) -> InterviewTurn:
    """Create the next AI question turn."""
    result = await db.execute(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session.id)
        .order_by(InterviewTurn.turn_number)
    )
    existing_turns = result.scalars().all()
    turn_number = len(existing_turns) + 1

    jd = await db.get(JobDescription, session.job_description_id)
    candidate = await db.get(CandidateProfile, session.candidate_id)

    history = [
        {"question": t.ai_question, "answer": t.candidate_answer or ""}
        for t in existing_turns
    ]

    question = await _call_llm_question(
        jd_text=jd.description if jd else "",
        resume_text=candidate.resume_text or "" if candidate else "",
        history=history,
        turn_number=turn_number,
    )

    turn = InterviewTurn(
        session_id=session.id,
        turn_number=turn_number,
        ai_question=question,
    )
    db.add(turn)
    await db.commit()
    await db.refresh(turn)
    return turn


async def submit_answer(
    db: AsyncSession, session_id: UUID, turn_id: UUID, answer: str
) -> InterviewTurn:
    """Record candidate answer, score it, generate polite reply, queue next question or end."""
    turn = await db.get(InterviewTurn, turn_id)
    if not turn or str(turn.session_id) != str(session_id):
        raise ValueError("Turn not found in this session")

    session = await db.get(InterviewSession, session_id)
    if session.status != InterviewStatus.in_progress:
        raise ValueError("Session is not in progress")

    jd = await db.get(JobDescription, session.job_description_id)
    score, reply = await _call_llm_score(turn.ai_question, answer, jd.description if jd else "")

    turn.candidate_answer = answer
    turn.answer_score = score
    turn.ai_reply = reply
    await db.commit()
    await db.refresh(turn)

    # Start next turn or end session
    result = await db.execute(
        select(InterviewTurn).where(InterviewTurn.session_id == session_id)
    )
    total_turns = len(result.scalars().all())

    if total_turns < MAX_TURNS:
        await _next_turn(db, session)
    else:
        await _end_session(db, session)

    return turn


async def _end_session(db: AsyncSession, session: InterviewSession):
    session.status = InterviewStatus.completed
    session.ended_at = datetime.now(timezone.utc)
    await db.commit()

    result = await db.execute(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session.id)
        .order_by(InterviewTurn.turn_number)
    )
    turns = result.scalars().all()

    jd = await db.get(JobDescription, session.job_description_id)
    candidate = await db.get(CandidateProfile, session.candidate_id)

    report_data = await _call_llm_report(
        turns=turns,
        candidate_name=candidate.name if candidate else "Candidate",
        jd_title=jd.title if jd else "Role",
    )

    report = ScoreReport(session_id=session.id, **report_data)
    db.add(report)
    await db.commit()


async def get_current_turn(db: AsyncSession, session_id: UUID) -> InterviewTurn | None:
    result = await db.execute(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id)
        .where(InterviewTurn.candidate_answer.is_(None))
        .order_by(InterviewTurn.turn_number)
        .limit(1)
    )
    return result.scalar_one_or_none()
