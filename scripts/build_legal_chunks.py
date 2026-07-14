from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.chunker import LegalChunker


INPUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "luat_dat_dai_2024.json"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_chunks.json"
)

MAX_CHARS = 5000
OVERLAP_CHARS = 200


def main() -> None:
    chunker = LegalChunker(
        max_chars=MAX_CHARS,
        overlap_chars=OVERLAP_CHARS,
    )

    document = chunker.load_legal_tree(
        INPUT_PATH
    )
    chunks = chunker.build_chunks(document)
    stats = chunker.validate_chunks(
        document,
        chunks,
    )

    output_path = chunker.write_json(
        chunks,
        OUTPUT_PATH,
    )

    print("=" * 80)
    print("MODULE 6 - LEGAL CHUNKER FINAL")
    print("=" * 80)
    print(f"Input file       : {INPUT_PATH}")
    print(f"Output file      : {output_path}")
    print(f"Max chars        : {MAX_CHARS}")
    print(f"Overlap          : {OVERLAP_CHARS}")
    print(f"Articles covered : {stats['articles']}")
    print(f"Chunks           : {stats['chunks']}")
    print(f"Oversized chunks : {stats['oversized_chunks']}")
    print(f"Empty chunks     : {stats['empty_chunks']}")
    print(f"Duplicate IDs    : {stats['duplicate_ids']}")
    print(f"Average length   : {stats['average_length']:.2f}")
    print(f"Shortest length  : {stats['shortest_length']}")
    print(f"Longest length   : {stats['longest_length']}")
    print(f"Strategies       : {stats['strategies']}")
    print("Status           : SUCCESS")


if __name__ == "__main__":
    main()
