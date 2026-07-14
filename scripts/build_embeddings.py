from __future__ import annotations

from pathlib import Path
import json
from hashlib import sha256
import os
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.embedding import (
    EmbeddingManifest,
    SentenceTransformerEmbedder,
)


INPUT_CHUNKS_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_chunks.json"
)

OUTPUT_EMBEDDINGS_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings.npy"
)

OUTPUT_METADATA_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings_metadata.json"
)

OUTPUT_MANIFEST_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings_manifest.json"
)

MODEL_NAME = "intfloat/multilingual-e5-small"
DEVICE = "cpu"
BATCH_SIZE = 32
TEXT_FIELD = "clean_text"
NORMALIZE_EMBEDDINGS = True
DOCUMENT_PREFIX = "passage: "
QUERY_PREFIX = "query: "


def load_chunks(
    path: Path,
) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy legal chunks: {path}"
        )

    chunks = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(chunks, list):
        raise ValueError(
            "legal_chunks.json phải là JSON array."
        )

    if not chunks:
        raise ValueError(
            "legal_chunks.json không có dữ liệu."
        )

    return chunks


def validate_chunks(
    chunks: list[dict],
) -> None:
    chunk_ids = []

    for index, chunk in enumerate(chunks):
        chunk_id = str(
            chunk.get("chunk_id", "")
        ).strip()
        text = str(
            chunk.get(TEXT_FIELD, "")
        ).strip()

        if not chunk_id:
            raise ValueError(
                f"Chunk tại vị trí {index} thiếu chunk_id."
            )

        if not text:
            raise ValueError(
                f"Chunk {chunk_id} thiếu {TEXT_FIELD}."
            )

        chunk_ids.append(chunk_id)

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError(
            "Phát hiện chunk_id bị trùng."
        )


def build_metadata_rows(
    chunks: list[dict],
) -> list[dict]:
    rows = []

    for vector_index, chunk in enumerate(chunks):
        rows.append(
            {
                "vector_index": vector_index,
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk.get(
                    "document_id"
                ),
                "document_name": chunk.get(
                    "document_name"
                ),
                "article_no": chunk.get(
                    "article_no"
                ),
                "article_title": chunk.get(
                    "article_title"
                ),
                "chapter_no": chunk.get(
                    "chapter_no"
                ),
                "chapter_title": chunk.get(
                    "chapter_title"
                ),
                "section_no": chunk.get(
                    "section_no"
                ),
                "section_title": chunk.get(
                    "section_title"
                ),
                "clause_nos": chunk.get(
                    "clause_nos",
                    [],
                ),
                "point_nos": chunk.get(
                    "point_nos",
                    [],
                ),
                "strategy": chunk.get(
                    "strategy"
                ),
                "char_count": chunk.get(
                    "char_count"
                ),
                "source_path": chunk.get(
                    "source_path",
                    [],
                ),
                "text_sha256": sha256(
                    str(chunk.get(TEXT_FIELD, "")).encode("utf-8")
                ).hexdigest(),
            }
        )

    return rows


