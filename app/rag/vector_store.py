from __future__ import annotations

from pathlib import Path
import json
from typing import Any

import numpy as np


class FaissVectorStore:
    """
    FAISS local vector store.

    - Dùng IndexFlatIP.
    - Embedding đã chuẩn hóa L2 nên inner product tương đương cosine similarity.
    - Ghi/đọc bằng serialize_index và deserialize_index để tránh lỗi đường dẫn
      Windows có ký tự tiếng Việt.
    """

    def __init__(self) -> None:
        self.index: Any | None = None
        self.metadata: list[dict[str, Any]] = []
        self.dimension: int | None = None

    @staticmethod
    def _import_faiss() -> Any:
        try:
            import faiss
        except ImportError as exc:
            raise ImportError(
                "Chưa cài faiss-cpu. Chạy: pip install faiss-cpu"
            ) from exc
        return faiss

    @staticmethod
    def _validate_embeddings(
        embeddings: np.ndarray,
    ) -> np.ndarray:
        array = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        if array.ndim != 2:
            raise ValueError(
                "Embeddings phải là ma trận 2 chiều."
            )

        if array.shape[0] == 0:
            raise ValueError(
                "Embeddings không có vector."
            )

        if not np.isfinite(array).all():
            raise ValueError(
                "Embeddings chứa NaN hoặc Infinity."
            )

        norms = np.linalg.norm(
            array,
            axis=1,
        )

        if not np.allclose(
            norms,
            1.0,
            atol=1e-3,
        ):
            raise ValueError(
                "Embeddings chưa được chuẩn hóa L2."
            )

        return np.ascontiguousarray(
            array,
            dtype=np.float32,
        )

    @staticmethod
    def _validate_metadata(
        metadata: list[dict[str, Any]],
        expected_count: int,
    ) -> list[dict[str, Any]]:
        if len(metadata) != expected_count:
            raise ValueError(
                "Số metadata không khớp số vector."
            )

        chunk_ids: list[str] = []

        for expected_index, row in enumerate(metadata):
            vector_index = row.get("vector_index")
            chunk_id = str(
                row.get("chunk_id", "")
            ).strip()

            if vector_index != expected_index:
                raise ValueError(
                    "vector_index phải liên tục từ 0."
                )

            if not chunk_id:
                raise ValueError(
                    f"Metadata dòng {expected_index} thiếu chunk_id."
                )

            chunk_ids.append(chunk_id)

        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError(
                "Metadata có chunk_id bị trùng."
            )

        return [dict(row) for row in metadata]

    def build(
        self,
        embeddings: np.ndarray,
        metadata: list[dict[str, Any]],
    ) -> None:
        faiss = self._import_faiss()
        vectors = self._validate_embeddings(
            embeddings
        )
        rows = self._validate_metadata(
            metadata,
            vectors.shape[0],
        )

        dimension = int(vectors.shape[1])
        index = faiss.IndexFlatIP(dimension)
        index.add(vectors)

        if int(index.ntotal) != vectors.shape[0]:
            raise ValueError(
                "FAISS không lưu đủ vector."
            )

        self.index = index
        self.metadata = rows
        self.dimension = dimension

    def save(
        self,
        index_path: str | Path,
        metadata_path: str | Path,
    ) -> None:
        if self.index is None:
            raise ValueError(
                "Chưa có FAISS index để lưu."
            )

        if len(self.metadata) != int(
            self.index.ntotal
        ):
            raise ValueError(
                "Metadata không khớp số vector."
            )

        faiss = self._import_faiss()

        index_path = Path(index_path)
        metadata_path = Path(metadata_path)

        index_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        metadata_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        serialized = faiss.serialize_index(
            self.index
        )

        index_path.write_bytes(
            serialized.tobytes()
        )

        metadata_path.write_text(
            json.dumps(
                self.metadata,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(
        self,
        index_path: str | Path,
        metadata_path: str | Path,
    ) -> None:
        faiss = self._import_faiss()

        index_path = Path(index_path)
        metadata_path = Path(metadata_path)

        if not index_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy index: {index_path}"
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy metadata: {metadata_path}"
            )

        index_bytes = index_path.read_bytes()
        serialized = np.frombuffer(
            index_bytes,
            dtype=np.uint8,
        )

        index = faiss.deserialize_index(
            serialized
        )

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(metadata, list):
            raise ValueError(
                "Metadata phải là JSON array."
            )

        rows = self._validate_metadata(
            metadata,
            int(index.ntotal),
        )

        self.index = index
        self.metadata = rows
        self.dimension = int(index.d)

    def search(
        self,
        query_vector: np.ndarray,
        *,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        if self.index is None:
            raise ValueError(
                "Vector store chưa được build hoặc load."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k phải lớn hơn 0."
            )

        query = np.asarray(
            query_vector,
            dtype=np.float32,
        )

        if query.ndim == 1:
            query = query.reshape(1, -1)

        if (
            query.ndim != 2
            or query.shape[0] != 1
        ):
            raise ValueError(
                "query_vector phải là một vector."
            )

        if query.shape[1] != self.dimension:
            raise ValueError(
                "Query dimension không khớp index."
            )

        norm = float(
            np.linalg.norm(query[0])
        )

        if norm == 0.0:
            raise ValueError(
                "Query vector không được bằng 0."
            )

        query = np.ascontiguousarray(
            query / norm,
            dtype=np.float32,
        )

        result_count = min(
            top_k,
            int(self.index.ntotal),
        )

        scores, indexes = self.index.search(
            query,
            result_count,
        )

        results: list[dict[str, Any]] = []

        for rank, (
            score,
            vector_index,
        ) in enumerate(
            zip(
                scores[0],
                indexes[0],
                strict=True,
            ),
            start=1,
        ):
            vector_index = int(vector_index)

            if vector_index < 0:
                continue

            row = dict(
                self.metadata[vector_index]
            )

            results.append(
                {
                    "rank": rank,
                    "score": float(score),
                    "vector_index": vector_index,
                    "chunk_id": row["chunk_id"],
                    "metadata": row,
                }
            )

        return results
