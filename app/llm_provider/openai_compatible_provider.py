from __future__ import annotations

from typing import Any
from time import sleep
import math

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

    def generate(
        self, *, system_prompt: str, user_prompt: str,
        request_timeout_seconds: float | None = None,
        request_max_retries: int | None = None,
    ) -> LLMResponse:
        timeout = self.timeout_seconds if request_timeout_seconds is None else request_timeout_seconds
        retries = self.max_retries if request_max_retries is None else request_max_retries
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Timeout phải là số hữu hạn lớn hơn 0.")
        if type(retries) is not int or retries < 0:
            raise ValueError("Số retry phải là số nguyên không âm.")
        response = None
        for attempt in range(retries + 1):
            try:
                response = self._client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=self._request_body(system_prompt, user_prompt),
                    timeout=timeout,
                )
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                retryable = exc.response.status_code == 429 or exc.response.status_code >= 500
                if not retryable or attempt >= retries:
                    raise ProviderRequestError(
                        f"{self.provider_name} HTTP {exc.response.status_code}."
                    ) from exc
            except httpx.RequestError as exc:
                if attempt >= retries:
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
        if isinstance(payload, dict) and payload.get("error"):
            raise ProviderResponseError(f"{self.provider_name} báo lỗi sinh câu trả lời.")
        try:
            choice = payload["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(
                f"{self.provider_name} trả về payload không đúng định dạng."
            ) from exc
        if finish_reason == "length":
            raise ProviderResponseError(
                f"{self.provider_name} trả lời bị cắt do giới hạn token."
            )
        if finish_reason == "error":
            raise ProviderResponseError(f"{self.provider_name} báo lỗi sinh câu trả lời.")
        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseError(
                f"{self.provider_name} không trả về nội dung văn bản."
            )
        text = content.strip()
        usage = payload.get("usage") if isinstance(payload, dict) else None
        metadata = {"usage": usage or {}}
        if finish_reason is not None:
            metadata["finish_reason"] = finish_reason
        reported_model = payload.get("model")
        actual_model = reported_model.strip() if isinstance(reported_model, str) and reported_model.strip() else self.model
        metadata["requested_model"] = self.model
        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=actual_model,
            metadata=metadata,
        )

    def _request_body(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": self.max_output_tokens,
            "stream": False,
        }
