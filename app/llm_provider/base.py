from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


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
