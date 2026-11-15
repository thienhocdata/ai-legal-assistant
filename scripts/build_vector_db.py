from __future__ import annotations

from pathlib import Path
import json
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.vector_store import FaissVectorStore


EMBEDDINGS_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings.npy"
)

EMBEDDING_METADATA_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings_metadata.json"
)

EMBEDDING_MANIFEST_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings_manifest.json"
)

OUTPUT_INDEX_PATH = (
    ROOT
    / "data"
    / "vector_db"
    / "legal_chunks.faiss"
)

OUTPUT_METADATA_PATH = (
    ROOT
    / "data"
    / "vector_db"
    / "legal_chunks_metadata.json"
)

OUTPUT_MANIFEST_PATH = (
    ROOT
    / "data"
    / "vector_db"
    / "vector_store_manifest.json"
)

PROMOTION_MANIFEST_PATH = (
    ROOT
    / "data"
    / "processed"
    / "promotion_manifest.json"
)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if not EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy: {EMBEDDINGS_PATH}"
        )

    if not EMBEDDING_METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy: {EMBEDDING_METADATA_PATH}"
        )

    if not EMBEDDING_MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy: {EMBEDDING_MANIFEST_PATH}"
        )

    embeddings = np.load(
        EMBEDDINGS_PATH
    )

    metadata = json.loads(
        EMBEDDING_METADATA_PATH.read_text(
            encoding="utf-8"
        )
    )

    embedding_manifest = json.loads(
        EMBEDDING_MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(metadata, list):
        raise ValueError(
            "Embedding metadata phải là JSON array."
        )

    expected_count = int(
        embedding_manifest["chunk_count"]
    )
    expected_dimension = int(
        embedding_manifest[
            "embedding_dimension"
        ]
    )

    if embeddings.shape != (
        expected_count,
        expected_dimension,
    ):
        raise ValueError(
            "Shape embeddings không khớp manifest."
        )

    store = FaissVectorStore()
    store.build(
        embeddings,
        metadata,
    )
    store.save(
        OUTPUT_INDEX_PATH,
        OUTPUT_METADATA_PATH,
    )

    vector_manifest = {
        "provider": "faiss",
        "index_type": "IndexFlatIP",
        "metric": "cosine_similarity",
        "vector_count": int(
            store.index.ntotal
        ),
        "dimension": store.dimension,
        "model_name": embedding_manifest[
            "model_name"
        ],
        "index_file": OUTPUT_INDEX_PATH.relative_to(ROOT).as_posix(),
        "metadata_file": OUTPUT_METADATA_PATH.relative_to(ROOT).as_posix(),
    }
    if PROMOTION_MANIFEST_PATH.exists():
        promotion = json.loads(PROMOTION_MANIFEST_PATH.read_text(encoding="utf-8"))
        vector_manifest.update(
            {
                "production_replaced": True,
                "promoted_from": str(promotion.get("source_experiment", "")),
                "promoted_at": promotion.get("promoted_at"),
            }
        )

    OUTPUT_MANIFEST_PATH.write_text(
        json.dumps(
            vector_manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 80)
    print("MODULE 8 - VECTOR DATABASE")
    print("=" * 80)
    print("Provider          : FAISS")
    print("Index type        : IndexFlatIP")
    print(
        f"Vectors stored    : "
        f"{vector_manifest['vector_count']}"
    )
    print(
        f"Dimension         : "
        f"{vector_manifest['dimension']}"
    )
    print(
        f"Index file        : "
        f"{OUTPUT_INDEX_PATH}"
    )
    print(
        f"Metadata file     : "
        f"{OUTPUT_METADATA_PATH}"
    )
    print("Status            : SUCCESS")


if __name__ == "__main__":
    main()