def compute_chunks_sha256(chunks: list[dict]) -> str:
    digest = sha256()
    for chunk in chunks:
        digest.update(str(chunk.get("chunk_id", "")).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(chunk.get(TEXT_FIELD, "")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def atomic_save_numpy(
    array: np.ndarray,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.NamedTemporaryFile(
        dir=output_path.parent,
        suffix=".npy",
        delete=False,
    ) as temporary:
        temp_path = Path(temporary.name)

    try:
        np.save(temp_path, array)
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_json(
    data: object,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output_path.parent,
        suffix=".json",
        delete=False,
    ) as temporary:
        json.dump(
            data,
            temporary,
            ensure_ascii=False,
            indent=2,
        )
        temp_path = Path(temporary.name)

    try:
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def validate_embeddings(
    embeddings: np.ndarray,
    *,
    expected_count: int,
    expected_dimension: int,
) -> dict[str, float | int]:
    if embeddings.ndim != 2:
        raise ValueError(
            "Embedding phải là ma trận 2 chiều."
        )

    if embeddings.shape[0] != expected_count:
        raise ValueError(
            "Số vector không khớp số chunk."
        )

    if embeddings.shape[1] != expected_dimension:
        raise ValueError(
            "Embedding dimension không đúng."
        )

    if embeddings.dtype != np.float32:
        raise ValueError(
            "Embedding phải có dtype float32."
        )

    if not np.isfinite(embeddings).all():
        raise ValueError(
            "Embedding chứa NaN hoặc Infinity."
        )

    norms = np.linalg.norm(
        embeddings,
        axis=1,
    )

    if NORMALIZE_EMBEDDINGS:
        if not np.allclose(
            norms,
            1.0,
            atol=1e-3,
        ):
            raise ValueError(
                "Embedding chưa được chuẩn hóa L2."
            )

    return {
        "count": int(embeddings.shape[0]),
        "dimension": int(embeddings.shape[1]),
        "min_norm": float(norms.min()),
        "max_norm": float(norms.max()),
        "average_norm": float(norms.mean()),
    }


def main() -> None:
    chunks = load_chunks(
        INPUT_CHUNKS_PATH
    )
    validate_chunks(chunks)

    texts = [
        str(chunk[TEXT_FIELD])
        for chunk in chunks
    ]

    embedder = SentenceTransformerEmbedder(
        model_name=MODEL_NAME,
        device=DEVICE,
        normalize_embeddings=NORMALIZE_EMBEDDINGS,
        document_prefix=DOCUMENT_PREFIX,
        query_prefix=QUERY_PREFIX,
    )

    embeddings = embedder.encode_documents(
        texts,
        batch_size=BATCH_SIZE,
    )

    stats = validate_embeddings(
        embeddings,
        expected_count=len(chunks),
        expected_dimension=embedder.dimension,
    )

    metadata_rows = build_metadata_rows(
        chunks
    )

    document_id = str(
        chunks[0].get(
            "document_id",
            "unknown_document",
        )
    )

    manifest = EmbeddingManifest(
        document_id=document_id,
        source_chunks_file=str(
            INPUT_CHUNKS_PATH
        ),
        embeddings_file=str(
            OUTPUT_EMBEDDINGS_PATH
        ),
        metadata_file=str(
            OUTPUT_METADATA_PATH
        ),
        model_name=embedder.model_name,
        device=DEVICE,
        normalize_embeddings=NORMALIZE_EMBEDDINGS,
        chunk_count=stats["count"],
        embedding_dimension=stats[
            "dimension"
        ],
        dtype=str(embeddings.dtype),
        text_field=TEXT_FIELD,
        document_prefix=DOCUMENT_PREFIX,
        query_prefix=QUERY_PREFIX,
        source_chunks_sha256=compute_chunks_sha256(chunks),
    )

    atomic_save_numpy(
        embeddings,
        OUTPUT_EMBEDDINGS_PATH,
    )
    atomic_write_json(
        metadata_rows,
        OUTPUT_METADATA_PATH,
    )
    atomic_write_json(
        manifest.to_dict(),
        OUTPUT_MANIFEST_PATH,
    )

    print("=" * 80)
    print("MODULE 7 - EMBEDDING")
    print("=" * 80)
    print(f"Input chunks     : {INPUT_CHUNKS_PATH}")
    print(f"Embeddings file  : {OUTPUT_EMBEDDINGS_PATH}")
    print(f"Metadata file    : {OUTPUT_METADATA_PATH}")
    print(f"Manifest file    : {OUTPUT_MANIFEST_PATH}")
    print(f"Model            : {embedder.model_name}")
    print(f"Device           : {DEVICE}")
    print(f"Chunks embedded  : {stats['count']}")
    print(f"Dimension        : {stats['dimension']}")
    print(f"Dtype            : {embeddings.dtype}")
    print(f"Min norm         : {stats['min_norm']:.6f}")
    print(f"Max norm         : {stats['max_norm']:.6f}")
    print(f"Average norm     : {stats['average_norm']:.6f}")
    print("Status           : SUCCESS")


if __name__ == "__main__":
    main()
