from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import Settings
from app.evaluation.dataset_loader import extract_questions
from app.evaluation.system_behavior_evaluator import SystemBehaviorEvaluator
from app.llm_provider import ExtractiveProvider
from app.rag.retriever import LegalRetriever
from app.services.legal_assistant import LegalAssistantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate frozen questions against the offline system baseline."
    )
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--allow-code-drift", action="store_true")
    parser.add_argument("--allow-overwrite", action="store_true")
    return parser.parse_args()


def _resolve_inside_repository(path: Path) -> Path:
    resolved = (path if path.is_absolute() else ROOT / path).resolve()
    if resolved != ROOT.resolve() and ROOT.resolve() not in resolved.parents:
        raise ValueError("Đường dẫn phải nằm trong repository.")
    return resolved


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _artifact_fingerprint(path: Path) -> dict[str, str | int]:
    content = path.read_bytes()
    if path.suffix.lower() in {".json", ".py"}:
        digest_content = content.replace(b"\r\n", b"\n")
        digest_mode = "normalized_lf_text"
    else:
        digest_content = content
        digest_mode = "raw_bytes"
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(digest_content).hexdigest(),
        "sha256_mode": digest_mode,
        "size_bytes": len(content),
    }


def _verify_frozen_dataset(
    questions_path: Path,
    questions_bytes: bytes,
    manifest: dict,
) -> str:
    dataset_sha256 = sha256(questions_bytes).hexdigest()
    if manifest.get("dataset_sha256") != dataset_sha256:
        raise ValueError("SHA-256 dataset không khớp freeze manifest.")
    if manifest.get("dataset") != questions_path.relative_to(ROOT).as_posix():
        raise ValueError("Dataset path không khớp freeze manifest.")
    return dataset_sha256


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    questions_path = _resolve_inside_repository(args.questions)
    manifest_path = _resolve_inside_repository(args.manifest)
    output_path = _resolve_inside_repository(args.output)
    if output_path.exists() and not args.allow_overwrite:
        raise FileExistsError(
            "Output đã tồn tại; dùng path mới hoặc --allow-overwrite có chủ đích."
        )
    questions_bytes = questions_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    dataset_sha256 = _verify_frozen_dataset(
        questions_path, questions_bytes, manifest
    )
    current_git_commit = _git("rev-parse", "HEAD")
    baseline_commit = str(manifest.get("baseline_commit", ""))
    if not baseline_commit:
        raise ValueError("Freeze manifest thiếu baseline_commit.")
    _git("rev-parse", "--verify", f"{baseline_commit}^{{commit}}")
    baseline_match = current_git_commit == baseline_commit
    if not baseline_match and not args.allow_code_drift:
        raise RuntimeError(
            "HEAD không khớp baseline_commit; checkout baseline hoặc dùng "
            "--allow-code-drift và lưu output phiên bản mới."
        )
    questions, dataset_metadata = extract_questions(
        json.loads(questions_bytes.decode("utf-8"))
    )
    settings = Settings(project_root=ROOT, llm_provider="none")
    retriever = LegalRetriever(
        index_path=ROOT / "data" / "vector_db" / "legal_chunks.faiss",
        vector_metadata_path=ROOT / "data" / "vector_db" / "legal_chunks_metadata.json",
        embedding_manifest_path=ROOT / "data" / "processed" / "legal_embeddings_manifest.json",
        chunks_path=ROOT / "data" / "processed" / "legal_chunks.json",
        device=args.device,
    )
    service = LegalAssistantService(
        settings=settings,
        provider=ExtractiveProvider(),
        retriever=retriever,
    )
    report = SystemBehaviorEvaluator(service).evaluate(questions)
    fingerprint_paths = [
        ROOT / "app" / "core" / "config.py",
        ROOT / "app" / "evaluation" / "system_behavior_evaluator.py",
        ROOT / "app" / "rag" / "retriever.py",
        ROOT / "app" / "services" / "legal_assistant.py",
        ROOT / "scripts" / "evaluate_system_behavior.py",
        ROOT / "data" / "processed" / "legal_chunks.json",
        ROOT / "data" / "processed" / "legal_embeddings_manifest.json",
        ROOT / "data" / "vector_db" / "legal_chunks.faiss",
        ROOT / "data" / "vector_db" / "legal_chunks_metadata.json",
    ]
    dirty_output = _git(
        "status", "--porcelain", "--", "app", "scripts/evaluate_system_behavior.py"
    )
    report.update(
        {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "questions_file": questions_path.relative_to(ROOT).as_posix(),
            "provider_mode": "extractive_offline",
            "dataset_metadata": dataset_metadata,
            "provenance": {
                "dataset_sha256": dataset_sha256,
                "manifest_file": manifest_path.relative_to(ROOT).as_posix(),
                "manifest_sha256": sha256(
                    manifest_bytes.replace(b"\r\n", b"\n")
                ).hexdigest(),
                "manifest_sha256_mode": "normalized_lf_text",
                "baseline_commit": baseline_commit,
                "evaluation_git_commit": current_git_commit,
                "baseline_commit_matches_head": baseline_match,
                "relevant_worktree_dirty": bool(dirty_output),
                "relevant_worktree_status": dirty_output.splitlines(),
                "runtime_config": {
                    "device": args.device,
                    "retrieval_top_k": settings.retrieval_top_k,
                    "minimum_dense_score": settings.minimum_dense_score,
                },
                "artifact_fingerprints": [
                    _artifact_fingerprint(path) for path in fingerprint_paths
                ],
            },
            "interpretation_warning": (
                "Article ranking and routing behavior are technical metrics, not "
                "independent legal correctness or answer-quality validation."
            ),
        }
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "rows"},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
