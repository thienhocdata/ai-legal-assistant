from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.vector_store import FaissVectorStore


DOCUMENT_ID = "vbhn_133_2025_luat_dat_dai"
EXPERIMENT_DIR = ROOT / "data" / "experiments" / DOCUMENT_ID
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_DIR = ROOT / "data" / "vector_db"
BACKUP_ROOT = ROOT / "data" / "backups"

PROCESSED_FILES = {
    "raw.txt": f"{DOCUMENT_ID}.txt",
    "normalized.txt": f"{DOCUMENT_ID}_normalized.txt",
    "normalizer_report.json": f"{DOCUMENT_ID}_normalizer_report.json",
    "legal_tree.json": f"{DOCUMENT_ID}.json",
    "baseline_chunks.json": "baseline_chunks.json",
    "legal_chunks.json": "legal_chunks.json",
    "legal_embeddings.npy": "legal_embeddings.npy",
    "legal_embeddings_metadata.json": "legal_embeddings_metadata.json",
}
VECTOR_FILES = {
    "legal_chunks.faiss": "legal_chunks.faiss",
    "legal_chunks_metadata.json": "legal_chunks_metadata.json",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_experiment(experiment_dir: Path = EXPERIMENT_DIR) -> dict[str, Any]:
    manifest_path = experiment_dir / "experiment_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing experiment manifest: {manifest_path}")
    manifest = _load_json(manifest_path)
    if manifest.get("status") != "experimental_index_built":
        raise ValueError("Experiment has not built a validated index.")
    if not manifest.get("quality_gate", {}).get("passed"):
        raise ValueError("Experiment quality gate did not pass.")
    if manifest.get("production_replaced") is not False:
        raise ValueError("Unexpected experiment provenance flag.")

    required = set(PROCESSED_FILES) | set(VECTOR_FILES) | {
        "legal_embeddings_manifest.json",
        "vector_store_manifest.json",
    }
    missing = sorted(name for name in required if not (experiment_dir / name).is_file())
    if missing:
        raise FileNotFoundError(f"Missing experimental artifacts: {missing}")

    chunks = _load_json(experiment_dir / "legal_chunks.json")
    embedding_metadata = _load_json(experiment_dir / "legal_embeddings_metadata.json")
    vector_metadata = _load_json(experiment_dir / "legal_chunks_metadata.json")
    embeddings = np.load(experiment_dir / "legal_embeddings.npy", mmap_mode="r")
    store = FaissVectorStore()
    store.load(
        experiment_dir / "legal_chunks.faiss",
        experiment_dir / "legal_chunks_metadata.json",
    )
    counts = {
        len(chunks),
        len(embedding_metadata),
        len(vector_metadata),
        int(embeddings.shape[0]),
        int(store.index.ntotal),
    }
    if counts != {441}:
        raise ValueError(f"Experimental artifact counts are inconsistent: {counts}")
    if int(embeddings.shape[1]) != 384 or store.dimension != 384:
        raise ValueError("Experimental embedding dimension must be 384.")
    if {int(row["article_no"]) for row in chunks} != set(range(1, 261)):
        raise ValueError("Experimental corpus must contain Articles 1 through 260.")
    return manifest


def _write_json_atomic(value: Any, target: Path) -> None:
    temporary = target.with_suffix(target.suffix + ".promote.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(temporary, target)


def _copy_atomic(source: Path, target: Path) -> None:
    temporary = target.with_suffix(target.suffix + ".promote.tmp")
    shutil.copy2(source, temporary)
    os.replace(temporary, target)


def promote(experiment_dir: Path = EXPERIMENT_DIR) -> Path:
    manifest = validate_experiment(experiment_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = BACKUP_ROOT / f"pre_{DOCUMENT_ID}_{timestamp}"
    (backup_dir / "processed").mkdir(parents=True, exist_ok=False)
    (backup_dir / "vector_db").mkdir(parents=True, exist_ok=False)

    for directory, names in (
        (PROCESSED_DIR, set(PROCESSED_FILES.values()) | {"legal_embeddings_manifest.json"}),
        (VECTOR_DIR, set(VECTOR_FILES.values()) | {"vector_store_manifest.json"}),
    ):
        backup_target = backup_dir / directory.name
        for name in sorted(names):
            source = directory / name
            if source.is_file():
                shutil.copy2(source, backup_target / name)

    for source_name, target_name in PROCESSED_FILES.items():
        _copy_atomic(experiment_dir / source_name, PROCESSED_DIR / target_name)
    for source_name, target_name in VECTOR_FILES.items():
        _copy_atomic(experiment_dir / source_name, VECTOR_DIR / target_name)

    embedding_manifest = _load_json(experiment_dir / "legal_embeddings_manifest.json")
    embedding_manifest.update(
        {
            "source_chunks_file": str(PROCESSED_DIR / "legal_chunks.json"),
            "embeddings_file": str(PROCESSED_DIR / "legal_embeddings.npy"),
            "metadata_file": str(PROCESSED_DIR / "legal_embeddings_metadata.json"),
            "promoted_from": str(experiment_dir.relative_to(ROOT)),
            "promoted_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _write_json_atomic(
        embedding_manifest, PROCESSED_DIR / "legal_embeddings_manifest.json"
    )

    vector_manifest = _load_json(experiment_dir / "vector_store_manifest.json")
    vector_manifest.update(
        {
            "index_file": str(VECTOR_DIR / "legal_chunks.faiss"),
            "metadata_file": str(VECTOR_DIR / "legal_chunks_metadata.json"),
            "production_replaced": True,
            "promoted_from": str(experiment_dir.relative_to(ROOT)),
            "promoted_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _write_json_atomic(vector_manifest, VECTOR_DIR / "vector_store_manifest.json")

    promotion_manifest = {
        "document_id": DOCUMENT_ID,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "source_experiment": str(experiment_dir.relative_to(ROOT)),
        "backup_dir": str(backup_dir.relative_to(ROOT)),
        "quality_gate": manifest["quality_gate"],
        "chunk_count": 441,
        "embedding_dimension": 384,
    }
    _write_json_atomic(promotion_manifest, PROCESSED_DIR / "promotion_manifest.json")
    return backup_dir


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Promote a validated corpus to production.")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    manifest = validate_experiment()
    if args.validate_only:
        print(json.dumps({"valid": True, "status": manifest["status"]}, indent=2))
        return
    if not args.confirm:
        raise ValueError("Promotion requires --confirm after validation.")
    backup_dir = promote()
    print(json.dumps({"promoted": True, "backup_dir": str(backup_dir)}, indent=2))


if __name__ == "__main__":
    main()
