from __future__ import annotations

import os

from .base import BaseLLMProvider
from .extractive_provider import ExtractiveProvider
from .gemini_provider import GeminiProvider


def create_llm_provider(name: str | None = None) -> BaseLLMProvider:
    selected = (name or os.getenv("LLM_PROVIDER", "none")).strip().lower()
    if selected in {"", "none", "extractive", "local"}:
        return ExtractiveProvider()
    if selected == "gemini":
        return GeminiProvider(model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"))
    raise ValueError(f"LLM_PROVIDER chưa được hỗ trợ: {selected}")
