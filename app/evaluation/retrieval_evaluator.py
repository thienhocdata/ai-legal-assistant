from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class RetrieverProtocol(Protocol):
    def retrieve(self, question: str, *, top_k: int = 5) -> list[dict[str, Any]]: ...


@dataclass(slots=True)
class RetrievalEvaluator:
    retriever: RetrieverProtocol
    top_k: int = 5

    def evaluate(self, questions: list[dict[str, Any]]) -> dict[str, Any]:
        if not questions:
            raise ValueError("Bộ câu hỏi đánh giá rỗng.")
        if self.top_k <= 0:
            raise ValueError("top_k phải lớn hơn 0.")

        rows: list[dict[str, Any]] = []
        reciprocal_rank_sum = 0.0
        hit_at_1 = 0
        hit_at_3 = 0
        hit_at_5 = 0

        for question in questions:
            expected = {int(value) for value in question["expected_article_numbers"]}
            results = self.retriever.retrieve(question["question"], top_k=self.top_k)
            retrieved = [int(item["article_no"]) for item in results]
            first_relevant_rank = next(
                (rank for rank, article in enumerate(retrieved, start=1) if article in expected),
                None,
            )
            if first_relevant_rank is not None:
                reciprocal_rank_sum += 1.0 / first_relevant_rank
            hit_at_1 += int(bool(expected.intersection(retrieved[:1])))
            hit_at_3 += int(bool(expected.intersection(retrieved[:3])))
            hit_at_5 += int(bool(expected.intersection(retrieved[:5])))

            rows.append(
                {
                    "question_id": question["question_id"],
                    "question": question["question"],
                    "expected_articles": sorted(expected),
                    "retrieved_articles": retrieved,
                    "retrieved_chunk_ids": [item["chunk_id"] for item in results],
                    "scores": [round(float(item["score"]), 6) for item in results],
                    "first_relevant_rank": first_relevant_rank,
                }
            )

        count = len(questions)
        return {
            "question_count": count,
            "top_k": self.top_k,
            "hit_at_1": hit_at_1 / count,
            "recall_at_3": hit_at_3 / count,
            "recall_at_5": hit_at_5 / count,
            "mrr": reciprocal_rank_sum / count,
            "results": rows,
        }
