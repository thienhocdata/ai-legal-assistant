from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation import AnswerQualityEvaluator


def test_answer_quality_metrics_separate_answers_and_refusals() -> None:
    reviews = [
        {
            "question_id": "A1",
            "review_status": "reviewed",
            "expected_behavior": "answer",
            "citation_correct": True,
            "faithful": True,
            "complete": False,
        },
        {
            "question_id": "R1",
            "review_status": "reviewed",
            "expected_behavior": "refuse",
            "refusal_correct": True,
        },
        {"question_id": "P1", "review_status": "pending"},
    ]
    report = AnswerQualityEvaluator().evaluate(reviews)
    assert report["reviewed_count"] == 2
    assert report["pending_count"] == 1
    assert report["citation_correct_rate"] == 1.0
    assert report["answer_completeness_rate"] == 0.0
    assert report["refusal_correctness_rate"] == 1.0
    assert report["fully_correct_answer_rate"] == 0.0


def test_answer_quality_rejects_missing_human_labels() -> None:
    with pytest.raises(ValueError):
        AnswerQualityEvaluator().evaluate(
            [
                {
                    "question_id": "A1",
                    "review_status": "reviewed",
                    "expected_behavior": "answer",
                    "citation_correct": None,
                }
            ]
        )
