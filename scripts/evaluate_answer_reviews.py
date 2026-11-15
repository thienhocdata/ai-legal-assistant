from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation import AnswerQualityEvaluator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate completed human reviews of final answers."
    )
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    report = AnswerQualityEvaluator().evaluate(reviews)
    report["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    report["review_file"] = args.reviews.as_posix()
    report["label_source"] = "human_review"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
