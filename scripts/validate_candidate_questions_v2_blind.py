"""Validate the blind V2 candidate retrieval set.

This checks structure and construction quotas only. Passing validation is not
independent expert or legal validation of the questions or article labels.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = REPO_ROOT / "data/evaluation/candidate_questions_v2_blind.json"
DEFAULT_CORPUS = REPO_ROOT / "data/processed/legal_chunks.json"

QUESTION_COUNT = 60
LABEL_STATUS = "ai_generated_candidate_pending_human_review"
QUESTION_TYPES = {
    "direct",
    "colloquial_paraphrase",
    "multi_condition",
    "ambiguous_refusal",
}
DIFFICULTIES = {"easy", "medium", "hard"}
BEHAVIORS = {"answer", "refuse"}
MINIMUM_QUOTAS = {
    "colloquial_paraphrase": 15,
    "multi_condition": 10,
    "ambiguous_refusal": 10,
}
QUESTION_KEYS = {
    "question_id",
    "question",
    "question_type",
    "difficulty",
    "expected_article_numbers",
    "expected_behavior",
    "label_status",
    "notes",
}


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate(dataset: Any, corpus: Any) -> tuple[list[str], Counter[str]]:
    errors: list[str] = []
    counts: Counter[str] = Counter()

    if not isinstance(dataset, dict):
        return ["Top level must be a JSON object."], counts

    metadata = dataset.get("dataset_metadata")
    questions = dataset.get("questions")
    if not isinstance(metadata, dict):
        errors.append("dataset_metadata must be an object.")
        metadata = {}
    if not isinstance(questions, list):
        return errors + ["questions must be an array."], counts

    if metadata.get("question_count") != QUESTION_COUNT:
        errors.append(f"dataset_metadata.question_count must be {QUESTION_COUNT}.")
    if metadata.get("independent_expert_validation") is not False:
        errors.append("independent_expert_validation must be false.")
    notice = metadata.get("review_notice")
    if not isinstance(notice, str) or "not independent expert validation" not in notice.lower():
        errors.append("review_notice must explicitly say this is not independent expert validation.")
    if len(questions) != QUESTION_COUNT:
        errors.append(f"Expected {QUESTION_COUNT} questions, found {len(questions)}.")

    if not isinstance(corpus, list):
        errors.append("Processed legal corpus must be an array.")
        available_articles: set[int] = set()
    else:
        available_articles = {
            row["article_no"]
            for row in corpus
            if isinstance(row, dict)
            and isinstance(row.get("article_no"), int)
            and not isinstance(row.get("article_no"), bool)
        }

    expected_ids = [f"V2Q{number:03d}" for number in range(1, QUESTION_COUNT + 1)]
    actual_ids: list[Any] = []
    normalized_questions: set[str] = set()

    for index, item in enumerate(questions, start=1):
        prefix = f"questions[{index - 1}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object.")
            continue

        missing = QUESTION_KEYS - item.keys()
        extra = item.keys() - QUESTION_KEYS
        if missing:
            errors.append(f"{prefix} missing fields: {sorted(missing)}.")
        if extra:
            errors.append(f"{prefix} has unexpected fields: {sorted(extra)}.")

        question_id = item.get("question_id")
        actual_ids.append(question_id)
        question = item.get("question")
        question_type = item.get("question_type")
        difficulty = item.get("difficulty")
        articles = item.get("expected_article_numbers")
        behavior = item.get("expected_behavior")

        if question_id != f"V2Q{index:03d}":
            errors.append(f"{prefix}.question_id must be V2Q{index:03d}.")
        if not isinstance(question, str) or not question.strip():
            errors.append(f"{prefix}.question must be a non-empty string.")
        else:
            normalized = " ".join(question.casefold().split())
            if normalized in normalized_questions:
                errors.append(f"{prefix}.question duplicates an earlier question.")
            normalized_questions.add(normalized)

        if question_type not in QUESTION_TYPES:
            errors.append(f"{prefix}.question_type is invalid: {question_type!r}.")
        else:
            counts[question_type] += 1
        if difficulty not in DIFFICULTIES:
            errors.append(f"{prefix}.difficulty is invalid: {difficulty!r}.")
        if behavior not in BEHAVIORS:
            errors.append(f"{prefix}.expected_behavior is invalid: {behavior!r}.")
        else:
            counts[behavior] += 1
        if item.get("label_status") != LABEL_STATUS:
            errors.append(f"{prefix}.label_status must be {LABEL_STATUS!r}.")
        if not isinstance(item.get("notes"), str) or not item["notes"].strip():
            errors.append(f"{prefix}.notes must be a non-empty string.")

        if not isinstance(articles, list):
            errors.append(f"{prefix}.expected_article_numbers must be an array.")
            continue
        if any(not isinstance(value, int) or isinstance(value, bool) for value in articles):
            errors.append(f"{prefix}.expected_article_numbers must contain integers only.")
            continue
        if articles != sorted(set(articles)):
            errors.append(f"{prefix}.expected_article_numbers must be sorted and unique.")
        unknown = set(articles) - available_articles
        if unknown:
            errors.append(f"{prefix} references articles absent from the corpus: {sorted(unknown)}.")
        if behavior == "answer" and not articles:
            errors.append(f"{prefix} expects an answer but has no article label.")
        if behavior == "refuse" and articles:
            errors.append(f"{prefix} expects refusal and must not preselect an article label.")
        if question_type == "ambiguous_refusal" and behavior != "refuse":
            errors.append(f"{prefix} is ambiguous_refusal but does not expect refusal.")
        if question_type != "ambiguous_refusal" and behavior == "refuse":
            errors.append(f"{prefix} expects refusal but is not ambiguous_refusal.")

    if actual_ids != expected_ids:
        errors.append("Question IDs must be unique and ordered from V2Q001 through V2Q060.")
    for question_type, minimum in MINIMUM_QUOTAS.items():
        if counts[question_type] < minimum:
            errors.append(
                f"Quota not met for {question_type}: {counts[question_type]} < {minimum}."
            )

    return errors, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    args = parser.parse_args()

    try:
        dataset = read_json(args.dataset)
        corpus = read_json(args.corpus)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAILED: {exc}")
        return 1

    errors, counts = validate(dataset, corpus)
    if errors:
        print(f"FAILED with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"PASS: {QUESTION_COUNT} candidate questions validated.")
    print(
        "Types: "
        + ", ".join(f"{name}={counts[name]}" for name in sorted(QUESTION_TYPES))
    )
    print(f"Behaviors: answer={counts['answer']}, refuse={counts['refuse']}")
    print("Scope: structural/quota validation only; not independent expert validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
