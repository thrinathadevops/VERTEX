# PATH: varex_backend/app/services/llm_service.py
# Real LLM integration using Google Gemini 1.5 Flash (fast + cheap)
# Set GEMINI_API_KEY in .env
# pip install google-generativeai

import json
import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")


async def generate_interview_question(
    job_title: str,
    job_description: str,
    skills: list[str],
    turn_number: int,
    previous_qa: list[dict],
) -> str:
    history_text = ""
    for i, qa in enumerate(previous_qa, 1):
        history_text += f"Q{i}: {qa['question']}\nA{i}: {qa.get('answer', '(no answer)')}\n\n"

    prompt = f"""You are a professional technical interviewer for a {job_title} role.

Job Description: {job_description}
Required Skills: {", ".join(skills)}
Interview Turn: {turn_number}/5

Previous exchange:
{history_text if history_text else "This is the first question."}

Generate ONE focused interview question for turn {turn_number}.
- Turn 1-2: Background and experience
- Turn 3-4: Technical depth on required skills
- Turn 5: Situational/behavioural

Return ONLY the question text, no preamble."""

    response = await _model.generate_content_async(prompt)
    return response.text.strip()


async def score_answer(
    question: str,
    answer: str,
    job_title: str,
    skills: list[str],
) -> dict:
    prompt = f"""You are evaluating a candidate for a {job_title} role.
Required skills: {", ".join(skills)}

Question: {question}
Candidate Answer: {answer}

Evaluate this answer and return a JSON object with exactly these fields:
{{
  "score": <integer 1-10>,
  "feedback": "<2-3 sentence constructive feedback>",
  "strengths": ["<strength1>", "<strength2>"],
  "improvements": ["<area1>", "<area2>"]
}}

Return ONLY valid JSON, no markdown, no explanation."""

    response = await _model.generate_content_async(prompt)
    text = response.text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


async def generate_score_report(
    job_title: str,
    candidate_name: str,
    turns: list[dict],
) -> dict:
    qa_text = ""
    for i, t in enumerate(turns, 1):
        qa_text += f"Q{i}: {t['question']}\nA{i}: {t.get('answer', '(no answer)')}\nScore: {t.get('score', 'N/A')}/10\n\n"

    prompt = f"""Generate a comprehensive interview assessment report for:
Candidate: {candidate_name}
Role: {job_title}

Interview Transcript:
{qa_text}

Return a JSON object with exactly these fields:
{{
  "overall_score": <float 1-10>,
  "technical_score": <float 1-10>,
  "communication": <float 1-10>,
  "summary": "<3-4 sentence overall assessment>",
  "recommendation": "<hire|reject|consider>",
  "details": {{
    "strengths": ["<s1>", "<s2>", "<s3>"],
    "weaknesses": ["<w1>", "<w2>"],
    "hiring_notes": "<notes for hiring manager>"
  }}
}}

Return ONLY valid JSON."""

    response = await _model.generate_content_async(prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


async def run_ats_analysis(resume_text: str, job_description: str, required_skills: list[str]) -> dict:
    prompt = f"""Analyze this resume against the job requirements.

Job Description: {job_description}
Required Skills: {", ".join(required_skills)}

Resume:
{resume_text[:3000]}

Return a JSON object:
{{
  "ats_score": <integer 0-100>,
  "matched_skills": ["<skill1>", "<skill2>"],
  "missing_skills": ["<skill1>", "<skill2>"],
  "feedback": "<2-3 sentence summary>",
  "recommendations": ["<rec1>", "<rec2>"]
}}

Return ONLY valid JSON."""

    response = await _model.generate_content_async(prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
