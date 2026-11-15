from __future__ import annotations

from pathlib import Path
import importlib.util
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "calibrate_evidence_threshold",
    ROOT / "scripts" / "calibrate_evidence_threshold.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_balanced_accuracy_rewards_separating_threshold() -> None:
    rows = [
        {"expected_answerable": True, "top_dense_score": 0.90},
        {"expected_answerable": True, "top_dense_score": 0.80},
        {"expected_answerable": False, "top_dense_score": 0.60},
        {"expected_answerable": False, "top_dense_score": 0.50},
    ]
    assert MODULE._balanced_accuracy(rows, 0.70) == 1.0
    assert MODULE._balanced_accuracy(rows, 0.40) == 0.5


def test_candidate_thresholds_include_score_boundaries() -> None:
    rows = [
        {"top_dense_score": 0.5},
        {"top_dense_score": 0.7},
    ]
    thresholds = MODULE._candidate_thresholds(rows)
    assert any(0.5 < value < 0.7 for value in thresholds)
    assert min(thresholds) < 0.5
    assert max(thresholds) > 0.7


def test_calibration_rejects_empty_or_single_class_inputs() -> None:
    with pytest.raises(ValueError):
        MODULE._summary([])
    with pytest.raises(ValueError):
        MODULE._balanced_accuracy(
            [{"expected_answerable": True, "top_dense_score": 0.9}],
            0.7,
        )


def test_question_validation_rejects_duplicates() -> None:
    rows = [
        {"question_id": "Q1", "question": "Một câu hỏi"},
        {"question_id": "Q1", "question": "Câu hỏi khác"},
    ]
    with pytest.raises(ValueError):
        MODULE._validate_questions(rows, source="test")
