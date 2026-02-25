"""
ATS (Applicant Tracking System) Screening Service
Compares candidate resume text against job description using keyword
matching + optional LLM scoring.

Replace the stub _call_llm() with a real OpenAI / Gemini call when ready.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.interview import (
    CandidateProfile, JobDescription, ScreeningStatus
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _skill_match(resume: str, required_skills: list[str]) -> tuple[list, list]:
    """Simple keyword scan — swap for embeddings/LLM in production."""
    resume_lower = resume.lower()
    matched = [s for s in required_skills if s.lower() in resume_lower]
    missing = [s for s in required_skills if s.lower() not in resume_lower]
    return matched, missing


async def _call_llm_ats(
    resume_text: str,
    jd_text: str,
    screening_prompt: str | None,
    matched: list,
    missing: list,
) -> dict:
    """
    Placeholder for LLM-powered deep screening.

    Prompt strategy:
      System : "You are a senior technical recruiter. Evaluate this resume
                against the job description. {screening_prompt or ''}"
      User   : "JD: {jd_text}

Resume: {resume_text}


                Matched skills: {matched}
Missing skills: {missing}"

    Expected JSON response:
      {summary, technical_fit_score (0-10), soft_skills_score (0-10),
       recommendation: Shortlist|Reject|Review}
    """
    # STUB — replace with openai.ChatCompletion or similar
    score = round(len(matched) / max(len(matched) + len(missing), 1) * 100, 1)
    recommendation = (
        "Shortlist" if score >= 70
        else "Review" if score >= 40
        else "Reject"
    )
    return {
        "summary": (
            f"Candidate matches {len(matched)} of "
            f"{len(matched)+len(missing)} required skills. "
            f"Score: {score}/100. Recommendation: {recommendation}."
        ),
        "recommendation": recommendation,
    }


# ── Main service function ──────────────────────────────────────────────────────

async def run_ats_scan(db: AsyncSession, candidate_id: UUID) -> dict:
    """
    1. Load candidate + JD from DB
    2. Run skill-keyword match
    3. Call LLM stub for summary & recommendation
    4. Persist results back to candidate row
    5. Return structured report
    """
    candidate = await db.get(CandidateProfile, candidate_id)
    if not candidate:
        raise ValueError("Candidate not found")

    jd = await db.get(JobDescription, candidate.job_description_id)
    if not jd:
        raise ValueError("Job description not found")

    required_skills: list[str] = jd.required_skills or []
    resume_text: str = candidate.resume_text or ""

    matched, missing = _skill_match(resume_text, required_skills)

    ats_score = round(len(matched) / max(len(matched) + len(missing), 1) * 100, 1)

    llm_result = await _call_llm_ats(
        resume_text=resume_text,
        jd_text=jd.description,
        screening_prompt=jd.screening_prompt,
        matched=matched,
        missing=missing,
    )

    report = {
        "matched_skills": matched,
        "missing_skills": missing,
        "summary": llm_result["summary"],
        "recommendation": llm_result["recommendation"],
    }

    # Persist
    candidate.ats_score = ats_score
    candidate.ats_report = report
    candidate.screening_status = (
        ScreeningStatus.shortlisted
        if llm_result["recommendation"] == "Shortlist"
        else ScreeningStatus.rejected
        if llm_result["recommendation"] == "Reject"
        else ScreeningStatus.screened
    )
    await db.commit()
    await db.refresh(candidate)

    return {
        "candidate_id": candidate.id,
        "ats_score": ats_score,
        **report,
        "screening_status": candidate.screening_status,
    }
