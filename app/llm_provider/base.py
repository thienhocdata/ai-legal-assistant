from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ProviderError(RuntimeError):
    """Expected hosted-provider failure that may safely use local fallback."""


class ProviderRequestError(ProviderError):
    """Network, timeout, rate-limit, authentication, or upstream failure."""


class ProviderResponseError(ProviderError):
    """Provider returned an empty or malformed response."""


@dataclass(slots=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        raise NotImplementedError
