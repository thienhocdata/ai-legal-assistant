from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class LegalChunkMetadata:
    document_number: str | None = None
    document_type: str | None = None
    issued_date: str | None = None
    effective_date: str | None = None
    language: str = "vi"
    jurisdiction: str = "VN"
    source_file: str | None = None


@dataclass(slots=True)
class LegalChunk:
    chunk_id: str
    document_id: str
    document_name: str

    article_no: int
    article_title: str
    chapter_no: str | None
    chapter_title: str | None
    section_no: int | None
    section_title: str | None

    clause_nos: list[int] = field(default_factory=list)
    point_nos: list[str] = field(default_factory=list)

    strategy: str = "article"
    chunk_index: int = 1
    chunk_count: int = 1

    source_node_id: str = ""
    source_path: list[str] = field(default_factory=list)
    parent_id: str = ""

    text: str = ""
    clean_text: str = ""
    char_count: int = 0

    metadata: LegalChunkMetadata = field(
        default_factory=LegalChunkMetadata
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
