from __future__ import annotations

import csv
import json
from pathlib import Path

from app.schemas.kb_schemas import DocumentMetadata
from scripts.validate_kb_metadata import validate_source_files


ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = ROOT / "data" / "metadata" / "documents"


def _load_metadata(document_id: str) -> DocumentMetadata:
    path = METADATA_DIR / f"{document_id}.json"
    return DocumentMetadata.model_validate_json(path.read_text(encoding="utf-8"))


def test_original_land_law_source_files_remain_verifiable_after_promotion() -> None:
    metadata = _load_metadata("luat_dat_dai_2024")

    assert metadata.legal_status == "amended"
    assert metadata.current_effective_date == "2024-08-01"
    assert metadata.processing.processing_status == "chunked"
    assert metadata.processing.indexed is False
    assert len(metadata.source.files) == 3
    assert validate_source_files(metadata) == []


def test_amendment_relationship_is_bidirectional() -> None:
    land_law = _load_metadata("luat_dat_dai_2024")
    amendment = _load_metadata("luat_43_2024")

    assert amendment.document_id in land_law.relations.amended_by
    assert land_law.document_id in amendment.relations.amends


def test_inventory_rows_have_matching_metadata_files() -> None:
    inventory = ROOT / "data" / "metadata" / "source_inventory.csv"
    with inventory.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))

    assert rows
    for row in rows:
        metadata_path = ROOT / row["metadata_path"]
        metadata = DocumentMetadata.model_validate_json(
            metadata_path.read_text(encoding="utf-8")
        )
        assert metadata.document_id == row["document_id"]


def test_consolidated_source_is_verifiable_and_indexed() -> None:
    metadata = _load_metadata("vbhn_133_2025_luat_dat_dai")

    assert metadata.processing.processing_status == "indexed"
    assert metadata.processing.indexed is True
    assert metadata.processing.experimental_status == "indexed"
    assert len(metadata.source.files) == 7
    assert sum(item.role == "official" for item in metadata.source.files) == 4
    assert sum(item.role == "derived" for item in metadata.source.files) == 3
    assert validate_source_files(metadata) == []


def test_production_artifacts_use_consolidated_document() -> None:
    chunks = json.loads(
        (ROOT / "data" / "processed" / "legal_chunks.json").read_text(
            encoding="utf-8"
        )
    )
    embedding_manifest = json.loads(
        (ROOT / "data" / "processed" / "legal_embeddings_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(chunks) == 441
    assert {chunk["document_id"] for chunk in chunks} == {
        "vbhn_133_2025_luat_dat_dai"
    }
    assert embedding_manifest["document_id"] == "vbhn_133_2025_luat_dat_dai"
    assert embedding_manifest["chunk_count"] == 441
