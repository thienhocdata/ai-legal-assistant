"""Compare retrieval experiments on observed development datasets only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agent import QueryAnalyzer
from app.evaluation.dataset_loader import extract_questions
from app.rag.ranking import bm25_rrf_scores, diverse_article_rows
from app.rag.retriever import LegalRetriever
from scripts.evaluate_system_behavior import _artifact_fingerprint, _fingerprint_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    evaluation_dir = ROOT / "data" / "evaluation"
    if evaluation_dir not in output.parents:
        raise ValueError("Output must be under data/evaluation/.")
    if output.exists():
        raise FileExistsError("Use a new output path.")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--", "app", "scripts", "requirements.txt",
         "data/processed", "data/vector_db"], cwd=ROOT, text=True,
    ).strip()
    if args.require_clean and dirty:
        raise RuntimeError("Benchmark requires clean source/artifact checkout.")
    fingerprint_paths = [*_fingerprint_paths(), Path(__file__).resolve()]
    fingerprints_before = [_artifact_fingerprint(path) for path in fingerprint_paths]
    retriever = LegalRetriever(
        index_path=ROOT / "data/vector_db/legal_chunks.faiss",
        vector_metadata_path=ROOT / "data/vector_db/legal_chunks_metadata.json",
        embedding_manifest_path=ROOT / "data/processed/legal_embeddings_manifest.json",
        chunks_path=ROOT / "data/processed/legal_chunks.json",
    )
    retriever.load()
    analyzer = QueryAnalyzer()
    datasets = []
    for filename in ("test_questions_v1.json", "candidate_questions_v2_blind.json"):
        path = evaluation_dir / filename
        raw = path.read_bytes()
        questions, _ = extract_questions(json.loads(raw.decode("utf-8")))
        questions = [row for row in questions if row.get("expected_behavior", "answer") == "answer"]
        variants = {key: [] for key in ("baseline", "article_diverse", "bm25_rrf", "bm25_rrf_diverse")}
        for item in questions:
            query = analyzer.analyze(item["question"]).rewritten_question
            all_results = retriever.retrieve_hybrid(
                query, top_k=len(retriever._chunks_by_id), diversify_articles=False
            )
            rows = [(row["score"], row["dense_score"], row["lexical_score"], row) for row in all_results]
            scores = bm25_rrf_scores(query, rows, retriever._tokens)
            rrf = sorted(
                [(scores[row[3]["chunk_id"]], row[1], row[2], row[3]) for row in rows],
                key=lambda row: (row[0], row[1]), reverse=True,
            )
            selected = {
                "baseline": rows[:5], "article_diverse": diverse_article_rows(rows, 5),
                "bm25_rrf": rrf[:5], "bm25_rrf_diverse": diverse_article_rows(rrf, 5),
            }
            expected = set(item["expected_article_numbers"])
            for name, matches in selected.items():
                articles = [row[3]["article_no"] for row in matches]
                ranks = [rank for rank, article in enumerate(articles, 1) if article in expected]
                variants[name].append({
                    "question_id": item["question_id"], "rewritten_query": query,
                    "expected_articles": sorted(expected), "articles": articles,
                    "chunk_ids": [row[3]["chunk_id"] for row in matches],
                    "hit_at_1": bool(ranks and ranks[0] == 1), "hit_at_5": bool(ranks),
                    "reciprocal_rank": 1 / ranks[0] if ranks else 0,
                })
        datasets.append({
            "dataset": filename, "sha256": sha256(raw).hexdigest(),
            "role": "observed_development_not_independent_validation",
            "question_count": len(questions),
            "variants": {name: {
                "hit_at_1": sum(row["hit_at_1"] for row in rows) / len(rows),
                "hit_at_5": sum(row["hit_at_5"] for row in rows) / len(rows),
                "mrr": sum(row["reciprocal_rank"] for row in rows) / len(rows),
                "rows": rows,
            } for name, rows in variants.items()},
        })
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "warning": "Development comparison. No new independent/generalization claim. Routing bypassed for ranking isolation.",
        "source_worktree_dirty": bool(dirty),
        "source_worktree_status": dirty.splitlines(),
        "require_clean_enforced": args.require_clean,
        "config": {"top_k": 5, "lexical_weight": 0.35, "rrf_k": 60,
                   "rrf_term_frequency": "binary_presence", "query_rewrite": True},
        "source_artifact_fingerprints": fingerprints_before,
        "datasets": datasets,
    }
    if fingerprints_before != [_artifact_fingerprint(path) for path in fingerprint_paths]:
        raise RuntimeError("Source/artifact changed during benchmark; refusing mixed report.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps([{**{k: v for k, v in dataset.items() if k != "variants"},
                       "variants": {name: {k: v for k, v in values.items() if k != "rows"}
                                    for name, values in dataset["variants"].items()}}
                      for dataset in datasets], indent=2))


if __name__ == "__main__":
    main()
