from __future__ import annotations

from pathlib import Path
import json
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.vector_store import FaissVectorStore


INDEX_PATH = (
    ROOT
    / "data"
    / "vector_db"
    / "legal_chunks.faiss"
)

METADATA_PATH = (
    ROOT
    / "data"
    / "vector_db"
    / "legal_chunks_metadata.json"
)

MANIFEST_PATH = (
    ROOT
    / "data"
    / "vector_db"
    / "vector_store_manifest.json"
)


def main() -> None:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy index: {INDEX_PATH}"
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy metadata: {METADATA_PATH}"
        )

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy manifest: {MANIFEST_PATH}"
        )

    manifest = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    store = FaissVectorStore()
    store.load(
        INDEX_PATH,
        METADATA_PATH,
    )

    if int(store.index.ntotal) != int(
        manifest["vector_count"]
    ):
        raise ValueError(
            "Số vector trong index không khớp manifest."
        )

    if store.dimension != int(
        manifest["dimension"]
    ):
        raise ValueError(
            "Dimension không khớp manifest."
        )

    test_query = np.zeros(
        store.dimension,
        dtype=np.float32,
    )
    test_query[0] = 1.0

    results = store.search(
        test_query,
        top_k=3,
    )

    if len(results) != 3:
        raise ValueError(
            "FAISS search không trả đủ 3 kết quả."
        )

    print("=" * 80)
    print("MODULE 8 - VECTOR DATABASE VALIDATION")
    print("=" * 80)
    print(
        f"Vectors           : "
        f"{store.index.ntotal}"
    )
    print(
        f"Dimension         : "
        f"{store.dimension}"
    )
    print(
        f"Search results    : "
        f"{len(results)}"
    )
    print("Status            : SUCCESS")


if __name__ == "__main__":
    main()
