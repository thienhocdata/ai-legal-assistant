from __future__ import annotations

from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.embedding.base import BaseEmbedder


EMBEDDINGS_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings.npy"
)

METADATA_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings_metadata.json"
)

MANIFEST_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings_manifest.json"
)


class FakeEmbedder(BaseEmbedder):
    """Embedder giả để unit test không tải model."""

    @property
    def model_name(self) -> str:
        return "fake-embedder"

    @property
    def dimension(self) -> int:
        return 4

    def _encode(
        self,
        texts: list[str],
    ) -> np.ndarray:
        rows = []

        for index, text in enumerate(texts):
            if not str(text).strip():
                raise ValueError("Text rỗng.")

            vector = np.array(
                [
                    float(index + 1),
                    float(len(text)),
                    1.0,
                    2.0,
                ],
                dtype=np.float32,
            )
            vector /= np.linalg.norm(vector)
            rows.append(vector)

        return np.vstack(rows)

    def encode_documents(
        self,
        texts,
        *,
        batch_size: int = 32,
    ) -> np.ndarray:
        return self._encode(list(texts))

    def encode_queries(
        self,
        texts,
        *,
        batch_size: int = 32,
    ) -> np.ndarray:
        return self._encode(list(texts))


def test_fake_embedder() -> None:
    embedder = FakeEmbedder()
    vectors = embedder.encode_documents(
        ["Điều 1", "Điều 2"]
    )

    assert vectors.shape == (2, 4)
    assert vectors.dtype == np.float32
    assert np.allclose(
        np.linalg.norm(vectors, axis=1),
        1.0,
        atol=1e-6,
    )


def test_generated_embedding_files() -> None:
    if not EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(
            f"Chưa có embeddings: {EMBEDDINGS_PATH}\n"
            "Chạy trước: python scripts\\build_embeddings.py"
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Chưa có metadata: {METADATA_PATH}"
        )

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Chưa có manifest: {MANIFEST_PATH}"
        )

    embeddings = np.load(
        EMBEDDINGS_PATH
    )

    metadata = json.loads(
        METADATA_PATH.read_text(
            encoding="utf-8"
        )
    )

    manifest = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert embeddings.ndim == 2
    assert embeddings.dtype == np.float32
    assert embeddings.shape[0] == len(metadata)
    assert embeddings.shape[0] == manifest[
        "chunk_count"
    ]
    assert embeddings.shape[1] == manifest[
        "embedding_dimension"
    ]
    assert len(manifest.get("source_chunks_sha256", "")) == 64
    assert all(len(row.get("text_sha256", "")) == 64 for row in metadata)

    vector_indexes = [
        row["vector_index"]
        for row in metadata
    ]
    assert vector_indexes == list(
        range(len(metadata))
    )

    chunk_ids = [
        row["chunk_id"]
        for row in metadata
    ]
    assert len(chunk_ids) == len(
        set(chunk_ids)
    )

    assert np.isfinite(embeddings).all()

    if manifest["normalize_embeddings"]:
        norms = np.linalg.norm(
            embeddings,
            axis=1,
        )
        assert np.allclose(
            norms,
            1.0,
            atol=1e-3,
        )


def main() -> None:
    test_fake_embedder()
    test_generated_embedding_files()

    embeddings = np.load(
        EMBEDDINGS_PATH
    )
    manifest = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    print("=" * 80)
    print("MODULE 7 - EMBEDDING VALIDATION")
    print("=" * 80)
    print(f"Vectors          : {embeddings.shape[0]}")
    print(f"Dimension        : {embeddings.shape[1]}")
    print(f"Dtype            : {embeddings.dtype}")
    print(f"Model            : {manifest['model_name']}")
    print("NaN/Infinity     : 0")
    print("Status           : SUCCESS")


if __name__ == "__main__":
    main()
