from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class BaselineChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_type: str
    start_char: int
    end_char: int
    chunk_size: int
    overlap_chars: int
    text: str
    source_file: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
