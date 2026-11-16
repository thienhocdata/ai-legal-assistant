from __future__ import annotations

from collections import Counter
from math import log
from typing import Any, Callable


def bm25_rrf_scores(
    question: str,
    candidates: list[tuple[float, float, float, dict[str, Any]]],
    tokenize: Callable[[str], set[str]],
    *,
    rrf_k: int = 60,
) -> dict[str, float]:
    """Experimental BM25 title+body / dense reciprocal rank fusion.

    Token presence is used (binary term frequency), so chunk repetition cannot
    earn a larger lexical score. This is an experiment, not a trained reranker.
    """
    if not candidates:
        return {}
    documents = {
        str(chunk["chunk_id"]): tokenize(
            str(chunk.get("article_title", "")) + " " + str(chunk.get("clean_text", ""))
        )
        for _, _, _, chunk in candidates
    }
    frequency = Counter(token for tokens in documents.values() for token in tokens)
    average_length = sum(map(len, documents.values())) / max(1, len(documents)) or 1
    query_tokens = tokenize(question)
    lexical: dict[str, float] = {}
    for chunk_id, tokens in documents.items():
        denominator = 1 + 1.2 * (1 - 0.75 + 0.75 * len(tokens) / average_length)
        lexical[chunk_id] = sum(
            log(1 + (len(documents) - frequency[token] + 0.5) / (frequency[token] + 0.5))
            * 2.2 / denominator
            for token in query_tokens.intersection(tokens)
        )
    dense_ids = [str(row[3]["chunk_id"]) for row in sorted(
        candidates, key=lambda row: (-row[1], str(row[3]["chunk_id"]))
    )]
    lexical_ids = sorted(lexical, key=lambda key: (-lexical[key], key))
    scores = {key: 1 / (rrf_k + rank) for rank, key in enumerate(dense_ids, 1)}
    for rank, key in enumerate(lexical_ids, 1):
        # A zero-overlap lexical list adds no evidence to the dense ranking.
        if lexical[key] > 0:
            scores[key] += 1 / (rrf_k + rank)
    return scores


def diverse_article_rows(
    ranked: list[tuple[float, float, float, dict[str, Any]]],
    top_k: int,
) -> list[tuple[float, float, float, dict[str, Any]]]:
    """Keep the best chunk per (document, article), preserving score order."""
    if top_k <= 0:
        raise ValueError("top_k must be positive.")
    selected = []
    seen: set[tuple[str, object]] = set()
    for row in ranked:
        chunk = row[3]
        article = chunk.get("article_no")
        key = (str(chunk.get("document_id", "")), article if article is not None else chunk["chunk_id"])
        if key in seen:
            continue
        seen.add(key)
        selected.append(row)
        if len(selected) >= top_k:
            break
    return selected
