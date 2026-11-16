from __future__ import annotations

from pathlib import Path
import importlib.util
import json

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "freeze_evaluation_dataset",
    ROOT / "scripts" / "freeze_evaluation_dataset.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_manifest_records_hash_and_full_baseline(tmp_path: Path) -> None:
    dataset = tmp_path / "questions.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "question_id": "V2Q001",
                    "question": "Câu hỏi thử nghiệm?",
                    "label_status": "pending_review",
                    "expected_behavior": "answer",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    # build_manifest requires a repository-relative path for the final manifest.
    repository_dataset = ROOT / "data" / "evaluation" / "_freeze_test.json"
    repository_dataset.write_bytes(dataset.read_bytes())
    try:
        manifest = MODULE.build_manifest(repository_dataset, "73d3a14")
    finally:
        repository_dataset.unlink(missing_ok=True)
    assert manifest["question_count"] == 1
    assert len(manifest["dataset_sha256"]) == 64
    assert manifest["baseline_commit"].startswith("73d3a14")
    assert "not independent" in manifest["independence_warning"]


def test_build_manifest_rejects_duplicate_ids() -> None:
    repository_dataset = ROOT / "data" / "evaluation" / "_freeze_test.json"
    repository_dataset.write_text(
        json.dumps(
            [
                {"question_id": "Q1", "question": "Một"},
                {"question_id": "Q1", "question": "Hai"},
            ]
        ),
        encoding="utf-8",
    )
    try:
        with pytest.raises(ValueError, match="trùng"):
            MODULE.build_manifest(repository_dataset, "73d3a14")
    finally:
        repository_dataset.unlink(missing_ok=True)
