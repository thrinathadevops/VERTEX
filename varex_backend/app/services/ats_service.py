"""
ATS (Applicant Tracking System) Screening Service
Compares candidate resume text against job description using keyword
matching + optional LLM scoring.

Replace the stub _call_llm() with a real OpenAI / Gemini call when ready.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.interview import (
    CandidateProfile, JobDescription, ScreeningStatus
)


from app.services.llm_service import run_ats_analysis


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

    if not settings.GEMINI_API_KEY:
        # Fallback if no LLM key provided
        resume_lower = resume_text.lower()
        matched = [s for s in required_skills if s.lower() in resume_lower]
        missing = [s for s in required_skills if s.lower() not in resume_lower]
        ats_score = round(len(matched) / max(len(matched) + len(missing), 1) * 100, 1)
        feedback = f"Matched {len(matched)} of {len(required_skills)} skills."
    else:
        # Actual LLM Integration
        from app.services.llm_service import run_ats_analysis
        llm_result = await run_ats_analysis(resume_text, jd.description, required_skills)
        ats_score = llm_result.get("ats_score", 0)
        matched = llm_result.get("matched_skills", [])
        missing = llm_result.get("missing_skills", [])
        feedback = llm_result.get("feedback", "")
    
    recommendation = (
        "Shortlist" if ats_score >= 70
        else "Review" if ats_score >= 40
        else "Reject"
    )

    report = {
        "matched_skills": matched,
        "missing_skills": missing,
        "summary": feedback,
        "recommendation": recommendation,
    }

    # Persist
    candidate.ats_score = ats_score
    candidate.ats_report = report
    candidate.screening_status = (
        ScreeningStatus.shortlisted
        if recommendation == "Shortlist"
        else ScreeningStatus.rejected
        if recommendation == "Reject"
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
