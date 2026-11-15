from __future__ import annotations

import os
from typing import Any

from .base import BaseLLMProvider, LLMResponse, ProviderRequestError, ProviderResponseError


class GeminiProvider(BaseLLMProvider):
    """Gemini Interactions API provider using the official Google GenAI SDK."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "gemini-3.5-flash",
    ) -> None:
        key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            raise ValueError("Thiếu GEMINI_API_KEY.")
        try:
            from google import genai
        except ImportError as exc:
            raise ImportError("Hãy cài package google-genai.") from exc
        self.model = model
        self._client: Any = genai.Client(api_key=key)

    def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            interaction = self._client.interactions.create(
                model=self.model,
                input=f"{system_prompt}\n\nYÊU CẦU NGƯỜI DÙNG:\n{user_prompt}",
                store=False,
            )
        except Exception as exc:
            raise ProviderRequestError("Không thể gọi Gemini.") from exc
        text = str(getattr(interaction, "output_text", "") or "").strip()
        if not text:
            raise ProviderResponseError("Gemini không trả về nội dung văn bản.")
        return LLMResponse(
            text=text,
            provider="gemini",
            model=self.model,
            metadata={"interaction_id": getattr(interaction, "id", None)},
        )
