from app.rag.ranking import bm25_rrf_scores, diverse_article_rows
from app.rag.retriever import LegalRetriever
import numpy as np
import pytest


def _row(chunk_id, doc, article, score, text):
    return (score, score, 0, {
        "chunk_id": chunk_id, "document_id": doc, "article_no": article,
        "article_title": text, "clean_text": text,
    })


def test_article_diversity_preserves_best_chunk_and_document_identity():
    rows = [_row("a", "law1", 45, .99, "a"), _row("b", "law1", 45, .98, "b"),
            _row("c", "law1", 133, .97, "c"), _row("d", "law2", 45, .96, "d")]
    selected = diverse_article_rows(rows, 3)
    assert [row[3]["chunk_id"] for row in selected] == ["a", "c", "d"]


def test_rrf_uses_overlap_and_is_deterministic():
    rows = [_row("a", "doc", 1, .9, "đất chung"), _row("b", "doc", 2, .8, "đất bồi thường")]
    scores = bm25_rrf_scores("bồi thường", rows, lambda text: set(text.split()))
    assert scores["b"] > scores["a"]
    assert scores == bm25_rrf_scores("bồi thường", rows, lambda text: set(text.split()))


def test_default_retrieval_preserves_multiple_chunks_within_requested_article():
    class _Embedder:
        def encode_queries(self, questions, *, batch_size):
            return np.zeros((1, 2), dtype=np.float32)

    class _Store:
        metadata = [1, 2, 3]

        def search(self, vector, *, top_k):
            return [{"chunk_id": key, "score": score}
                    for key, score in (("intro", .99), ("conditions", .98), ("other", .9))]

    retriever = LegalRetriever(index_path="unused", vector_metadata_path="unused",
                               embedding_manifest_path="unused", chunks_path="unused")
    retriever._loaded = True
    retriever._embedder = _Embedder()
    retriever._store = _Store()
    retriever._chunks_by_id = {
        key: _row(key, "doc", article, 0, text)[3]
        for key, article, text in (("intro", 138, "Giới thiệu"),
                                   ("conditions", 138, "Điều kiện cụ thể"),
                                   ("other", 152, "Khác"))
    }
    matches = retriever.retrieve_hybrid("Điều 138", top_k=3, lexical_weight=0)
    assert [row["chunk_id"] for row in matches] == ["intro", "conditions", "other"]
    diverse = retriever.retrieve_hybrid("Điều 138", top_k=3, lexical_weight=0, diversify_articles=True)
    assert [row["chunk_id"] for row in diverse] == ["intro", "other"]
    with pytest.raises(ValueError):
        diverse_article_rows([], 0)
