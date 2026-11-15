from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import statistics
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.retriever import LegalRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calibrate the dense evidence threshold on positive and negative queries."
    )
    parser.add_argument(
        "--positive-questions",
        type=Path,
        default=ROOT / "data" / "evaluation" / "test_questions_v1.json",
    )
    parser.add_argument(
        "--negative-questions",
        type=Path,
        default=ROOT / "data" / "evaluation" / "evidence_negative_queries_v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "evaluation" / "evidence_calibration_v1.json",
    )
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def _summary(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("Không thể tổng hợp danh sách score rỗng.")
    ordered = sorted(values)
    return {
        "min": round(ordered[0], 6),
        "median": round(statistics.median(ordered), 6),
        "mean": round(statistics.fmean(ordered), 6),
        "max": round(ordered[-1], 6),
    }


def _balanced_accuracy(rows: list[dict[str, Any]], threshold: float) -> float:
    positives = [row for row in rows if row["expected_answerable"]]
    negatives = [row for row in rows if not row["expected_answerable"]]
    if not positives or not negatives:
        raise ValueError("Calibration cần cả câu answerable và unanswerable.")
    true_positive_rate = sum(
        row["top_dense_score"] >= threshold for row in positives
    ) / len(positives)
    true_negative_rate = sum(
        row["top_dense_score"] < threshold for row in negatives
    ) / len(negatives)
    return (true_positive_rate + true_negative_rate) / 2


def _candidate_thresholds(rows: list[dict[str, Any]]) -> list[float]:
    scores = sorted({float(row["top_dense_score"]) for row in rows})
    if not scores:
        raise ValueError("Calibration không có score.")
    thresholds = [scores[0] - 1e-6, scores[-1] + 1e-6]
    thresholds.extend((left + right) / 2 for left, right in zip(scores, scores[1:]))
    return thresholds


def _validate_questions(items: Any, *, source: str) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise ValueError(f"{source} phải là JSON array không rỗng.")
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"{source}[{index}] phải là object.")
        question_id = str(item.get("question_id", "")).strip()
        question = str(item.get("question", "")).strip()
        if not question_id or not question:
            raise ValueError(f"{source}[{index}] thiếu question_id hoặc question.")
        if question_id in seen:
            raise ValueError(f"{source} trùng question_id: {question_id}")
        seen.add(question_id)
    return items


def _accuracy_by_group(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row["evaluation_group"]), []).append(row)
    output: dict[str, Any] = {}
    for name, group_rows in sorted(groups.items()):
        expected = bool(group_rows[0]["expected_answerable"])
        correct = sum(
            (row["top_dense_score"] >= threshold) == expected
            for row in group_rows
        )
        output[name] = {
            "count": len(group_rows),
            "expected_answerable": expected,
            "accuracy": round(correct / len(group_rows), 6),
            "dense_scores": _summary(
                [float(row["top_dense_score"]) for row in group_rows]
            ),
        }
    return output


def main() -> None:
    args = parse_args()
    positives = _validate_questions(
        json.loads(args.positive_questions.read_text(encoding="utf-8")),
        source="positive_questions",
    )
    negatives = _validate_questions(
        json.loads(args.negative_questions.read_text(encoding="utf-8")),
        source="negative_questions",
    )
    retriever = LegalRetriever(
        index_path=ROOT / "data" / "vector_db" / "legal_chunks.faiss",
        vector_metadata_path=ROOT / "data" / "vector_db" / "legal_chunks_metadata.json",
        embedding_manifest_path=ROOT / "data" / "processed" / "legal_embeddings_manifest.json",
        chunks_path=ROOT / "data" / "processed" / "legal_chunks.json",
        device=args.device,
    )
    rows: list[dict[str, Any]] = []
    positive_ids = {str(item["question_id"]) for item in positives}
    if positive_ids.intersection(str(item["question_id"]) for item in negatives):
        raise ValueError("Question IDs must be unique across calibration datasets.")
    for item, expected in [
        *((item, True) for item in positives),
        *((item, False) for item in negatives),
    ]:
        results = retriever.retrieve_hybrid(str(item["question"]), top_k=2)
        rows.append(
            {
                "question_id": item["question_id"],
                "question": item["question"],
                "category": item.get("category", item.get("question_type", "positive")),
                "evaluation_group": (
                    "answerable_positive"
                    if expected
                    else (
                        "missing_source"
                        if str(item.get("category", "")).startswith("missing_")
                        else "upstream_scope_rejection"
                    )
                ),
                "expected_answerable": expected,
                "top_article": results[0]["article_no"],
                "top_dense_score": round(float(results[0]["dense_score"]), 6),
                "top_combined_score": round(float(results[0]["score"]), 6),
                "dense_margin_top_1_2": round(
                    float(results[0]["dense_score"]) - float(results[1]["dense_score"]), 6
                ),
            }
        )
    threshold_rows = [
        row
        for row in rows
        if row["evaluation_group"] in {"answerable_positive", "missing_source"}
    ]
    candidates = _candidate_thresholds(threshold_rows)
    ranked = sorted(
        (
            (_balanced_accuracy(threshold_rows, threshold), threshold)
            for threshold in candidates
        ),
        # On ties, prefer the lower threshold to reduce false refusals.
        key=lambda pair: (pair[0], -pair[1]),
        reverse=True,
    )
    best_accuracy, best_threshold = ranked[0]
    positive_scores = [row["top_dense_score"] for row in rows if row["expected_answerable"]]
    negative_scores = [row["top_dense_score"] for row in rows if not row["expected_answerable"]]
    report = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "label_status": "in_sample_diagnostic_not_legal_ground_truth",
        "warning": (
            "The threshold is selected and scored on the same diagnostic rows; it is not "
            "held-out validation. Missing-source labels require legal review before use."
        ),
        "positive_count": len(positive_scores),
        "negative_count": len(negative_scores),
        "positive_dense_scores": _summary(positive_scores),
        "negative_dense_scores": _summary(negative_scores),
        "recommended_dense_threshold": round(best_threshold, 6),
        "balanced_accuracy_at_recommendation": round(best_accuracy, 6),
        "balanced_accuracy_at_current_0_55": round(
            _balanced_accuracy(threshold_rows, 0.55), 6
        ),
        "groups_at_recommendation": _accuracy_by_group(rows, best_threshold),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "rows"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
