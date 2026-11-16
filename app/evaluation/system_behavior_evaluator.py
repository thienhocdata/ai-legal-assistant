from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class AssistantProtocol(Protocol):
    def answer(self, question: str) -> dict[str, Any]: ...


REFUSAL_STATUSES = {
    "blocked",
    "generation_rejected",
    "insufficient_coverage",
    "insufficient_evidence",
    "needs_clarification",
    "out_of_scope",
}


@dataclass(slots=True)
class SystemBehaviorEvaluator:
    assistant: AssistantProtocol

    def evaluate(self, questions: list[dict[str, Any]]) -> dict[str, Any]:
        if not questions:
            raise ValueError("Bộ câu hỏi đánh giá rỗng.")
        rows: list[dict[str, Any]] = []
        answerable_count = 0
        answer_success_count = 0
        article_hit_at_1_count = 0
        article_hit_at_k_count = 0
        reciprocal_rank_total = 0.0
        refusal_count = 0
        correct_refusal_count = 0
        seen: set[str] = set()

        for item in questions:
            question_id = str(item.get("question_id", "")).strip()
            question = str(item.get("question", "")).strip()
            behavior = str(item.get("expected_behavior", "")).strip()
            if not question_id or not question or question_id in seen:
                raise ValueError("Question ID/text thiếu hoặc bị trùng.")
            seen.add(question_id)
            if behavior not in {"answer", "refuse"}:
                raise ValueError(f"expected_behavior không hợp lệ: {behavior}")

            result = self.assistant.answer(question)
            status = str(result.get("status", "unknown"))
            retrieved_articles: list[int] = []
            for citation in result.get("citations", []):
                if citation.get("article_no") is None:
                    continue
                article_no = int(citation["article_no"])
                if article_no not in retrieved_articles:
                    retrieved_articles.append(article_no)
            expected_articles = {
                int(value) for value in item.get("expected_article_numbers", [])
            }
            article_hit_at_1 = bool(
                retrieved_articles and retrieved_articles[0] in expected_articles
            )
            matching_ranks = [
                rank
                for rank, article_no in enumerate(retrieved_articles, start=1)
                if article_no in expected_articles
            ]
            reciprocal_rank = 1 / matching_ranks[0] if matching_ranks else 0.0
            article_hit_at_k = bool(matching_ranks)
            if behavior == "answer":
                answerable_count += 1
                answer_success = status == "success"
                answer_success_count += int(answer_success)
                article_hit_at_1_count += int(article_hit_at_1)
                article_hit_at_k_count += int(article_hit_at_k)
                reciprocal_rank_total += reciprocal_rank
                # ExtractiveProvider answers only from evidence block [1], so the
                # grounded behavior metric must require the expected article at rank 1.
                behavior_correct = answer_success and article_hit_at_1
            else:
                refusal_count += 1
                behavior_correct = status in REFUSAL_STATUSES
                correct_refusal_count += int(behavior_correct)

            rows.append(
                {
                    "question_id": question_id,
                    "expected_behavior": behavior,
                    "status": status,
                    "expected_articles": sorted(expected_articles),
                    "retrieved_articles": retrieved_articles,
                    "article_hit_at_1": article_hit_at_1,
                    "article_hit_at_k": article_hit_at_k,
                    "article_reciprocal_rank": round(reciprocal_rank, 6),
                    "behavior_correct": behavior_correct,
                    "citation_count": len(result.get("citations", [])),
                    "provider": result.get("provider"),
                    "latency_ms": result.get("latency_ms"),
                }
            )

        return {
            "question_count": len(questions),
            "answerable_count": answerable_count,
            "refusal_count": refusal_count,
            "answer_success_rate": self._rate(answer_success_count, answerable_count),
            "article_hit_at_1_rate": self._rate(
                article_hit_at_1_count, answerable_count
            ),
            "article_hit_at_k_rate": self._rate(
                article_hit_at_k_count, answerable_count
            ),
            "article_mrr": (
                round(reciprocal_rank_total / answerable_count, 6)
                if answerable_count
                else None
            ),
            "refusal_correctness_rate": self._rate(
                correct_refusal_count, refusal_count
            ),
            "overall_grounded_behavior_accuracy": round(
                sum(row["behavior_correct"] for row in rows) / len(rows), 6
            ),
            "rows": rows,
        }

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float | None:
        return round(numerator / denominator, 6) if denominator else None
