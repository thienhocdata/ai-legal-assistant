from __future__ import annotations

import json

import pytest

from scripts.promote_experimental_corpus import validate_experiment


def test_promotion_rejects_manifest_without_quality_gate(tmp_path) -> None:
    (tmp_path / "experiment_manifest.json").write_text(
        json.dumps(
            {
                "status": "experimental_index_built",
                "quality_gate": {"passed": False},
                "production_replaced": False,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="quality gate"):
        validate_experiment(tmp_path)


def test_promotion_rejects_unbuilt_experiment(tmp_path) -> None:
    (tmp_path / "experiment_manifest.json").write_text(
        json.dumps(
            {
                "status": "parser_validated",
                "quality_gate": {"passed": True},
                "production_replaced": False,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="validated index"):
        validate_experiment(tmp_path)
