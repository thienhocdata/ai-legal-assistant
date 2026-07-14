from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.chunk_validator import ChunkValidator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated chunks.")
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data" / "processed" / "legal_chunks.json",
    )
    parser.add_argument("--max-chars", type=int, default=5000)
    parser.add_argument("--text-field", default="clean_text")
    parser.add_argument("--legal", action="store_true", default=True)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validator = ChunkValidator(max_chars=args.max_chars, text_field=args.text_field)
    chunks = validator.load(args.input)
    report = validator.validate(chunks, require_legal_metadata=args.legal)
    data = report.to_dict()

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(json.dumps(data, ensure_ascii=False, indent=2))
    if not report.valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
