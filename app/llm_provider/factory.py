from __future__ import annotations

import os

from .base import BaseLLMProvider
from .extractive_provider import ExtractiveProvider
from .gemini_provider import GeminiProvider
from .openai_compatible_provider import OpenAICompatibleProvider


def create_llm_provider(name: str | None = None) -> BaseLLMProvider:
    selected = (name or os.getenv("LLM_PROVIDER", "none")).strip().lower()
    if selected in {"", "none", "extractive", "local"}:
        return ExtractiveProvider()
    if selected == "gemini":
        return GeminiProvider(model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"))
    if selected == "qwen":
        return OpenAICompatibleProvider(
            api_key=(
                os.getenv("QWEN_API_KEY", "").strip()
                or os.getenv("DASHSCOPE_API_KEY", "").strip()
            ),
            base_url=os.getenv(
                "QWEN_BASE_URL",
                "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            ),
            model=os.getenv("QWEN_MODEL", "qwen-plus"),
            provider_name="qwen",
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "45")),
            max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "800")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "1")),
        )
    raise ValueError(f"LLM_PROVIDER chưa được hỗ trợ: {selected}")
