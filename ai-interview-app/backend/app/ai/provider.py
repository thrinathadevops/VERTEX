"""
LLM Provider Abstraction Layer
──────────────────────────────
Supports: OpenAI GPT-4o, Google Gemini, Ollama (self-hosted)
Switch providers via AI_PROVIDER environment variable.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

from ..config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
        """Send a prompt and return the text completion."""
        ...

    @abstractmethod
    async def complete_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
        """Send a prompt and return parsed JSON."""
        ...


# ─── OpenAI ────────────────────────────────────────────────────────
class OpenAIProvider(LLMProvider):
    def __init__(self):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""

    async def complete_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or "{}"
        return json.loads(text)


# ─── Google Gemini ─────────────────────────────────────────────────
class GeminiProvider(LLMProvider):
    def __init__(self):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Install google-generativeai: pip install google-generativeai")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._genai = genai
        self.model_name = settings.GEMINI_MODEL

    async def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
        model = self._genai.GenerativeModel(
            self.model_name,
            system_instruction=system_prompt,
            generation_config=self._genai.GenerationConfig(temperature=temperature, max_output_tokens=2048),
        )
        response = await model.generate_content_async(user_prompt)
        return response.text or ""

    async def complete_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
        model = self._genai.GenerativeModel(
            self.model_name,
            system_instruction=system_prompt + "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no code fences.",
            generation_config=self._genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=2048,
                response_mime_type="application/json",
            ),
        )
        response = await model.generate_content_async(user_prompt)
        text = (response.text or "{}").strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(text)


# ─── Ollama (Self-hosted) ─────────────────────────────────────────
class OllamaProvider(LLMProvider):
    def __init__(self):
        import httpx
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self._client = httpx.AsyncClient(timeout=120)

    async def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
        response = await self._client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "options": {"temperature": temperature},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    async def complete_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
        text = await self.complete(
            system_prompt + "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no extra text.",
            user_prompt,
            temperature,
        )
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(text)


# ─── Factory ──────────────────────────────────────────────────────
_provider_instance: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider singleton."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    name = settings.AI_PROVIDER.lower()
    logger.info(f"Initializing LLM provider: {name}")

    if name == "openai":
        _provider_instance = OpenAIProvider()
    elif name == "gemini":
        _provider_instance = GeminiProvider()
    elif name == "ollama":
        _provider_instance = OllamaProvider()
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {name}. Use 'openai', 'gemini', or 'ollama'.")

    return _provider_instance
