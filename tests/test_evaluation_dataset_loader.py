from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation.dataset_loader import extract_questions


def test_extract_questions_supports_versioned_and_legacy_datasets() -> None:
    legacy, metadata = extract_questions(
        [{"question_id": "Q1", "question": "Câu hỏi"}]
    )
    assert legacy[0]["question_id"] == "Q1"
    assert metadata == {}

    versioned, metadata = extract_questions(
        {
            "dataset_metadata": {"dataset_id": "v2"},
            "questions": [{"question_id": "V2Q001", "question": "Câu hỏi mới"}],
        }
    )
    assert versioned[0]["question_id"] == "V2Q001"
    assert metadata["dataset_id"] == "v2"


def test_extract_questions_rejects_empty_or_malformed_payload() -> None:
    with pytest.raises(ValueError):
        extract_questions({"questions": []})
    with pytest.raises(ValueError):
        extract_questions({"dataset_metadata": {}})
