"""Read-only local demo checks. Never sends a hosted API request or prints keys."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Mapping
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_MODULES = (
    "fastapi", "uvicorn", "httpx", "pydantic", "dotenv", "numpy", "faiss",
    "torch", "sentence_transformers",
)
ARTIFACT_FILES = (
    "data/processed/legal_chunks.json",
    "data/processed/legal_embeddings.npy",
    "data/processed/legal_embeddings_metadata.json",
    "data/processed/legal_embeddings_manifest.json",
    "data/vector_db/legal_chunks.faiss",
    "data/vector_db/legal_chunks_metadata.json",
    "data/vector_db/vector_store_manifest.json",
)


def inspect_configuration(root: Path, environ: Mapping[str, str]) -> dict[str, Any]:
    from dotenv import dotenv_values

    # Read without loading values into this process. Inherited environment wins,
    # matching Settings.from_env(override=False). Never return raw config values.
    values = {**dotenv_values(root / ".env", interpolate=False), **environ}
    selected = str(values.get("LLM_PROVIDER") or "none").strip().lower()
    aliases = {"": "none", "local": "none", "extractive": "none"}
    selected = aliases.get(selected, selected)
    if selected not in {"none", "qwen", "gemini", "openrouter"}:
        return {"status": "fail", "selected_provider": "unsupported"}
    credential = {
        "qwen": values.get("QWEN_API_KEY") or values.get("DASHSCOPE_API_KEY"),
        "gemini": values.get("GEMINI_API_KEY"),
        "openrouter": values.get("OPENROUTER_API_KEY"),
    }.get(selected)
    present = bool(str(credential or "").strip())
    result: dict[str, Any] = {
        "status": "pass" if selected == "none" or present else "fail",
        "selected_provider": selected,
        "credential_value_present": present if selected != "none" else None,
        "credential_validity": "unverified" if selected != "none" else "not_required",
        "hosted_credentials_present": {
            "qwen": bool(str(values.get("QWEN_API_KEY") or values.get("DASHSCOPE_API_KEY") or "").strip()),
            "gemini": bool(str(values.get("GEMINI_API_KEY") or "").strip()),
            "openrouter": bool(str(values.get("OPENROUTER_API_KEY") or "").strip()),
        },
        "hosted_live_tested": False,
    }
    if selected == "qwen":
        url = urlparse(str(values.get("QWEN_BASE_URL") or
                           "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"))
        endpoint_shape_ok = (
            url.scheme == "https" and bool(url.hostname) and not url.username
            and not url.password and not url.query and not url.fragment
            and url.path.rstrip("/").endswith("/compatible-mode/v1")
        )
        result["endpoint_shape_valid"] = endpoint_shape_ok
        if not endpoint_shape_ok:
            result["status"] = "fail"
    if selected == "openrouter":
        model = str(values.get("OPENROUTER_MODEL", "baidu/ernie-5.5-flash-preview:free") or "").strip()
        free_model_only = model == "openrouter/free" or model.endswith(":free")
        result["free_model_only"] = free_model_only
        if not free_model_only:
            result["status"] = "fail"
    return result


def inspect_artifacts(root: Path) -> dict[str, Any]:
    import numpy as np
    from app.kb.chunk_validator import ChunkValidator
    from app.rag.vector_store import FaissVectorStore
    from scripts.build_embeddings import TEXT_FIELD, compute_chunks_sha256

    missing = [name for name in ARTIFACT_FILES if not (root / name).is_file()]
    if missing:
        return {"status": "fail", "missing_files": missing}
    read_json = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    chunks = read_json("data/processed/legal_chunks.json")
    manifest = read_json("data/processed/legal_embeddings_manifest.json")
    vector_manifest = read_json("data/vector_db/vector_store_manifest.json")
    rows = read_json("data/processed/legal_embeddings_metadata.json")
    validator = ChunkValidator(max_chars=5000, text_field=TEXT_FIELD)
    if not validator.validate(chunks, require_legal_metadata=True).valid:
        return {"status": "fail", "error_code": "chunk_validation_failed"}
    if (manifest.get("text_field") != TEXT_FIELD or
            manifest.get("source_chunks_sha256") != compute_chunks_sha256(chunks)):
        return {"status": "fail", "error_code": "source_chunks_hash_mismatch"}
    embeddings = np.load(root / "data/processed/legal_embeddings.npy", allow_pickle=False)
    # Reuse the same vector and metadata gates as the production vector store.
    vectors = FaissVectorStore._validate_embeddings(embeddings)
    FaissVectorStore._validate_metadata(rows, len(chunks))
    store = FaissVectorStore()
    store.load(root / "data/vector_db/legal_chunks.faiss",
               root / "data/vector_db/legal_chunks_metadata.json")
    count, dimension = vectors.shape
    ids = [chunk["chunk_id"] for chunk in chunks]
    aligned = ids == [row["chunk_id"] for row in rows] == [row["chunk_id"] for row in store.metadata]
    consistent = (
        aligned and count == len(chunks) == int(store.index.ntotal)
        == manifest.get("chunk_count") == vector_manifest.get("vector_count")
        and dimension == store.dimension == manifest.get("embedding_dimension")
        == vector_manifest.get("dimension")
        and manifest.get("model_name") == vector_manifest.get("model_name")
        and {chunk["document_id"] for chunk in chunks} == {manifest.get("document_id")}
        and np.allclose(store.index.reconstruct_n(0, count), vectors, atol=1e-6)
    )
    return {
        "status": "pass" if consistent else "fail",
        "chunk_count": len(chunks), "vector_count": int(store.index.ntotal),
        "dimension": store.dimension, "source_hash_matches": True,
        "ids_and_vectors_aligned": consistent,
    }


def probe_local_model(root: Path) -> dict[str, Any]:
    from app.rag.retriever import LegalRetriever

    # Opt-in probe uses cached model files only, never a hosted answer provider.
    names = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
    before = {name: os.environ.get(name) for name in names}
    try:
        for name in names:
            os.environ[name] = "1"
        retriever = LegalRetriever(
            index_path=root / "data/vector_db/legal_chunks.faiss",
            vector_metadata_path=root / "data/vector_db/legal_chunks_metadata.json",
            embedding_manifest_path=root / "data/processed/legal_embeddings_manifest.json",
            chunks_path=root / "data/processed/legal_chunks.json", device="cpu",
        )
        rows = retriever.retrieve_hybrid("Phạm vi điều chỉnh của Luật Đất đai", top_k=1)
        return {"status": "pass" if rows else "fail", "hosted_live_tested": False}
    finally:
        for name, value in before.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _safe_check(function, *args) -> dict[str, Any]:
    try:
        return function(*args)
    except Exception as exc:
        # Import/network/file exceptions may embed private config or paths.
        return {"status": "fail", "error_code": type(exc).__name__}


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def collect_report(root: Path = ROOT, *, probe_model: bool = False,
                   environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    modules = {name: _module_available(name) for name in REQUIRED_MODULES}
    configuration = _safe_check(inspect_configuration, root, os.environ if environ is None else environ)
    if configuration.get("selected_provider") == "gemini":
        modules["google.genai"] = _module_available("google.genai")
    artifacts = _safe_check(inspect_artifacts, root)
    dependencies_ok = sys.version_info >= (3, 11) and all(modules.values())
    local_checks_ok = dependencies_ok and artifacts["status"] == "pass"
    probe = _safe_check(probe_local_model, root) if probe_model and local_checks_ok else {
        "status": "not_checked", "hosted_live_tested": False,
    }
    return {
        "python_supported": sys.version_info >= (3, 11),
        "module_available": modules, "node_available": shutil.which("node") is not None,
        "configuration": configuration, "artifacts": artifacts, "local_model_probe": probe,
        "local_checks_passed": local_checks_ok,
        "local_runtime_ready": probe["status"] == "pass" if probe_model else None,
        "hosted_live_tested": False,
        "configured_demo_checks_passed": local_checks_ok and configuration["status"] == "pass"
        and (not probe_model or probe["status"] == "pass"),
        "start_command": ".\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
        "interpretation": "Local integrity/configuration checks do not establish hosted API success or legal correctness.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-model", action="store_true", help="Probe cached local retrieval offline; no hosted API call.")
    args = parser.parse_args()
    report = collect_report(probe_model=args.probe_model)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    raise SystemExit(0 if report["configured_demo_checks_passed"] else 1)


if __name__ == "__main__":
    main()
