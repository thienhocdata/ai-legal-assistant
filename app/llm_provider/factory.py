from __future__ import annotations

import os

from .base import BaseLLMProvider
from .extractive_provider import ExtractiveProvider
from .gemini_provider import GeminiProvider
from .openai_compatible_provider import OpenAICompatibleProvider
from .openrouter_provider import DEFAULT_OPENROUTER_MODEL, OpenRouterProvider


def create_llm_provider(name: str | None = None) -> BaseLLMProvider:
    selected = (name or os.getenv("LLM_PROVIDER", "none")).strip().lower()
    if selected in {"", "none", "extractive", "local"}:
        return ExtractiveProvider()
    if selected == "gemini":
        return GeminiProvider(model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"))
    if selected == "openrouter":
        return OpenRouterProvider(
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            model=os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "45")),
            max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "8192")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "0")),
        )
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
