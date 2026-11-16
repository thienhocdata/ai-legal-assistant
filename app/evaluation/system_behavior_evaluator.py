from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import sqrt
import re
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
CITATION_RE = re.compile(r"\[(\d+)\]")
METRIC_DESCRIPTIONS = {
    "answer_status_success_rate": (
        "On expected-answer rows, status == success; this does not score answer content."
    ),
    "article_hit_at_1_rate": (
        "On expected-answer rows, the first returned citation has any expected article."
    ),
    "article_hit_at_k_rate": (
        "On expected-answer rows, any returned citation has any expected article. "
        "k is the number of returned citations, not necessarily a constant."
    ),
    "article_mrr": (
        "Mean reciprocal first matching citation rank on expected-answer rows. "
        "Repeated articles retain their citation positions; misses contribute zero."
    ),
    "refusal_route_match_rate": (
        "On expected-refuse rows, returned status belongs to expected_statuses. "
        "If absent, the legacy broad non-answer status set is used and disclosed."
    ),
    "routing_and_top1_article_match_rate": (
        "Across all rows: expected-answer requires success AND expected article at "
        "citation rank 1; expected-refuse requires an accepted status. "
        "This is a routing/ranking proxy, not legal or answer accuracy."
    ),
    "answer_cited_article_hit_rate": (
        "On expected-answer rows, a valid [n] marker in the actual answer references "
        "any expected article. Marker matching does not establish semantic support, "
        "faithfulness, completeness, or legal correctness."
    ),
    "answer_cited_all_expected_articles_rate": (
        "On expected-answer rows, valid [n] markers reference every listed expected "
        "article. This is a syntactic all-label coverage check, not answer completeness; "
        "expected labels may be incomplete or include alternative acceptable articles."
    ),
}


def wilson95(numerator: int, denominator: int) -> dict[str, float] | None:
    """Wilson score interval for a binomial proportion; no interval for n=0."""
    if denominator < 0 or numerator < 0 or numerator > denominator:
        raise ValueError("Tử số/mẫu số không hợp lệ cho khoảng Wilson.")
    if denominator == 0:
        return None
    z = 1.959963984540054
    proportion = numerator / denominator
    adjustment = 1 + z * z / denominator
    center = (proportion + z * z / (2 * denominator)) / adjustment
    half_width = (
        z
        * sqrt(
            proportion * (1 - proportion) / denominator
            + z * z / (4 * denominator * denominator)
        )
        / adjustment
    )
    return {
        "lower": round(max(0.0, center - half_width), 6),
        "upper": round(min(1.0, center + half_width), 6),
    }


