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

from app.evaluation.dataset_loader import extract_questions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze an evaluation dataset against an existing baseline commit."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _resolve_inside_repository(path: Path) -> Path:
    resolved = path if path.is_absolute() else ROOT / path
    resolved = resolved.resolve()
    if resolved != ROOT.resolve() and ROOT.resolve() not in resolved.parents:
        raise ValueError("Đường dẫn phải nằm trong repository.")
    return resolved


def _validate_baseline_commit(value: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{value}^{{commit}}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_manifest(dataset_path: Path, baseline_commit: str) -> dict:
    raw = dataset_path.read_bytes()
    questions, dataset_metadata = extract_questions(json.loads(raw.decode("utf-8")))
    ids: list[str] = []
    label_statuses: dict[str, int] = {}
    expected_behaviors: dict[str, int] = {}
    for index, row in enumerate(questions):
        if not isinstance(row, dict):
            raise ValueError(f"Dòng {index} phải là JSON object.")
        question_id = str(row.get("question_id", "")).strip()
        question = str(row.get("question", "")).strip()
        if not question_id or not question:
            raise ValueError(f"Dòng {index} thiếu question_id hoặc question.")
        ids.append(question_id)
        label_status = str(row.get("label_status", "unspecified"))
        label_statuses[label_status] = label_statuses.get(label_status, 0) + 1
        behavior = str(row.get("expected_behavior", "unspecified"))
        expected_behaviors[behavior] = expected_behaviors.get(behavior, 0) + 1
    if len(ids) != len(set(ids)):
        raise ValueError("Evaluation dataset có question_id trùng.")
    return {
        "dataset": dataset_path.relative_to(ROOT).as_posix(),
        "dataset_sha256": sha256(raw).hexdigest(),
        "question_count": len(questions),
        "baseline_commit": _validate_baseline_commit(baseline_commit),
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "label_status_counts": label_statuses,
        "expected_behavior_counts": expected_behaviors,
        "dataset_metadata": dataset_metadata,
        "policy": (
            "Do not tune retrieval/query rules on this dataset after inspecting its results. "
            "Any label correction requires a new dataset version and manifest. Freezing alone "
            "does not make the dataset independent expert-held-out evaluation."
        ),
        "independence_warning": (
            "A frozen AI-generated candidate set is post-baseline but is not independent "
            "expert validation."
        ),
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    dataset_path = _resolve_inside_repository(args.dataset)
    output_path = _resolve_inside_repository(args.output)
    if output_path.exists():
        raise FileExistsError(
            "Freeze manifest đã tồn tại; tạo version mới thay vì ghi đè."
        )
    manifest = build_manifest(dataset_path, args.baseline_commit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
