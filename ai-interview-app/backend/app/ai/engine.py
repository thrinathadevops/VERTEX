"""
AI Interview Engine (Orchestrator)
──────────────────────────────────
Coordinates the full AI-powered interview flow:
  1. Generate interviewer introduction
  2. Generate contextual questions from resume
  3. Evaluate answers with multi-criteria scoring
  4. Generate follow-up questions
  5. Produce final assessment report
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

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

# Question counts per mode
QUESTION_COUNTS = {
    "mock_free": 5,
    "mock_paid": 5,
    "real": 7,
}

# Fallback questions when LLM is unavailable
FALLBACK_QUESTIONS = {
    "mock_free": [
        "Describe a production incident you handled and how you restored service.",
        "How do you design CI/CD pipelines for both deployment speed and safe rollback?",
        "How would you secure container workloads in a multi-tenant Kubernetes cluster?",
        "Explain your approach for cloud cost optimisation without reducing reliability.",
        "How do you define SLOs and use observability to improve system resilience?",
    ],
    "mock_paid": [
        "Walk through your approach to building a zero-downtime deployment pipeline.",
        "A critical microservice is experiencing cascading failures — walk us through your incident response.",
        "How would you implement Infrastructure as Code for a multi-cloud environment?",
        "Describe how you would set up comprehensive monitoring and alerting for a microservices platform.",
        "How do you balance developer velocity with security compliance in a DevSecOps pipeline?",
    ],
    "real": [
        "Architect a zero-downtime deployment pipeline for a financial-grade microservices platform.",
        "You discover a lateral-movement attempt in your cluster. Walk us through your incident response playbook.",
        "Your CTO asks you to cut cloud spend by 30% while maintaining 99.95% availability. Detail your strategy.",
        "Explain how you would migrate a monolith to event-driven microservices with data consistency guarantees.",
        "Design a multi-region disaster-recovery strategy for a real-time payments SaaS. Include RTO/RPO targets.",
        "Implement a comprehensive DevSecOps pipeline balancing security scanning, velocity, and compliance.",
        "Onboard 50 microservices to a service mesh. Cover technical approach, org buy-in, and risk mitigation.",
    ],
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


# ─── Generate Introduction ────────────────────────────────────────

async def generate_introduction(
    candidate_name: str,
    target_role: str,
    interview_mode: str,
    resume_summary: str | None = None,
) -> str:
    """Generate the AI interviewer's opening introduction."""
    total_q = QUESTION_COUNTS.get(interview_mode, 5)

    resume_section = ""
    if resume_summary and len(resume_summary.strip()) > 20:
        resume_section = f"RESUME SUMMARY:\n{resume_summary}"
    else:
        resume_section = "RESUME: Not provided"

    prompt = INTRODUCTION_PROMPT.format(
        target_role=target_role,
        interview_mode="practice" if interview_mode != "real" else "enterprise assessment",
        candidate_name=candidate_name,
        total_questions=total_q,
        resume_section=resume_section,
    )

    try:
        provider = get_llm_provider()
        intro = await provider.complete(INTERVIEWER_PERSONA, prompt, temperature=0.6)
        return intro.strip()
    except Exception as e:
        logger.warning(f"LLM introduction generation failed: {e}")
        mode_label = "Enterprise Assessment" if interview_mode == "real" else "Practice Session"
        return (
            f"Hello {candidate_name}! I'm Aria, your AI technical interviewer at VAREX. "
            f"I'll be conducting your {mode_label} for the {target_role} position today. "
            f"We'll go through {total_q} questions covering technical depth, real-world scenarios, "
            f"and problem-solving. Take your time with each answer — depth and specifics matter. Let's begin!"
        )


# ─── Generate Question ───────────────────────────────────────────

async def generate_question(
    candidate_name: str,
    target_role: str,
    interview_mode: str,
    turn_number: int,
    resume_summary: str | None = None,
    previous_turns: list[dict] | None = None,
) -> str:
    """Generate the next contextual interview question."""
    total_q = QUESTION_COUNTS.get(interview_mode, 5)

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
    )

    try:
        provider = get_llm_provider()
        question = await provider.complete(INTERVIEWER_PERSONA, prompt, temperature=0.5)
        return question.strip()
    except Exception as e:
        logger.warning(f"LLM question generation failed: {e}. Using fallback.")
        fb = FALLBACK_QUESTIONS.get(interview_mode, FALLBACK_QUESTIONS["mock_free"])
        idx = min(turn_number - 1, len(fb) - 1)
        return fb[idx]


# ─── Evaluate Answer ─────────────────────────────────────────────

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
    # Inject real-world scoring rubric context
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


# ─── Generate Final Report ───────────────────────────────────────

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
