from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation.system_behavior_evaluator import SystemBehaviorEvaluator


class _FakeAssistant:
    def answer(self, question: str):
        if "ngoài phạm vi" in question:
            return {"status": "out_of_scope", "citations": [], "latency_ms": 1}
        return {
            "status": "success",
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
    assert report["answer_success_rate"] == 1.0
    assert report["article_hit_at_1_rate"] == 1.0
    assert report["article_hit_at_k_rate"] == 1.0
    assert report["article_mrr"] == 1.0
    assert report["refusal_correctness_rate"] == 1.0
    assert report["overall_grounded_behavior_accuracy"] == 1.0


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
    assert report["answer_success_rate"] == 1.0
    assert report["article_hit_at_1_rate"] == 0.0
    assert report["article_hit_at_k_rate"] == 0.0
    assert report["overall_grounded_behavior_accuracy"] == 0.0


class _ExpectedArticleAtRankTwo:
    def answer(self, question: str):
        return {
            "status": "success",
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
    assert report["overall_grounded_behavior_accuracy"] == 0.0
