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
    return parser.parse_args()


class _HybridAdapter:
    def __init__(self, retriever: LegalRetriever) -> None:
        self.retriever = retriever

    def retrieve(self, question: str, *, top_k: int = 5):
        return self.retriever.retrieve_hybrid(question, top_k=top_k)


def main() -> None:
    args = parse_args()
    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    retriever = LegalRetriever(
        index_path=ROOT / "data" / "vector_db" / "legal_chunks.faiss",
        vector_metadata_path=ROOT / "data" / "vector_db" / "legal_chunks_metadata.json",
        embedding_manifest_path=ROOT / "data" / "processed" / "legal_embeddings_manifest.json",
        chunks_path=ROOT / "data" / "processed" / "legal_chunks.json",
        device=args.device,
    )
    evaluated_retriever = _HybridAdapter(retriever) if args.mode == "hybrid" else retriever
    report = RetrievalEvaluator(
        retriever=evaluated_retriever, top_k=args.top_k
    ).evaluate(questions)
    report["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    report["dataset"] = str(args.questions)
    report["retrieval_mode"] = args.mode
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
