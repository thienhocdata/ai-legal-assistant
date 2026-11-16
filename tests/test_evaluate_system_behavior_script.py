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


def test_require_clean_refuses_dirty_source_before_evaluation() -> None:
    MODULE._require_clean_worktree("", enabled=True)
    MODULE._require_clean_worktree(" M app/agent/query_understanding.py", enabled=False)
    with pytest.raises(RuntimeError, match="require-clean"):
        MODULE._require_clean_worktree(" M app/agent/query_understanding.py", enabled=True)


def test_fingerprints_cover_routes_generation_guards_and_embedding() -> None:
    paths = {path.relative_to(ROOT).as_posix() for path in MODULE._fingerprint_paths()}
    assert {
        "app/agent/query_understanding.py",
        "app/agent/clarification.py",
        "app/citation/engine.py",
        "app/guardrails/engine.py",
        "app/llm_provider/extractive_provider.py",
        "app/rag/retriever.py",
        "data/processed/legal_embeddings.npy",
        "scripts/evaluate_system_behavior.py",
        "requirements.txt",
    }.issubset(paths)


def test_observed_v2_cannot_be_relabelled_as_unreviewed_candidate() -> None:
    path = ROOT / "data" / "evaluation" / "candidate_questions_v2_blind.json"
    metadata = {"dataset_id": "candidate_questions_v2_blind"}
    MODULE._verify_dataset_role(path, metadata, "development_observed")
    with pytest.raises(ValueError, match="đã quan sát"):
        MODULE._verify_dataset_role(path, metadata, "candidate_unreviewed")
