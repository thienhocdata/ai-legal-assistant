from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class QueryAnalysis:
    original_question: str
    rewritten_question: str
    intent: str
    keywords: list[str] = field(default_factory=list)
    article_refs: list[int] = field(default_factory=list)
    clause_refs: list[int] = field(default_factory=list)
    point_refs: list[str] = field(default_factory=list)
    in_scope: bool = True
    requires_clarification: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ClarificationResult:
    status: str
    questions: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
