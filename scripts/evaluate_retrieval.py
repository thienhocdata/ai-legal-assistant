from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation import RetrievalEvaluator
from app.rag.retriever import LegalRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate dense legal retrieval.")
    parser.add_argument(
        "--questions",
        type=Path,
        default=ROOT / "data" / "evaluation" / "test_questions_v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "evaluation" / "retrieval_eval_v1.json",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--mode", choices=("dense", "hybrid"), default="hybrid")
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Optional isolated artifact directory; defaults to production artifacts.",
    )
    return parser.parse_args()


class _HybridAdapter:
    def __init__(self, retriever: LegalRetriever) -> None:
        self.retriever = retriever

    def retrieve(self, question: str, *, top_k: int = 5):
        return self.retriever.retrieve_hybrid(question, top_k=top_k)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    if args.artifact_dir:
        artifact_dir = (
            args.artifact_dir
            if args.artifact_dir.is_absolute()
            else ROOT / args.artifact_dir
        ).resolve()
        if ROOT.resolve() not in artifact_dir.parents:
            raise ValueError("Artifact directory must stay inside the repository.")
        index_path = artifact_dir / "legal_chunks.faiss"
        vector_metadata_path = artifact_dir / "legal_chunks_metadata.json"
        embedding_manifest_path = artifact_dir / "legal_embeddings_manifest.json"
        chunks_path = artifact_dir / "legal_chunks.json"
    else:
        index_path = ROOT / "data" / "vector_db" / "legal_chunks.faiss"
        vector_metadata_path = ROOT / "data" / "vector_db" / "legal_chunks_metadata.json"
        embedding_manifest_path = ROOT / "data" / "processed" / "legal_embeddings_manifest.json"
        chunks_path = ROOT / "data" / "processed" / "legal_chunks.json"
    retriever = LegalRetriever(
        index_path=index_path,
        vector_metadata_path=vector_metadata_path,
        embedding_manifest_path=embedding_manifest_path,
        chunks_path=chunks_path,
        device=args.device,
    )
    evaluated_retriever = _HybridAdapter(retriever) if args.mode == "hybrid" else retriever
    report = RetrievalEvaluator(
        retriever=evaluated_retriever, top_k=args.top_k
    ).evaluate(questions)
    report["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    report["dataset"] = str(args.questions)
    report["retrieval_mode"] = args.mode
    report["artifact_dir"] = str(args.artifact_dir or "production")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
