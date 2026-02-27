"""
Resume Parser
─────────────
Extracts text from PDF and DOCX files.
Optionally uses LLM to create a structured summary.
"""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file using PyMuPDF."""
    try:
        import fitz  # pymupdf
    except ImportError:
        raise ImportError("Install pymupdf: pip install pymupdf")

    text_parts: list[str] = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract all text from a DOCX file."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("Install python-docx: pip install python-docx")

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Detect file type and extract text."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif lower.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace").strip()
    else:
        raise ValueError(f"Unsupported resume format: {filename}. Use PDF, DOCX, or TXT.")


async def parse_resume_with_llm(resume_text: str) -> dict:
    """Use the LLM to extract structured info from resume text."""
    from .provider import get_llm_provider
    from .prompts import RESUME_PARSE_PROMPT

    if not resume_text or len(resume_text.strip()) < 50:
        return {
            "name": "",
            "current_role": "",
            "years_experience": 0,
            "companies": [],
            "key_skills": [],
            "certifications": [],
            "education": "",
            "notable_projects": [],
            "summary": "Resume text too short or empty to parse.",
        }

    provider = get_llm_provider()
    prompt = RESUME_PARSE_PROMPT.format(resume_text=resume_text[:4000])

    try:
        result = await provider.complete_json(
            system_prompt="You are a resume parsing assistant. Extract structured data from resumes. Return ONLY valid JSON.",
            user_prompt=prompt,
        )
        return result
    except Exception as e:
        logger.error(f"LLM resume parsing failed: {e}")
        return {
            "name": "",
            "current_role": "",
            "years_experience": 0,
            "companies": [],
            "key_skills": [],
            "certifications": [],
            "education": "",
            "notable_projects": [],
            "summary": f"Failed to parse resume: {str(e)}",
        }
