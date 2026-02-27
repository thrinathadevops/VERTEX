"""
AI Interview Engine (Orchestrator) — v2
────────────────────────────────────────
Coordinates the full 7-phase AI-powered interview flow:

  Phase 1 → AI Introduction
  Phase 2 → Ice-breaker (warm-up from resume)
  Phase 3 → Resume summary validation
  Phase 4 → Technical deep dive
  Phase 5 → Scenario-based questions
  Phase 6 → Behavioral evaluation
  Phase 7 → Closing remarks

The engine adapts question difficulty based on:
  - Difficulty level (junior / mid / senior / architect)
  - Resume content
  - Previous answer quality

Question counts per mode:
  - mock_free:   5 questions
  - mock_paid:   8 questions
  - enterprise: 12 questions
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from ..config import settings
from .prompts import (
    EVALUATION_PROMPT,
    INTERVIEWER_PERSONA,
    INTRODUCTION_PROMPT,
    QUESTION_GEN_PROMPT,
    REPORT_PROMPT,
)
from .provider import get_llm_provider
from .training_data import format_training_context_for_prompt, format_scoring_context_for_prompt

logger = logging.getLogger(__name__)

# ─── Question counts per mode ────────────────────────────────────
QUESTION_COUNTS = {
    "mock_free": settings.QUESTIONS_MOCK_FREE,
    "mock_paid": settings.QUESTIONS_MOCK_PAID,
    "enterprise": settings.QUESTIONS_ENTERPRISE,
}


# ─── 7-Phase Interview Flow ─────────────────────────────────────
def get_question_phase(turn_number: int, total_questions: int) -> str:
    """
    Determine which interview phase a question belongs to.

    Phase mapping (proportional to total questions):
      Turn 1        → ice_breaker
      Turn 2        → resume_validation
      Turns 3–60%   → technical_deep_dive
      Turns 60%–80% → scenario_based
      Turns 80%–N-1 → behavioral
      Last turn     → closing
    """
    if turn_number == 1:
        return "ice_breaker"
    if turn_number == 2:
        return "resume_validation"
    if turn_number == total_questions:
        return "closing"

    # Proportional splits for the middle turns
    ratio = turn_number / total_questions
    if ratio <= 0.60:
        return "technical_deep_dive"
    if ratio <= 0.80:
        return "scenario_based"
    return "behavioral"


# Phase-specific instructions for question generation
PHASE_INSTRUCTIONS = {
    "ice_breaker": (
        "This is the ICE-BREAKER question. Ask something conversational and warm "
        "that puts the candidate at ease. Reference something specific from their "
        "resume — a company they worked at, a project they led, or a technology they list. "
        "Example: 'I see you worked at Acme Corp on their Kubernetes migration. "
        "Tell me about a moment during that project where things went sideways — what happened?'"
    ),
    "resume_validation": (
        "This is the RESUME VALIDATION question. Verify a specific claim from the resume. "
        "Pick a skill or achievement they list and ask them to walk through the details. "
        "Example: 'Your resume mentions you reduced build times by 60%. "
        "Walk me through exactly how you measured that and what changes you made.'"
    ),
    "technical_deep_dive": (
        "This is a TECHNICAL DEEP DIVE question. Go 3 levels deep into a technology "
        "or architecture from their experience. Frame it as a real scenario. "
        "Example: 'Your pod keeps getting OOMKilled every 48 hours. The team's fix is "
        "a cron that restarts it daily. What do you do?'"
    ),
    "scenario_based": (
        "This is a SCENARIO-BASED question. Present a realistic production situation "
        "with constraints (time pressure, limited resources, business impact). "
        "Example: 'It's 2 AM, PagerDuty fires. Your API gateway returns 503s for 40% "
        "of requests. Walk me through your first 15 minutes.'"
    ),
    "behavioral": (
        "This is a BEHAVIORAL question. Evaluate leadership, teamwork, conflict resolution, "
        "and decision-making under pressure. "
        "Example: 'Tell me about a time you disagreed with your manager about a technical "
        "decision. How did you handle it? What was the outcome?'"
    ),
    "closing": (
        "This is the CLOSING question. Ask something forward-looking and reflective. "
        "Example: 'If you could redesign the infrastructure at your last company from "
        "scratch with unlimited budget, what would you change and why?'"
    ),
}


# ─── Difficulty multipliers ──────────────────────────────────────
DIFFICULTY_INSTRUCTIONS = {
    "junior": (
        "The candidate is JUNIOR level. Ask foundational questions. "
        "Expect basic understanding, not advanced architecture. "
        "Still use scenarios, but simpler ones."
    ),
    "mid": (
        "The candidate is MID level. Ask questions that test practical experience. "
        "Expect them to have handled real production systems."
    ),
    "senior": (
        "The candidate is SENIOR level. Ask complex architectural questions. "
        "Expect system design thinking, trade-off analysis, and leadership signals. "
        "Push back hard on vague answers."
    ),
    "architect": (
        "The candidate is ARCHITECT level. Ask the hardest questions. "
        "Expect multi-region design, cost optimization, org-wide strategic thinking, "
        "and ability to articulate complex trade-offs. Challenge every assumption."
    ),
}


# ─── Fallback questions by phase ─────────────────────────────────
FALLBACK_QUESTIONS = {
    "ice_breaker": "Tell me about a project you're really proud of from your recent work. What was your specific contribution?",
    "resume_validation": "Walk me through your day-to-day responsibilities in your current or most recent role. What tools and processes do you use daily?",
    "technical_deep_dive": "How would you design a CI/CD pipeline for a microservices architecture with 15 services? Walk me through end to end.",
    "scenario_based": "It's 2 AM. PagerDuty fires — your main API gateway is returning 503s for 40% of requests. Walk me through your first 15 minutes.",
    "behavioral": "Tell me about a time you had to make a tough technical decision under pressure. What factors did you weigh?",
    "closing": "If you could redesign the infrastructure at your last company from scratch, what would you change first and why?",
}


@dataclass
class EvaluationResult:
    overall_score: float
    technical_accuracy: dict
    depth_detail: dict
    practical_experience: dict
    communication: dict
    problem_solving: dict
    feedback: str
    improvement_tips: list[str]
    strengths: list[str]
    follow_up_question: str | None


# ═══════════════════════════════════════════════════════════════════
#  Generate Introduction (Phase 1)
# ═══════════════════════════════════════════════════════════════════

async def generate_introduction(
    candidate_name: str,
    target_role: str,
    interview_mode: str,
    difficulty_level: str = "mid",
    resume_summary: str | None = None,
) -> str:
    """Generate the AI interviewer's opening introduction (Phase 1)."""
    total_q = QUESTION_COUNTS.get(interview_mode, 5)

    resume_section = ""
    if resume_summary and len(resume_summary.strip()) > 20:
        resume_section = f"RESUME SUMMARY:\n{resume_summary}"
    else:
        resume_section = "RESUME: Not provided"

    prompt = INTRODUCTION_PROMPT.format(
        target_role=target_role,
        interview_mode="practice" if interview_mode != "enterprise" else "enterprise assessment",
        candidate_name=candidate_name,
        total_questions=total_q,
        resume_section=resume_section,
        difficulty_level=difficulty_level,
    )

    try:
        provider = get_llm_provider()
        intro = await provider.complete(INTERVIEWER_PERSONA, prompt, temperature=0.6)
        return intro.strip()
    except Exception as e:
        logger.warning(f"LLM introduction generation failed: {e}")
        mode_label = "Enterprise Assessment" if interview_mode == "enterprise" else "Practice Session"
        return (
            f"Hello {candidate_name}! I'm Aria, your AI technical interviewer at VAREX. "
            f"I'll be conducting your {mode_label} for the {target_role} position today. "
            f"We'll go through {total_q} questions covering real-world scenarios, "
            f"technical depth, and problem-solving. Take your time — depth and specifics matter. "
            f"I'm looking for what YOU actually did, not just what the team did. Let's begin!"
        )


