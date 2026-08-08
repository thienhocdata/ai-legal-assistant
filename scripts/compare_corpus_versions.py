from __future__ import annotations

import argparse
from collections import defaultdict
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTION = ROOT / "data" / "processed" / "legal_chunks.json"
DEFAULT_EXPERIMENT = (
    ROOT
    / "data"
    / "experiments"
    / "vbhn_133_2025_luat_dat_dai"
    / "legal_chunks.json"
)
DEFAULT_OUTPUT = DEFAULT_EXPERIMENT.parent / "corpus_comparison.json"
DEFAULT_QUESTIONS_OUTPUT = DEFAULT_EXPERIMENT.parent / "changed_article_questions.json"
ARTICLE_HEADER = re.compile(r"^Điều\s+\d+[a-zA-Z]?\s*\.\s*[^\n]*\s*", re.IGNORECASE)


def _load_chunks(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"Expected a JSON list: {path}")
    return value


def group_articles(chunks: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        grouped[int(chunk["article_no"])].append(chunk)

    articles: dict[int, dict[str, Any]] = {}
    for article_no, rows in grouped.items():
        ordered = sorted(rows, key=lambda row: int(row.get("chunk_index", 0)))
        text_parts = []
        for row in ordered:
            text = str(row.get("text") or row.get("clean_text") or "").strip()
            text_parts.append(ARTICLE_HEADER.sub("", text, count=1).strip())
        normalized = re.sub(r"\s+", " ", " ".join(text_parts)).strip()
        articles[article_no] = {
            "title": str(ordered[0].get("article_title", "")),
            "text": normalized,
            "sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "chunk_count": len(ordered),
        }
    return articles


def compare_articles(
    production: dict[int, dict[str, Any]],
    experiment: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    production_numbers = set(production)
    experiment_numbers = set(experiment)
    common = sorted(production_numbers & experiment_numbers)
    changed: list[dict[str, Any]] = []
    unchanged: list[int] = []
    for article_no in common:
        old = production[article_no]
        new = experiment[article_no]
        title_changed = old["title"] != new["title"]
        text_changed = old["sha256"] != new["sha256"]
        if title_changed or text_changed:
            changed.append(
                {
                    "article_no": article_no,
                    "production_title": old["title"],
                    "experimental_title": new["title"],
                    "title_changed": title_changed,
                    "text_changed": text_changed,
                    "similarity": round(
                        SequenceMatcher(None, old["text"], new["text"]).ratio(), 6
                    ),
                    "production_chars": len(old["text"]),
                    "experimental_chars": len(new["text"]),
                    "production_chunks": old["chunk_count"],
                    "experimental_chunks": new["chunk_count"],
                }
            )
        else:
            unchanged.append(article_no)

    changed.sort(key=lambda item: (item["similarity"], item["article_no"]))
    return {
        "production_article_count": len(production),
        "experimental_article_count": len(experiment),
        "common_article_count": len(common),
        "unchanged_article_count": len(unchanged),
        "changed_article_count": len(changed),
        "missing_from_experiment": sorted(production_numbers - experiment_numbers),
        "new_in_experiment": sorted(experiment_numbers - production_numbers),
        "changed_articles": changed,
        "notes": (
            "Text is grouped from legal chunks and whitespace-normalized. "
            "This is a technical diff, not a legal-effect determination."
        ),
    }


def build_changed_article_questions(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "question_id": f"DIFF{item['article_no']:03d}",
            "question": (
                f"Điều {item['article_no']} quy định gì về "
                f"{item['experimental_title'].rstrip('.')}?"
            ),
            "question_type": "changed_article_title_lookup",
            "difficulty": "medium",
            "expected_article_numbers": [item["article_no"]],
            "expected_clause_numbers": [],
            "expected_point_numbers": [],
            "requires_clarification": False,
            "notes": "Generated from technical corpus diff; requires legal review.",
        }
        for item in sorted(report["changed_articles"], key=lambda row: row["article_no"])
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare production and experimental corpora by article.")
    parser.add_argument("--production", type=Path, default=DEFAULT_PRODUCTION)
    parser.add_argument("--experiment", type=Path, default=DEFAULT_EXPERIMENT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--questions-output", type=Path, default=DEFAULT_QUESTIONS_OUTPUT
    )
    args = parser.parse_args()

    report = compare_articles(
        group_articles(_load_chunks(args.production)),
        group_articles(_load_chunks(args.experiment)),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.questions_output.parent.mkdir(parents=True, exist_ok=True)
    args.questions_output.write_text(
        json.dumps(build_changed_article_questions(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key != "changed_articles"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
