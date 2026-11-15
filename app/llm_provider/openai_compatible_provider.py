from __future__ import annotations

from typing import Any
from time import sleep

import httpx

from .base import (
    BaseLLMProvider,
    LLMResponse,
    ProviderRequestError,
    ProviderResponseError,
)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Hosted chat-completions provider with an OpenAI-compatible API."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        provider_name: str,
        timeout_seconds: float = 45.0,
        max_output_tokens: int = 800,
        max_retries: int = 1,
        retry_backoff_seconds: float = 0.25,
        client: Any | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError(f"Thiếu API key cho provider {provider_name}.")
        if not base_url.strip():
            raise ValueError("Thiếu base URL của provider.")
        if not model.strip():
            raise ValueError("Thiếu tên model.")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.provider_name = provider_name.strip().lower()
        self.timeout_seconds = timeout_seconds
        if max_output_tokens <= 0:
            raise ValueError("max_output_tokens phải lớn hơn 0.")
        if max_retries < 0:
            raise ValueError("max_retries không được âm.")
        self.max_output_tokens = max_output_tokens
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": self.max_output_tokens,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                retryable = exc.response.status_code == 429 or exc.response.status_code >= 500
                if not retryable or attempt >= self.max_retries:
                    raise ProviderRequestError(
                        f"{self.provider_name} HTTP {exc.response.status_code}."
                    ) from exc
            except httpx.RequestError as exc:
                if attempt >= self.max_retries:
                    raise ProviderRequestError(
                        f"Không thể kết nối provider {self.provider_name}."
                    ) from exc
            if self.retry_backoff_seconds > 0:
                sleep(self.retry_backoff_seconds * (attempt + 1))
        if response is None:
            raise ProviderRequestError(f"Provider {self.provider_name} không phản hồi.")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderResponseError(
                f"{self.provider_name} trả về nội dung không phải JSON hợp lệ."
            ) from exc
        try:
            text = str(payload["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(
                f"{self.provider_name} trả về payload không đúng định dạng."
            ) from exc
        if not text:
            raise ProviderResponseError(
                f"{self.provider_name} không trả về nội dung văn bản."
            )
        usage = payload.get("usage") if isinstance(payload, dict) else None
        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=self.model,
            metadata={"usage": usage or {}},
        )