# ═══════════════════════════════════════════════════════════════════
#  Generate Question (Phases 2–7)
# ═══════════════════════════════════════════════════════════════════

async def generate_question(
    candidate_name: str,
    target_role: str,
    interview_mode: str,
    turn_number: int,
    difficulty_level: str = "mid",
    resume_summary: str | None = None,
    previous_turns: list[dict] | None = None,
) -> tuple[str, str]:
    """
    Generate the next contextual interview question.

    Returns:
        Tuple of (question_text, question_phase)
    """
    total_q = QUESTION_COUNTS.get(interview_mode, 5)
    phase = get_question_phase(turn_number, total_q)
    phase_instruction = PHASE_INSTRUCTIONS.get(phase, PHASE_INSTRUCTIONS["technical_deep_dive"])
    difficulty_instruction = DIFFICULTY_INSTRUCTIONS.get(difficulty_level, DIFFICULTY_INSTRUCTIONS["mid"])

    # Build previous Q&A context
    previous_qa = "None yet (this is the first question)."
    if previous_turns:
        parts = []
        for t in previous_turns[-3:]:  # Keep context window reasonable
            parts.append(f"Q{t['turn']}: {t['question']}")
            if t.get("answer"):
                answer_preview = t["answer"][:200] + "..." if len(t["answer"]) > 200 else t["answer"]
                parts.append(f"A{t['turn']}: {answer_preview}")
                if t.get("score"):
                    parts.append(f"Score: {t['score']}/10")
            parts.append("")
        previous_qa = "\n".join(parts)

    # Inject real-world interview training context
    training_context = format_training_context_for_prompt(
        role=target_role,
        turn_number=turn_number,
        total_turns=total_q,
    )

    prompt = QUESTION_GEN_PROMPT.format(
        target_role=target_role,
        interview_mode=interview_mode,
        turn_number=turn_number,
        total_questions=total_q,
        candidate_name=candidate_name,
        resume_summary=resume_summary or "Not provided",
        previous_qa=previous_qa,
        training_context=training_context,
        phase_instruction=phase_instruction,
        difficulty_instruction=difficulty_instruction,
        question_phase=phase,
    )

    try:
        provider = get_llm_provider()
        question = await provider.complete(INTERVIEWER_PERSONA, prompt, temperature=0.5)
        return question.strip(), phase
    except Exception as e:
        logger.warning(f"LLM question generation failed: {e}. Using fallback.")
        fallback = FALLBACK_QUESTIONS.get(phase, FALLBACK_QUESTIONS["technical_deep_dive"])
        return fallback, phase


