from __future__ import annotations

from pathlib import Path
import importlib.util
import json

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evaluate_system_behavior",
    ROOT / "scripts" / "evaluate_system_behavior.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_verify_frozen_dataset_accepts_matching_manifest() -> None:
    questions_path = ROOT / "data" / "evaluation" / "candidate_questions_v2_blind.json"
    manifest_path = (
        ROOT / "data" / "evaluation" / "candidate_questions_v2_blind_manifest.json"
    )
    questions_bytes = questions_path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert MODULE._verify_frozen_dataset(
        questions_path, questions_bytes, manifest
    ) == manifest["dataset_sha256"]


def test_verify_frozen_dataset_rejects_tampered_content() -> None:
    questions_path = ROOT / "data" / "evaluation" / "candidate_questions_v2_blind.json"
    manifest_path = (
        ROOT / "data" / "evaluation" / "candidate_questions_v2_blind_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="SHA-256"):
        MODULE._verify_frozen_dataset(questions_path, b"{}", manifest)
