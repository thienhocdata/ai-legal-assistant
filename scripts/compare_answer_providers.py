from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import Settings
from app.evaluation.dataset_loader import extract_questions
from app.evaluation.provider_comparison import ProviderComparisonRunner
from app.llm_provider import create_llm_provider
from app.rag.retriever import LegalRetriever
from app.services.legal_assistant import LegalAssistantService


EVALUATION_DIR = (ROOT / "data" / "evaluation").resolve()
RUNS_DIR = (EVALUATION_DIR / "runs").resolve()


class _NullLogger:
    def log(self, event_type: str, payload: dict[str, Any]) -> None:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare answer-provider runtime behavior on an explicit synthetic dataset."
    )
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["extractive", "gemini", "qwen"],
        choices=("extractive", "gemini", "qwen"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-answer-text", action="store_true")
    parser.add_argument("--acknowledge-synthetic-data", action="store_true")
    parser.add_argument("--require-all", action="store_true")
    return parser.parse_args()


def _resolve_questions(path: Path) -> Path:
    resolved = (path if path.is_absolute() else ROOT / path).resolve()
    if resolved != EVALUATION_DIR and EVALUATION_DIR not in resolved.parents:
        raise ValueError("Questions file phải nằm trong data/evaluation/.")
    if RUNS_DIR in resolved.parents:
        raise ValueError("Không dùng runtime output trong data/evaluation/runs làm input.")
    return resolved


def _resolve_output(path: Path | None) -> Path:
    if path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return RUNS_DIR / f"provider_comparison_{stamp}.json"
    resolved = (path if path.is_absolute() else ROOT / path).resolve()
    if resolved != RUNS_DIR and RUNS_DIR not in resolved.parents:
        raise ValueError("Output phải nằm trong data/evaluation/runs/ (đã gitignore).")
    return resolved


def _service_factory() -> Any:
    settings = Settings.from_env()
    retriever = LegalRetriever(
        index_path=ROOT / "data" / "vector_db" / "legal_chunks.faiss",
        vector_metadata_path=ROOT / "data" / "vector_db" / "legal_chunks_metadata.json",
        embedding_manifest_path=ROOT / "data" / "processed" / "legal_embeddings_manifest.json",
        chunks_path=ROOT / "data" / "processed" / "legal_chunks.json",
        device="cpu",
    )

    def build(provider_name: str) -> LegalAssistantService:
        provider = create_llm_provider(provider_name)
        service = LegalAssistantService(
            settings=Settings(
                project_root=ROOT,
                llm_provider=provider_name,
                retrieval_top_k=settings.retrieval_top_k,
                minimum_dense_score=settings.minimum_dense_score,
            ),
            provider=provider,
            retriever=retriever,
        )
        service.logger = _NullLogger()
        return service

    return build


def main() -> None:
    args = parse_args()
    if args.include_answer_text and not args.acknowledge_synthetic_data:
        raise ValueError(
            "--include-answer-text yêu cầu --acknowledge-synthetic-data. "
            "Không dùng tùy chọn này cho câu hỏi cá nhân."
        )
    questions_path = _resolve_questions(args.questions)
    output_path = _resolve_output(args.output)
    content = questions_path.read_bytes()
    questions, dataset_metadata = extract_questions(json.loads(content.decode("utf-8")))
    report = ProviderComparisonRunner(_service_factory()).run(
        questions,
        args.providers,
        dataset_sha256=ProviderComparisonRunner.hash_bytes(content),
        include_answer_text=args.include_answer_text,
    )
    report["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    report["dataset_file"] = questions_path.relative_to(ROOT).as_posix()
    report["dataset_metadata"] = dataset_metadata
    unavailable = [
        row["requested_provider"]
        for row in report["providers"]
        if row["setup_status"] != "ready"
    ]
    failed_runtime = [
        row["requested_provider"]
        for row in report["providers"]
        if row["setup_status"] == "ready"
        and (
            row["summary"]["runner_errors"] > 0
            or row["summary"]["fallback_count"] > 0
            or row["summary"]["native_response_count"] == 0
        )
    ]
    if args.require_all and (unavailable or failed_runtime):
        raise RuntimeError(
            "Provider chưa đạt native runtime gate: "
            + ", ".join(sorted(set(unavailable + failed_runtime)))
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = {
        "output": output_path.relative_to(ROOT).as_posix(),
        "question_count": report["question_count"],
        "unavailable_providers": unavailable,
        "failed_runtime_providers": failed_runtime,
        "providers": [
            {
                "provider": row["requested_provider"],
                "setup_status": row["setup_status"],
                "summary": row["summary"],
            }
            for row in report["providers"]
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