# ═══════════════════════════════════════════════════════════════════
#  Evaluate Answer
# ═══════════════════════════════════════════════════════════════════

async def evaluate_answer(
    candidate_name: str,
    target_role: str,
    interview_mode: str,
    turn_number: int,
    total_questions: int,
    question: str,
    answer: str,
    resume_summary: str | None = None,
) -> EvaluationResult:
    """Evaluate a candidate's answer using multi-criteria AI scoring."""
    scoring_context = format_scoring_context_for_prompt(question)

    prompt = EVALUATION_PROMPT.format(
        target_role=target_role,
        interview_mode=interview_mode,
        candidate_name=candidate_name,
        turn_number=turn_number,
        total_questions=total_questions,
        question=question,
        answer=answer,
        resume_summary=resume_summary or "Not provided",
        scoring_context=scoring_context,
    )

    try:
        provider = get_llm_provider()
        result = await provider.complete_json(
            system_prompt=INTERVIEWER_PERSONA + "\n\nYou are now in EVALUATION mode. Score the answer objectively.",
            user_prompt=prompt,
        )

        return EvaluationResult(
            overall_score=round(float(result.get("overall_score", 5.0)), 1),
            technical_accuracy=result.get("technical_accuracy", {"score": 5.0, "comment": "N/A"}),
            depth_detail=result.get("depth_detail", {"score": 5.0, "comment": "N/A"}),
            practical_experience=result.get("practical_experience", {"score": 5.0, "comment": "N/A"}),
            communication=result.get("communication", {"score": 5.0, "comment": "N/A"}),
            problem_solving=result.get("problem_solving", {"score": 5.0, "comment": "N/A"}),
            feedback=result.get("feedback", "Evaluation completed."),
            improvement_tips=result.get("improvement_tips", []),
            strengths=result.get("strengths", []),
            follow_up_question=result.get("follow_up_question"),
        )
    except Exception as e:
        logger.warning(f"LLM evaluation failed: {e}. Using fallback scoring.")
        return _fallback_score(answer)