@dataclass(slots=True)
class SystemBehaviorEvaluator:
    assistant: AssistantProtocol

    def evaluate(self, questions: list[dict[str, Any]]) -> dict[str, Any]:
        self._validate_questions(questions)
        rows: list[dict[str, Any]] = []
        for item in questions:
            expected_behavior = item["expected_behavior"]
            result = self.assistant.answer(item["question"])
            status = str(result.get("status", "unknown"))
            citations = result.get("citations", [])
            if not isinstance(citations, list):
                raise ValueError("Assistant citations phải là list.")
            # Preserve citation positions, including repeated articles. Deduplicating
            # would change MRR when several chunks from the same article rank first.
            retrieved_articles = [
                int(citation["article_no"])
                if citation.get("article_no") is not None
                else None
                for citation in citations
            ]
            expected_articles = set(item.get("expected_article_numbers", []))
            matching_ranks = [
                rank
                for rank, article_no in enumerate(retrieved_articles, start=1)
                if article_no in expected_articles
            ]
            hit_at_1 = bool(matching_ranks and matching_ranks[0] == 1)
            reciprocal_rank = 1 / matching_ranks[0] if matching_ranks else 0.0
            answer_status_success = status == "success"
            default_refusal_set = "expected_statuses" not in item
            expected_statuses = (
                sorted(item.get("expected_statuses", REFUSAL_STATUSES))
                if expected_behavior == "refuse"
                else ["success"]
            )
            refusal_route_match = (
                status in expected_statuses if expected_behavior == "refuse" else None
            )
            marker_labels = {
                int(label) for label in CITATION_RE.findall(str(result.get("answer", "")))
            }
            valid_labels = {label for label in marker_labels if 1 <= label <= len(citations)}
            answer_cited_articles = sorted(
                {
                    retrieved_articles[label - 1]
                    for label in valid_labels
                    if retrieved_articles[label - 1] is not None
                }
            )
            routing_and_top1_match = (
                answer_status_success and hit_at_1
                if expected_behavior == "answer"
                else bool(refusal_route_match)
            )
            rows.append(
                {
                    "question_id": item["question_id"],
                    "question_type": item.get("question_type", "unspecified"),
                    "expected_behavior": expected_behavior,
                    "status": status,
                    "expected_statuses": expected_statuses,
                    "uses_legacy_broad_refusal_status_set": (
                        expected_behavior == "refuse" and default_refusal_set
                    ),
                    "expected_articles": sorted(expected_articles),
                    "retrieved_articles": retrieved_articles,
                    "retrieved_chunk_ids": [citation.get("chunk_id") for citation in citations],
                    "citation_scores": [citation.get("score") for citation in citations],
                    "retrieval_diagnostics": result.get("retrieval", {}),
                    "missing_source_types": result.get("analysis", {}).get("missing_source_types", []),
                    "missing_context_types": result.get("analysis", {}).get("missing_context_types", []),
                    "article_hit_at_1": hit_at_1,
                    "article_hit_at_k": bool(matching_ranks),
                    "article_reciprocal_rank": round(reciprocal_rank, 12),
                    "answer_status_success": answer_status_success,
                    "refusal_route_match": refusal_route_match,
                    "routing_and_top1_match": routing_and_top1_match,
                    "answer_citation_labels": sorted(valid_labels),
                    "invalid_answer_citation_labels": sorted(marker_labels - valid_labels),
                    "answer_cited_articles": answer_cited_articles,
                    "answer_cited_article_hit": bool(
                        expected_articles.intersection(answer_cited_articles)
                    ),
                    "answer_cited_all_expected_articles": bool(expected_articles)
                    and expected_articles.issubset(answer_cited_articles),
                    "citation_count": len(citations),
                    "provider": result.get("provider"),
                    "latency_ms": result.get("latency_ms"),
                }
            )

        return {
            "schema_version": "2.0",
            "metric_descriptions": METRIC_DESCRIPTIONS,
            "interval_interpretation": (
                "Wilson 95% intervals describe binomial sampling uncertainty only. "
                "They do not account for AI-label errors, dependent questions, dataset "
                "selection bias, or legal validity. No binomial interval is assigned to MRR."
            ),
            **self._summarize(rows),
            "cohorts": {
                cohort: self._summarize(
                    [row for row in rows if row["question_type"] == cohort]
                )
                for cohort in sorted({row["question_type"] for row in rows})
            },
            "rows": rows,
        }

    @staticmethod
    def _validate_questions(questions: Any) -> None:
        if not isinstance(questions, list) or not questions:
            raise ValueError("Bộ câu hỏi đánh giá rỗng hoặc không phải list.")
        seen: set[str] = set()
        for item in questions:
            if not isinstance(item, dict):
                raise ValueError("Mỗi câu hỏi phải là object.")
            question_id = item.get("question_id")
            question = item.get("question")
            if (
                not isinstance(question_id, str)
                or not question_id.strip()
                or question_id in seen
                or not isinstance(question, str)
                or not question.strip()
            ):
                raise ValueError("Question ID/text thiếu hoặc bị trùng.")
            seen.add(question_id)
            behavior = item.get("expected_behavior")
            if behavior not in {"answer", "refuse"}:
                raise ValueError(f"expected_behavior không hợp lệ: {behavior}")
            articles = item.get("expected_article_numbers", [])
            if not isinstance(articles, list) or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 1
                for value in articles
            ):
                raise ValueError("expected_article_numbers phải là list số Điều dương.")
            if behavior == "answer" and not articles:
                raise ValueError("Câu expected answer phải có nhãn Điều.")
            statuses = item.get("expected_statuses")
            if "expected_statuses" in item and (
                behavior != "refuse"
                or not isinstance(statuses, list)
                or not statuses
                or any(
                    not isinstance(status, str) or status not in REFUSAL_STATUSES
                    for status in statuses
                )
            ):
                raise ValueError("expected_statuses chỉ nhận các refusal status đã biết.")
            if not isinstance(item.get("question_type", "unspecified"), str):
                raise ValueError("question_type phải là string.")

    @staticmethod
    def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
        answer_rows = [row for row in rows if row["expected_behavior"] == "answer"]
        refusal_rows = [row for row in rows if row["expected_behavior"] == "refuse"]
        metric_inputs = {
            "answer_status_success_rate": (answer_rows, "answer_status_success"),
            "article_hit_at_1_rate": (answer_rows, "article_hit_at_1"),
            "article_hit_at_k_rate": (answer_rows, "article_hit_at_k"),
            "answer_cited_article_hit_rate": (answer_rows, "answer_cited_article_hit"),
            "answer_cited_all_expected_articles_rate": (
                answer_rows, "answer_cited_all_expected_articles"
            ),
            "refusal_route_match_rate": (refusal_rows, "refusal_route_match"),
            "routing_and_top1_article_match_rate": (rows, "routing_and_top1_match"),
        }
        details = {}
        for name, (metric_rows, field) in metric_inputs.items():
            numerator = sum(bool(row[field]) for row in metric_rows)
            denominator = len(metric_rows)
            details[name] = {
                "numerator": numerator,
                "denominator": denominator,
                "value": round(numerator / denominator, 6) if denominator else None,
                "wilson95": wilson95(numerator, denominator),
            }
        return {
            "question_count": len(rows),
            "answerable_count": len(answer_rows),
            "refusal_count": len(refusal_rows),
            **{name: detail["value"] for name, detail in details.items()},
            "article_mrr": (
                round(
                    sum(row["article_reciprocal_rank"] for row in answer_rows)
                    / len(answer_rows),
                    6,
                )
                if answer_rows
                else None
            ),
            "metric_details": details,
            "status_counts": dict(sorted(Counter(row["status"] for row in rows).items())),
            "refusal_status_counts": dict(
                sorted(Counter(row["status"] for row in refusal_rows).items())
            ),
            "legacy_broad_refusal_label_count": sum(
                row["uses_legacy_broad_refusal_status_set"] for row in rows
            ),
        }
