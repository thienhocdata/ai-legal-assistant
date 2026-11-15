from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AnswerQualityEvaluator:
    """Aggregate human review labels without pretending they are model judgments."""

    def evaluate(self, reviews: list[dict[str, Any]]) -> dict[str, Any]:
        if not reviews:
            raise ValueError("Bộ review câu trả lời rỗng.")
        reviewed = [row for row in reviews if row.get("review_status") == "reviewed"]
        if not reviewed:
            raise ValueError("Chưa có dòng nào được người đánh giá hoàn tất.")

        answered: list[dict[str, Any]] = []
        refused: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in reviewed:
            question_id = str(row.get("question_id", "")).strip()
            if not question_id or question_id in seen:
                raise ValueError("Review thiếu hoặc trùng question_id.")
            seen.add(question_id)
            behavior = row.get("expected_behavior")
            if behavior == "answer":
                self._require_booleans(
                    row,
                    ("citation_correct", "faithful", "complete"),
                )
                answered.append(row)
            elif behavior == "refuse":
                self._require_booleans(row, ("refusal_correct",))
                refused.append(row)
            else:
                raise ValueError(
                    f"expected_behavior không hợp lệ cho {question_id}: {behavior}"
                )

        return {
            "reviewed_count": len(reviewed),
            "pending_count": len(reviews) - len(reviewed),
            "answered_count": len(answered),
            "refused_count": len(refused),
            "citation_correct_rate": self._rate(answered, "citation_correct"),
            "faithfulness_rate": self._rate(answered, "faithful"),
            "answer_completeness_rate": self._rate(answered, "complete"),
            "refusal_correctness_rate": self._rate(refused, "refusal_correct"),
            "fully_correct_answer_rate": (
                round(
                    sum(
                        row["citation_correct"] and row["faithful"] and row["complete"]
                        for row in answered
                    )
                    / len(answered),
                    6,
                )
                if answered
                else None
            ),
        }

    @staticmethod
    def _require_booleans(row: dict[str, Any], names: tuple[str, ...]) -> None:
        for name in names:
            if not isinstance(row.get(name), bool):
                raise ValueError(
                    f"{row.get('question_id', '<unknown>')} cần nhãn boolean {name}."
                )

    @staticmethod
    def _rate(rows: list[dict[str, Any]], name: str) -> float | None:
        if not rows:
            return None
        return round(sum(bool(row[name]) for row in rows) / len(rows), 6)
