"""
Background Evaluation Worker
─────────────────────────────
Evaluates answers asynchronously using FastAPI BackgroundTasks.
Stores interim scores per turn; final report generated only after completion.

Flow:
  1. Answer submitted → saved immediately → turn marked "evaluating"
  2. Background task calls AI engine for evaluation
  3. Scores stored → turn marked "evaluated"
  4. Final report generated ONLY when all turns complete

This ensures the candidate is NOT waiting for AI evaluation between questions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import engine as ai_engine
from ..models import InterviewSession, InterviewTurn

logger = logging.getLogger(__name__)


# ─── Score Weights ────────────────────────────────────────────────
SCORE_WEIGHTS = {
    "technical_depth": 0.40,
    "scenario_handling": 0.25,
    "communication": 0.20,
    "confidence": 0.15,
}


async def evaluate_answer_background(
    db_url: str,
    turn_id: int,
    candidate_name: str,
    target_role: str,
    interview_mode: str,
    difficulty_level: str,
    turn_number: int,
    total_questions: int,
    question: str,
    answer: str,
    resume_summary: str | None,
) -> None:
    """
    Background task: evaluate a single answer via AI and store results.

    Uses a fresh DB session so it doesn't interfere with the request session.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url, future=True, pool_pre_ping=True)
    SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionFactory()

    try:
        turn = db.get(InterviewTurn, turn_id)
        if turn is None:
            logger.error(f"Turn {turn_id} not found for background evaluation.")
            return

        turn.evaluation_status = "evaluating"
        db.commit()

        # ── Call AI Engine ────────────────────────────────────
        evaluation = await ai_engine.evaluate_answer(
            candidate_name=candidate_name,
            target_role=target_role,
            interview_mode=interview_mode,
            turn_number=turn_number,
            total_questions=total_questions,
            question=question,
            answer=answer,
            resume_summary=resume_summary,
        )

        # ── Store evaluation results ─────────────────────────
        turn.score = evaluation.overall_score
        turn.feedback = evaluation.feedback
        turn.dimension_scores = json.dumps({
            "technical_accuracy": evaluation.technical_accuracy,
            "depth_detail": evaluation.depth_detail,
            "practical_experience": evaluation.practical_experience,
            "communication": evaluation.communication,
            "problem_solving": evaluation.problem_solving,
        })
        turn.improvement_tips = json.dumps(evaluation.improvement_tips)
        turn.strengths = json.dumps(evaluation.strengths)
        turn.evaluation_status = "evaluated"
        db.commit()

        # ── Check if all turns are evaluated → generate report ─
        session = db.get(InterviewSession, turn.session_id)
        if session and session.status == "evaluating":
            all_turns = db.scalars(
                select(InterviewTurn)
                .where(InterviewTurn.session_id == session.id)
                .order_by(InterviewTurn.turn_number.asc())
            ).all()

            all_evaluated = all(t.evaluation_status == "evaluated" for t in all_turns)
            if all_evaluated:
                await _generate_final_report(db, session, all_turns)

        logger.info(f"Background evaluation completed for turn {turn_id}")

    except Exception as e:
        logger.error(f"Background evaluation failed for turn {turn_id}: {e}", exc_info=True)
        # Mark as evaluated with fallback so the session isn't stuck
        try:
            turn = db.get(InterviewTurn, turn_id)
            if turn and turn.evaluation_status != "evaluated":
                turn.evaluation_status = "evaluated"
                turn.score = turn.score or 5.0
                turn.feedback = turn.feedback or f"Evaluation fallback (background error): {str(e)[:200]}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


async def _generate_final_report(
    db: Session,
    session: InterviewSession,
    turns: list[InterviewTurn],
) -> None:
    """Generate AI report and compute weighted score breakdown."""
    turns_data = []
    tech_scores = []
    scenario_scores = []
    comm_scores = []
    conf_scores = []

    for t in turns:
        turns_data.append({
            "turn": t.turn_number,
            "question": t.question,
            "answer": t.answer,
            "score": t.score,
        })

        # Map dimension scores to weighted categories
        if t.dimension_scores:
            try:
                dims = json.loads(t.dimension_scores)
                ta = dims.get("technical_accuracy", {}).get("score", 5.0)
                dd = dims.get("depth_detail", {}).get("score", 5.0)
                pe = dims.get("practical_experience", {}).get("score", 5.0)
                co = dims.get("communication", {}).get("score", 5.0)
                ps = dims.get("problem_solving", {}).get("score", 5.0)

                # Map to weighted categories:
                # Technical Depth = avg(technical_accuracy, depth_detail)
                tech_scores.append((ta + dd) / 2)
                # Scenario Handling = avg(practical_experience, problem_solving)
                scenario_scores.append((pe + ps) / 2)
                # Communication
                comm_scores.append(co)
                # Confidence ≈ communication quality (approximation)
                conf_scores.append((co + pe) / 2)
            except (json.JSONDecodeError, TypeError):
                pass

    # ── Compute weighted breakdown ────────────────────────────
    def avg(lst: list[float]) -> float:
        return sum(lst) / len(lst) if lst else 5.0

    tech = round(avg(tech_scores), 1)
    scenario = round(avg(scenario_scores), 1)
    comm = round(avg(comm_scores), 1)
    conf = round(avg(conf_scores), 1)
    weighted = round(
        tech * SCORE_WEIGHTS["technical_depth"]
        + scenario * SCORE_WEIGHTS["scenario_handling"]
        + comm * SCORE_WEIGHTS["communication"]
        + conf * SCORE_WEIGHTS["confidence"],
        1,
    )

    session.score_technical_depth = tech
    session.score_scenario_handling = scenario
    session.score_communication = comm
    session.score_confidence = conf
    session.score_weighted_total = weighted

    # ── Generate AI report for paid modes ─────────────────────
    if session.interview_mode in ("mock_paid", "enterprise"):
        try:
            report = await ai_engine.generate_report(
                candidate_name=session.candidate_name,
                target_role=session.target_role,
                interview_mode=session.interview_mode,
                turns=turns_data,
            )
            session.ai_report = json.dumps(report, default=str)
        except Exception as e:
            logger.error(f"Report generation failed: {e}")

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    db.commit()
