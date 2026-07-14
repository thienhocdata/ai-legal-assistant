from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class EmbeddingManifest:
    document_id: str
    source_chunks_file: str
    embeddings_file: str
    metadata_file: str

    model_name: str
    device: str
    normalize_embeddings: bool

    chunk_count: int
    embedding_dimension: int
    dtype: str

    text_field: str
    document_prefix: str
    query_prefix: str
    source_chunks_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
