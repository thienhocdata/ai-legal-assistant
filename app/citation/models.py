from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Citation:
    citation_id: str
    chunk_id: str
    document_id: str
    document_name: str
    article_no: int
    article_title: str
    clause_nos: list[int] = field(default_factory=list)
    point_nos: list[str] = field(default_factory=list)
    quote: str = ""
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
