from __future__ import annotations

from pathlib import Path
from hashlib import sha256
import json
import re
import unicodedata
from typing import Any

from app.kb.embedding import SentenceTransformerEmbedder
from app.rag.vector_store import FaissVectorStore


class LegalRetriever:
    """
    Retriever cho hệ thống hỏi đáp pháp luật đất đai.

    Luồng:
    câu hỏi -> query embedding -> FAISS search -> lấy metadata + nội dung chunk.
    """

    def __init__(
        self,
        *,
        index_path: str | Path,
        vector_metadata_path: str | Path,
        embedding_manifest_path: str | Path,
        chunks_path: str | Path,
        device: str = "cpu",
    ) -> None:
        self.index_path = Path(index_path)
        self.vector_metadata_path = Path(
            vector_metadata_path
        )
        self.embedding_manifest_path = Path(
            embedding_manifest_path
        )
        self.chunks_path = Path(chunks_path)
        self.device = device

        self._store = FaissVectorStore()
        self._embedder: SentenceTransformerEmbedder | None = None
        self._chunks_by_id: dict[str, dict[str, Any]] = {}
        self._loaded = False

    @staticmethod
    def _load_json(
        path: Path,
    ) -> Any:
        if not path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy file: {path}"
            )

        return json.loads(
            path.read_text(encoding="utf-8")
        )

    def load(self) -> None:
        embedding_manifest = self._load_json(
            self.embedding_manifest_path
        )

        if not isinstance(
            embedding_manifest,
            dict,
        ):
            raise ValueError(
                "Embedding manifest phải là JSON object."
            )

        chunks = self._load_json(
            self.chunks_path
        )

        if not isinstance(chunks, list):
            raise ValueError(
                "legal_chunks.json phải là JSON array."
            )

        chunks_by_id: dict[
            str,
            dict[str, Any]
        ] = {}

        for index, chunk in enumerate(chunks):
            chunk_id = str(
                chunk.get("chunk_id", "")
            ).strip()

            if not chunk_id:
                raise ValueError(
                    f"Chunk tại vị trí {index} thiếu chunk_id."
                )

            if chunk_id in chunks_by_id:
                raise ValueError(
                    f"Trùng chunk_id: {chunk_id}"
                )

            chunks_by_id[chunk_id] = dict(
                chunk
            )

        expected_source_hash = str(
            embedding_manifest.get("source_chunks_sha256", "")
        ).strip()
        if expected_source_hash:
            digest = sha256()
            text_field = str(embedding_manifest.get("text_field", "clean_text"))
            for chunk in chunks:
                digest.update(str(chunk.get("chunk_id", "")).encode("utf-8"))
                digest.update(b"\0")
                digest.update(str(chunk.get(text_field, "")).encode("utf-8"))
                digest.update(b"\n")
            if digest.hexdigest() != expected_source_hash:
                raise ValueError(
                    "legal_chunks.json không khớp phiên bản đã dùng để tạo embedding."
                )

        self._store.load(
            self.index_path,
            self.vector_metadata_path,
        )

        if self._store.dimension != int(
            embedding_manifest[
                "embedding_dimension"
            ]
        ):
            raise ValueError(
                "Dimension FAISS không khớp embedding manifest."
            )

        self._embedder = SentenceTransformerEmbedder(
            model_name=str(
                embedding_manifest[
                    "model_name"
                ]
            ),
            device=self.device,
            normalize_embeddings=bool(
                embedding_manifest[
                    "normalize_embeddings"
                ]
            ),
            document_prefix=str(
                embedding_manifest[
                    "document_prefix"
                ]
            ),
            query_prefix=str(
                embedding_manifest[
                    "query_prefix"
                ]
            ),
        )

        if (
            self._embedder.dimension
            != self._store.dimension
        ):
            raise ValueError(
                "Embedding model dimension không khớp FAISS index."
            )

        self._chunks_by_id = chunks_by_id
        self._loaded = True

    @staticmethod
    def _validate_question(
        question: str,
    ) -> str:
        value = str(question).strip()

        if not value:
            raise ValueError(
                "Câu hỏi không được để trống."
            )

        if len(value) < 3:
            raise ValueError(
                "Câu hỏi quá ngắn."
            )

        return value

    def retrieve(
        self,
        question: str,
        *,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        if not self._loaded:
            self.load()

        if self._embedder is None:
            raise RuntimeError(
                "Embedder chưa được khởi tạo."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k phải lớn hơn 0."
            )

        question = self._validate_question(
            question
        )

        query_vector = self._embedder.encode_queries(
            [question],
            batch_size=1,
        )[0]

        vector_results = self._store.search(
            query_vector,
            top_k=top_k,
        )

        results: list[dict[str, Any]] = []

        for item in vector_results:
            chunk_id = str(
                item["chunk_id"]
            )

            chunk = self._chunks_by_id.get(
                chunk_id
            )

            if chunk is None:
                raise ValueError(
                    "Không tìm thấy nội dung chunk cho "
                    f"{chunk_id}"
                )

            results.append(
                {
                    "rank": int(item["rank"]),
                    "score": float(item["score"]),
                    "chunk_id": chunk_id,
                    "document_id": chunk.get(
                        "document_id"
                    ),
                    "document_name": chunk.get(
                        "document_name"
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
                    "article_no": chunk.get(
                        "article_no"
                    ),
                    "article_title": chunk.get(
                        "article_title"
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
                    "text": chunk.get(
                        "text",
                        "",
                    ),
                    "clean_text": chunk.get(
                        "clean_text",
                        "",
                    ),
                }
            )

        return results

    def retrieve_context(
        self,
        question: str,
        *,
        top_k: int = 5,
    ) -> str:
        results = self.retrieve(
            question,
            top_k=top_k,
        )

        blocks: list[str] = []

        for result in results:
            heading = (
                f"[Kết quả {result['rank']} | "
                f"Điều {result['article_no']} | "
                f"score={result['score']:.4f}]"
            )

            blocks.append(
                f"{heading}\n{result['text']}"
            )

        return "\n\n".join(blocks)

    _TOKEN_RE = re.compile(r"[0-9a-zA-ZÀ-ỹĐđ]+", re.UNICODE)
    _STOPWORDS = {
        "là", "gì", "những", "các", "nào", "như", "thế", "và", "của",
        "có", "không", "được", "theo", "quy", "định", "về", "cho",
    }
    _LEGAL_PHRASES = (
        "chuyển nhượng", "chuyển đổi", "tặng cho", "thừa kế", "cho thuê đất",
        "thu hồi đất", "bồi thường", "tái định cư", "giao đất không thu tiền",
        "giao đất có thu tiền", "chuyển mục đích", "đăng ký lần đầu",
        "đăng ký biến động", "giấy chứng nhận", "bảng giá đất", "giá đất",
        "tách thửa", "hợp thửa", "hòa giải", "tranh chấp đất đai", "thẩm quyền",
        "điều kiện được bồi thường về đất", "điều kiện để được bồi thường về đất",
        "đất không có giấy tờ",
    )
    _LEGAL_PHRASE_ALIASES = (
        ("điều chỉnh những vấn đề", "phạm vi điều chỉnh"),
        ("điều kiện để được bồi thường về đất", "điều kiện được bồi thường về đất"),
    )

    @classmethod
    def _tokens(cls, value: str) -> set[str]:
        normalized = unicodedata.normalize("NFC", str(value)).lower()
        return {
            token
            for token in cls._TOKEN_RE.findall(normalized)
            if len(token) > 1 and token not in cls._STOPWORDS
        }

    @classmethod
    def _lexical_score(cls, question: str, chunk: dict[str, Any]) -> float:
        query_tokens = cls._tokens(question)
        if not query_tokens:
            return 0.0
        title_tokens = cls._tokens(str(chunk.get("article_title", "")))
        text_tokens = cls._tokens(str(chunk.get("clean_text", "")))
        title_overlap = query_tokens.intersection(title_tokens)
        text_overlap = query_tokens.intersection(text_tokens)
        title_coverage = len(title_overlap) / max(1, len(title_tokens))
        query_title_coverage = len(title_overlap) / len(query_tokens)
        text_coverage = len(text_overlap) / len(query_tokens)
        question_lower = unicodedata.normalize("NFC", question).lower()
        title_lower = unicodedata.normalize(
            "NFC", str(chunk.get("article_title", ""))
        ).lower()
        query_phrases = [
            phrase for phrase in cls._LEGAL_PHRASES if phrase in question_lower
        ]
        query_phrases.extend(
            target
            for source, target in cls._LEGAL_PHRASE_ALIASES
            if source in question_lower
        )
        phrase_score = (
            sum(phrase in title_lower for phrase in query_phrases) / len(query_phrases)
            if query_phrases
            else 0.0
        )
        return min(
            1.0,
            0.35 * title_coverage
            + 0.15 * query_title_coverage
            + 0.10 * text_coverage
            + 0.40 * phrase_score,
        )

    def retrieve_hybrid(
        self,
        question: str,
        *,
        top_k: int = 5,
        lexical_weight: float = 0.35,
    ) -> list[dict[str, Any]]:
        """Dense retrieval with a deterministic legal-title lexical boost."""
        if not 0.0 <= lexical_weight <= 1.0:
            raise ValueError("lexical_weight phải nằm trong [0, 1].")
        if not self._loaded:
            self.load()
        if self._embedder is None:
            raise RuntimeError("Embedder chưa được khởi tạo.")

        question = self._validate_question(question)
        query_vector = self._embedder.encode_queries([question], batch_size=1)[0]
        dense_results = self._store.search(
            query_vector,
            top_k=len(self._store.metadata),
        )

        ranked: list[tuple[float, float, float, dict[str, Any]]] = []
        for item in dense_results:
            chunk = self._chunks_by_id[str(item["chunk_id"])]
            dense_score = float(item["score"])
            lexical_score = self._lexical_score(question, chunk)
            combined_score = dense_score + lexical_weight * lexical_score
            ranked.append((combined_score, dense_score, lexical_score, chunk))

        ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
        results: list[dict[str, Any]] = []
        for rank, (score, dense_score, lexical_score, chunk) in enumerate(
            ranked[:top_k], start=1
        ):
            results.append(
                {
                    "rank": rank,
                    "score": score,
                    "dense_score": dense_score,
                    "lexical_score": lexical_score,
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk.get("document_id"),
                    "document_name": chunk.get("document_name"),
                    "chapter_no": chunk.get("chapter_no"),
                    "chapter_title": chunk.get("chapter_title"),
                    "section_no": chunk.get("section_no"),
                    "section_title": chunk.get("section_title"),
                    "article_no": chunk.get("article_no"),
                    "article_title": chunk.get("article_title"),
                    "clause_nos": chunk.get("clause_nos", []),
                    "point_nos": chunk.get("point_nos", []),
                    "strategy": chunk.get("strategy"),
                    "text": chunk.get("text", ""),
                    "clean_text": chunk.get("clean_text", ""),
                }
            )
        return results
