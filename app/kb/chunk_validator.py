from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
from typing import Any


@dataclass(slots=True)
class ChunkValidationReport:
    chunk_count: int
    document_count: int
    empty_chunks: list[str] = field(default_factory=list)
    duplicate_ids: list[str] = field(default_factory=list)
    oversized_chunks: list[str] = field(default_factory=list)
    invalid_metadata: list[str] = field(default_factory=list)
    shortest_length: int = 0
    longest_length: int = 0
    average_length: float = 0.0

    @property
    def valid(self) -> bool:
        return not (
            self.empty_chunks
            or self.duplicate_ids
            or self.oversized_chunks
            or self.invalid_metadata
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["valid"] = self.valid
        return data


class ChunkValidator:
    """Shared validation gate for baseline and legal-aware chunks."""

    def __init__(self, *, max_chars: int, text_field: str = "clean_text") -> None:
        if max_chars <= 0:
            raise ValueError("max_chars phải lớn hơn 0.")
        self.max_chars = max_chars
        self.text_field = text_field

    def validate(
        self,
        chunks: list[dict[str, Any]],
        *,
        require_legal_metadata: bool = False,
    ) -> ChunkValidationReport:
        if not isinstance(chunks, list) or not chunks:
            raise ValueError("Danh sách chunk rỗng hoặc không hợp lệ.")

        seen: set[str] = set()
        duplicates: set[str] = set()
        empty: list[str] = []
        oversized: list[str] = []
        invalid_metadata: list[str] = []
        lengths: list[int] = []
        document_ids: set[str] = set()

        for index, chunk in enumerate(chunks):
            chunk_id = str(chunk.get("chunk_id", "")).strip()
            if not chunk_id:
                chunk_id = f"<index:{index}>"
                invalid_metadata.append(f"{chunk_id}: thiếu chunk_id")
            elif chunk_id in seen:
                duplicates.add(chunk_id)
            seen.add(chunk_id)

            document_id = str(chunk.get("document_id", "")).strip()
            if document_id:
                document_ids.add(document_id)
            else:
                invalid_metadata.append(f"{chunk_id}: thiếu document_id")

            text = str(chunk.get(self.text_field, "")).strip()
            if not text and self.text_field != "text":
                text = str(chunk.get("text", "")).strip()
            length = len(text)
            lengths.append(length)
            if not text:
                empty.append(chunk_id)
            if length > self.max_chars:
                oversized.append(chunk_id)

            if require_legal_metadata:
                if not isinstance(chunk.get("article_no"), int):
                    invalid_metadata.append(f"{chunk_id}: article_no không hợp lệ")
                if not str(chunk.get("article_title", "")).strip():
                    invalid_metadata.append(f"{chunk_id}: thiếu article_title")
                if not str(chunk.get("strategy", "")).strip():
                    invalid_metadata.append(f"{chunk_id}: thiếu strategy")

        return ChunkValidationReport(
            chunk_count=len(chunks),
            document_count=len(document_ids),
            empty_chunks=empty,
            duplicate_ids=sorted(duplicates),
            oversized_chunks=oversized,
            invalid_metadata=invalid_metadata,
            shortest_length=min(lengths),
            longest_length=max(lengths),
            average_length=sum(lengths) / len(lengths),
        )

    @staticmethod
    def load(path: str | Path) -> list[dict[str, Any]]:
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(f"Không tìm thấy file chunks: {source}")
        data = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("File chunks phải là JSON array.")
        return data
