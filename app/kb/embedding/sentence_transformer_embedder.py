from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from .base import BaseEmbedder


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Embedder dùng sentence-transformers.

    Mặc định dùng multilingual-e5-small:
    - văn bản pháp luật: prefix "passage: "
    - câu hỏi người dùng: prefix "query: "
    """

    def __init__(
        self,
        *,
        model_name: str = "intfloat/multilingual-e5-small",
        device: str = "cpu",
        normalize_embeddings: bool = True,
        document_prefix: str = "passage: ",
        query_prefix: str = "query: ",
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "Chưa cài sentence-transformers. "
                "Chạy: pip install -r requirements_module7.txt"
            ) from exc

        self._model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self.document_prefix = document_prefix
        self.query_prefix = query_prefix

        self._model: Any = SentenceTransformer(
            model_name,
            device=device,
        )

        get_dimension = getattr(
            self._model,
            "get_embedding_dimension",
            self._model.get_sentence_embedding_dimension,
        )
        dimension = get_dimension()
        if not dimension:
            raise ValueError(
                "Không xác định được embedding dimension."
            )

        self._dimension = int(dimension)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @staticmethod
    def _validate_texts(
        texts: Sequence[str],
    ) -> list[str]:
        if not texts:
            raise ValueError("Danh sách text rỗng.")

        cleaned = []

        for index, text in enumerate(texts):
            value = str(text).strip()
            if not value:
                raise ValueError(
                    f"Text tại vị trí {index} bị rỗng."
                )
            cleaned.append(value)

        return cleaned

    def _encode(
        self,
        texts: Sequence[str],
        *,
        prefix: str,
        batch_size: int,
    ) -> np.ndarray:
        if batch_size <= 0:
            raise ValueError("batch_size phải lớn hơn 0.")

        cleaned = self._validate_texts(texts)
        prepared = [
            f"{prefix}{text}"
            for text in cleaned
        ]

        vectors = self._model.encode(
            prepared,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings,
        )

        array = np.asarray(
            vectors,
            dtype=np.float32,
        )

        if array.ndim != 2:
            raise ValueError(
                "Embedding output phải là ma trận 2 chiều."
            )

        if array.shape[0] != len(cleaned):
            raise ValueError(
                "Số vector không khớp số văn bản."
            )

        if array.shape[1] != self.dimension:
            raise ValueError(
                "Embedding dimension không nhất quán."
            )

        if not np.isfinite(array).all():
            raise ValueError(
                "Embedding chứa NaN hoặc Infinity."
            )

        return array

    def encode_documents(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 32,
    ) -> np.ndarray:
        return self._encode(
            texts,
            prefix=self.document_prefix,
            batch_size=batch_size,
        )

    def encode_queries(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 32,
    ) -> np.ndarray:
        return self._encode(
            texts,
            prefix=self.query_prefix,
            batch_size=batch_size,
        )
