from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation.system_behavior_evaluator import SystemBehaviorEvaluator, wilson95


class _FakeAssistant:
    def answer(self, question: str):
        if "ngoài phạm vi" in question:
            return {"status": "out_of_scope", "citations": [], "latency_ms": 1}
        return {
            "status": "success",
            "answer": "Đoạn trích [1]",
            "citations": [{"article_no": 45}],
            "provider": "extractive",
            "latency_ms": 2,
        }


def test_system_behavior_evaluator_separates_answer_and_refusal() -> None:
    report = SystemBehaviorEvaluator(_FakeAssistant()).evaluate(
        [
            {
                "question_id": "A1",
                "question": "Điều kiện chuyển nhượng?",
                "expected_behavior": "answer",
                "expected_article_numbers": [45],
            },
            {
                "question_id": "R1",
                "question": "Câu ngoài phạm vi",
                "expected_behavior": "refuse",
                "expected_article_numbers": [],
            },
        ]
    )
    assert report["schema_version"] == "2.0"
    assert report["answer_status_success_rate"] == 1.0
    assert report["article_hit_at_1_rate"] == 1.0
    assert report["article_hit_at_k_rate"] == 1.0
    assert report["article_mrr"] == 1.0
    assert report["refusal_route_match_rate"] == 1.0
    assert report["routing_and_top1_article_match_rate"] == 1.0
    assert report["answer_cited_article_hit_rate"] == 1.0
    assert "answer_success_rate" not in report
    assert "overall_grounded_behavior_accuracy" not in report


def test_wrong_article_is_not_behavior_correct() -> None:
    report = SystemBehaviorEvaluator(_FakeAssistant()).evaluate(
        [
            {
                "question_id": "A1",
                "question": "Điều kiện chuyển nhượng?",
                "expected_behavior": "answer",
                "expected_article_numbers": [95],
            }
        ]
    )
    assert report["answer_status_success_rate"] == 1.0
    assert report["article_hit_at_1_rate"] == 0.0
    assert report["article_hit_at_k_rate"] == 0.0
    assert report["routing_and_top1_article_match_rate"] == 0.0


class _ExpectedArticleAtRankTwo:
    def answer(self, question: str):
        return {
            "status": "success",
            "answer": "Đoạn trích đúng Điều kỳ vọng [2]",
            "citations": [{"article_no": 45}, {"article_no": 95}],
            "provider": "extractive",
        }


def test_hit_at_k_does_not_overstate_extractive_grounding() -> None:
    report = SystemBehaviorEvaluator(_ExpectedArticleAtRankTwo()).evaluate(
        [
            {
                "question_id": "A1",
                "question": "Câu hỏi có Điều đúng ở hạng hai",
                "expected_behavior": "answer",
                "expected_article_numbers": [95],
            }
        ]
    )
    assert report["article_hit_at_1_rate"] == 0.0
    assert report["article_hit_at_k_rate"] == 1.0
    assert report["article_mrr"] == 0.5
    assert report["routing_and_top1_article_match_rate"] == 0.0
    assert report["answer_cited_article_hit_rate"] == 1.0


def test_mrr_retains_duplicate_article_citation_positions() -> None:
    class _RepeatedArticleAssistant:
        def answer(self, question: str):
            return {
                "status": "success",
                "answer": "Đoạn trích [3], marker không hợp lệ [9]",
                "citations": [
                    {"article_no": 45}, {"article_no": 45}, {"article_no": 95}
                ],
            }

    report = SystemBehaviorEvaluator(_RepeatedArticleAssistant()).evaluate(
        [{
            "question_id": "A1",
            "question": "Câu hỏi Điều 95",
            "question_type": "multi_condition",
            "expected_behavior": "answer",
            "expected_article_numbers": [95],
        }]
    )
    assert report["article_mrr"] == pytest.approx(1 / 3, abs=1e-6)
    assert report["rows"][0]["retrieved_articles"] == [45, 45, 95]
    assert report["rows"][0]["answer_citation_labels"] == [3]
    assert report["rows"][0]["invalid_answer_citation_labels"] == [9]
    assert report["answer_cited_article_hit_rate"] == 1.0


def test_expected_statuses_can_distinguish_clarification_from_other_refusals() -> None:
    report = SystemBehaviorEvaluator(_FakeAssistant()).evaluate(
        [{
            "question_id": "R1",
            "question": "Câu ngoài phạm vi",
            "question_type": "ambiguous_refusal",
            "expected_behavior": "refuse",
            "expected_statuses": ["needs_clarification"],
        }]
    )
    assert report["refusal_route_match_rate"] == 0.0
    assert report["legacy_broad_refusal_label_count"] == 0
    assert report["refusal_status_counts"] == {"out_of_scope": 1}
    assert report["rows"][0]["refusal_route_match"] is False


def test_any_and_all_answer_citation_label_coverage_are_separate() -> None:
    report = SystemBehaviorEvaluator(_ExpectedArticleAtRankTwo()).evaluate(
        [{
            "question_id": "M1", "question": "Câu có nhiều nhãn Điều",
            "question_type": "multi_condition", "expected_behavior": "answer",
            "expected_article_numbers": [45, 95],
        }]
    )
    assert report["answer_cited_article_hit_rate"] == 1.0
    assert report["answer_cited_all_expected_articles_rate"] == 0.0


def test_cohorts_include_denominators_intervals_and_no_inapplicable_metrics() -> None:
    report = SystemBehaviorEvaluator(_FakeAssistant()).evaluate(
        [
            {
                "question_id": "A1", "question": "Điều kiện đất",
                "question_type": "direct", "expected_behavior": "answer",
                "expected_article_numbers": [45],
            },
            {
                "question_id": "R1", "question": "Câu ngoài phạm vi",
                "question_type": "ambiguous_refusal", "expected_behavior": "refuse",
            },
        ]
    )
    direct = report["cohorts"]["direct"]
    refusal = report["cohorts"]["ambiguous_refusal"]
    metric = direct["metric_details"]["article_hit_at_1_rate"]
    assert metric["numerator"] == metric["denominator"] == 1
    assert metric["wilson95"]["lower"] == pytest.approx(0.206549, abs=1e-6)
    assert metric["wilson95"]["upper"] == 1.0
    assert direct["refusal_route_match_rate"] is None
    assert refusal["article_mrr"] is None
    assert refusal["metric_details"]["article_hit_at_1_rate"]["wilson95"] is None
    assert "article_mrr" not in direct["metric_details"]


def test_wilson_interval_handles_small_sample_and_extreme_counts() -> None:
    assert wilson95(3, 10) == {"lower": 0.107791, "upper": 0.603222}
    assert wilson95(0, 10)["lower"] == 0.0
    assert wilson95(10, 10)["upper"] == 1.0
    assert wilson95(0, 0) is None
    with pytest.raises(ValueError):
        wilson95(2, 1)


def test_dataset_validation_happens_before_any_assistant_calls() -> None:
    class _MustNotRun:
        def answer(self, question: str):
            raise AssertionError("Assistant should not run on malformed dataset")

    with pytest.raises(ValueError, match="expected_statuses"):
        SystemBehaviorEvaluator(_MustNotRun()).evaluate(
            [
                {
                    "question_id": "A1", "question": "Câu hợp lệ",
                    "expected_behavior": "answer", "expected_article_numbers": [45],
                },
                {
                    "question_id": "R1", "question": "Câu sai status",
                    "expected_behavior": "refuse", "expected_statuses": ["success"],
                },
            ]
        )