# ═══════════════════════════════════════════════════════════════════
#  Generate Final Report
# ═══════════════════════════════════════════════════════════════════

async def generate_report(
    candidate_name: str,
    target_role: str,
    interview_mode: str,
    turns: list[dict],
) -> dict:
    """Generate a comprehensive AI assessment report."""
    transcript = ""
    scores_parts = []
    for t in turns:
        transcript += f"\n--- Question {t['turn']} ---\n"
        transcript += f"Q: {t['question']}\n"
        transcript += f"A: {t.get('answer', 'No answer')}\n"
        if t.get("score"):
            transcript += f"Score: {t['score']}/10\n"
            scores_parts.append(f"Q{t['turn']}: {t['score']}/10")

    prompt = REPORT_PROMPT.format(
        candidate_name=candidate_name,
        target_role=target_role,
        interview_mode=interview_mode,
        transcript=transcript,
        scores_summary="\n".join(scores_parts),
    )

    try:
        provider = get_llm_provider()
        report = await provider.complete_json(
            system_prompt=INTERVIEWER_PERSONA + "\n\nYou are generating the final assessment report.",
            user_prompt=prompt,
        )
        return report
    except Exception as e:
        logger.warning(f"LLM report generation failed: {e}")
        avg = sum(t.get("score", 0) for t in turns) / max(len(turns), 1)
        return {
            "executive_summary": f"Interview completed with an average score of {avg:.1f}/10.",
            "strengths": ["Completed all questions"],
            "areas_for_improvement": ["Additional detail recommended"],
            "recommendation": "Shortlist" if avg >= 8.5 else ("Review" if avg >= 7.0 else "Reject"),
            "recommendation_reason": f"Average score: {avg:.1f}/10",
            "skill_ratings": {},
            "suggested_next_steps": "Review the detailed breakdown.",
        }


# ─── Fallback (no LLM) ──────────────────────────────────────────

def _fallback_score(answer: str) -> EvaluationResult:
    """Word-count-based fallback when LLM is unavailable."""
    words = len(answer.split())
    if words >= 120:
        score = 8.5
    elif words >= 80:
        score = 7.5
    elif words >= 50:
        score = 6.5
    elif words >= 30:
        score = 5.5
    else:
        score = 4.0

    dimension = {"score": score, "comment": "Evaluated using fallback (LLM unavailable)."}
    feedback_map = {
        8.5: "Strong answer with good depth. For more precision, add specific metrics and real outcomes.",
        7.5: "Good response. Consider adding more implementation details and trade-off analysis.",
        6.5: "Decent baseline. Strengthen with concrete examples from your experience.",
        5.5: "Answer needs more depth. Include specific tools, approaches, and measurable outcomes.",
        4.0: "Response is too brief. Elaborate with real scenarios, constraints, and solutions.",
    }

    return EvaluationResult(
        overall_score=score,
        technical_accuracy=dimension,
        depth_detail=dimension,
        practical_experience=dimension,
        communication=dimension,
        problem_solving=dimension,
        feedback=feedback_map.get(score, "Evaluation completed."),
        improvement_tips=["Provide more specific technical details", "Include metrics and measurable outcomes", "Reference real-world experience"],
        strengths=["Attempted the question"],
        follow_up_question=None,
    )
