from __future__ import annotations

from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation import RetrievalEvaluator


class FakeRetriever:
    def retrieve(self, question: str, *, top_k: int = 5):
        mapping = {
            "first": [1, 9, 8],
            "third": [7, 8, 3],
            "miss": [7, 8, 9],
        }
        return [
            {"article_no": article, "chunk_id": f"c{article}", "score": 1 / rank}
            for rank, article in enumerate(mapping[question][:top_k], start=1)
        ]


def test_metrics_are_computed_correctly() -> None:
    questions = [
        {"question_id": "1", "question": "first", "expected_article_numbers": [1]},
        {"question_id": "2", "question": "third", "expected_article_numbers": [3]},
        {"question_id": "3", "question": "miss", "expected_article_numbers": [4]},
    ]
    report = RetrievalEvaluator(FakeRetriever(), top_k=3).evaluate(questions)
    assert report["hit_at_1"] == 1 / 3
    assert report["recall_at_3"] == 2 / 3
    assert report["mrr"] == (1 + 1 / 3) / 3


def test_dataset_has_unique_ids_and_valid_articles() -> None:
    questions = json.loads(
        (ROOT / "data" / "evaluation" / "test_questions_v1.json").read_text(encoding="utf-8")
    )
    ids = [item["question_id"] for item in questions]
    assert len(questions) == 30
    assert len(ids) == len(set(ids))
    assert all(item["expected_article_numbers"] for item in questions)


def main() -> None:
    test_metrics_are_computed_correctly()
    test_dataset_has_unique_ids_and_valid_articles()
    print("MODULE 15 - RETRIEVAL EVALUATOR: SUCCESS")


if __name__ == "__main__":
    main()
