"""Request-local network timeouts; no mutation of a shared hosted client."""
from time import perf_counter

from .base import BaseLLMProvider, LLMResponse, ProviderRequestError
from .openai_compatible_provider import OpenAICompatibleProvider


class RequestScopedProvider(BaseLLMProvider):
    def __init__(self, delegate: BaseLLMProvider, *, deadline: float, stage_limit_seconds: float):
        self.delegate = delegate
        self.deadline = deadline
        self.stage_limit_seconds = stage_limit_seconds
        self.budget_enforced = isinstance(delegate, OpenAICompatibleProvider)

    def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        remaining = self.deadline - perf_counter()
        if remaining <= 0:
            raise ProviderRequestError("Đã hết thời gian chờ mô hình cho lượt này.")
        if isinstance(self.delegate, OpenAICompatibleProvider):
            return self.delegate.generate(
                system_prompt=system_prompt, user_prompt=user_prompt,
                request_timeout_seconds=min(remaining, self.stage_limit_seconds, self.delegate.timeout_seconds),
                request_max_retries=0,
            )
        # Generic adapters retain their own timeout. This is not a guarantee of
        # wall-clock cancellation, including for httpx's per-operation timeout.
        return self.delegate.generate(system_prompt=system_prompt, user_prompt=user_prompt)
