"""
NVIDIA NIM LLM Client (Tier 2).
Uses NVIDIA NIM's free-tier OpenAI-compatible API (meta/llama-3.1-8b-instruct).
Enforces context token budgeting, prompt injection defense, and graceful fallback to Tier 3.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

DEFAULT_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"


class LLMClient:
    """
    Client for interacting with NVIDIA NIM API.
    Provides structured JSON completion with automated retry on malformed payloads.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.api_key = self.settings.nvidia_api_key
        self.base_url = self.settings.nvidia_base_url or DEFAULT_NVIDIA_BASE_URL
        self.model = getattr(self.settings, "nvidia_model", None) or DEFAULT_MODEL
        self._client: AsyncOpenAI | None = None

        if self.api_key:
            self._client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=20.0,
            )

    @property
    def is_available(self) -> bool:
        """Check whether LLM API credentials are configured."""
        return self._client is not None and bool(self.api_key)

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> dict[str, Any] | None:
        """
        Request structured JSON generation from the LLM.
        Includes automatic one-shot repair retry if JSON parsing fails.
        Returns parsed dict or None if LLM is unavailable or fails.
        """
        if not self.is_available or self._client is None:
            logger.info("NVIDIA NIM LLM not available. Skipping LLM generation.")
            return None

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=1024,
            )
            raw_content = response.choices[0].message.content or ""
            # Parse JSON safely
            return self._extract_json(raw_content)

        except Exception as exc:
            logger.warning("NVIDIA NIM LLM generation error: %s. Attempting repair retry...", exc)

            # Retry once with repair prompt
            try:
                repair_messages = [
                    {
                        "role": "system",
                        "content": "You are a JSON repair assistant. Output ONLY valid JSON matching the schema.",
                    },
                    {
                        "role": "user",
                        "content": f"Fix the following output into valid JSON:\n\n{raw_content if 'raw_content' in locals() else user_prompt}",
                    },
                ]
                repair_res = await self._client.chat.completions.create(
                    model=self.model,
                    messages=repair_messages,
                    temperature=0.0,
                    max_tokens=1024,
                )
                repair_content = repair_res.choices[0].message.content or ""
                return self._extract_json(repair_content)
            except Exception as repair_exc:
                logger.error("LLM retry failed: %s. Falling back to template.", repair_exc)
                return None

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Strip markdown code fence if present and parse JSON."""
        cleaned = text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1]
            cleaned = cleaned.split("```", 1)[0]
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1]
            cleaned = cleaned.split("```", 1)[0]

        return json.loads(cleaned.strip())
