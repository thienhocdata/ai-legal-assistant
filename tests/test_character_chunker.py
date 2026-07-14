from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.baseline_chunker import CharacterChunker


INPUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "luat_dat_dai_2024_normalized.txt"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "baseline_chunks.json"
)

DOCUMENT_ID = "luat_dat_dai_2024"

CHUNK_SIZE = 1000
OVERLAP_CHARS = 150


def test_character_chunker_unit() -> None:
    sample = (
        "A" * 1000
        + "B" * 1000
        + "C" * 500
    )

    chunker = CharacterChunker(
        chunk_size=1000,
        overlap_chars=150,
    )

    chunks = chunker.split_text(
        sample,
        document_id="sample",
        source_file="sample.txt",
    )

    assert len(chunks) == 3
    assert chunks[0]["start_char"] == 0
    assert chunks[1]["start_char"] == 850
    assert chunks[2]["start_char"] == 1700

    assert len(chunks[0]["text"]) == 1000
    assert len(chunks[1]["text"]) == 1000
    assert len(chunks[2]["text"]) == 800


def test_character_chunker_integration() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Chưa có file đầu vào: {INPUT_PATH}\n"
            "Hãy hoàn thành Module 3 trước."
        )

    chunker = CharacterChunker(
        chunk_size=CHUNK_SIZE,
        overlap_chars=OVERLAP_CHARS,
    )

    chunks = chunker.split_file(
        INPUT_PATH,
        document_id=DOCUMENT_ID,
    )

    stats = chunker.validate_chunks(chunks)

    assert stats["count"] > 0
    assert stats["longest_length"] <= CHUNK_SIZE
    assert chunks[0]["chunk_index"] == 1
    assert chunks[0]["chunk_type"] == "character"
    assert chunks[0]["document_id"] == DOCUMENT_ID


def main() -> None:
    chunker = CharacterChunker(
        chunk_size=CHUNK_SIZE,
        overlap_chars=OVERLAP_CHARS,
    )

    chunks = chunker.split_file(
        INPUT_PATH,
        document_id=DOCUMENT_ID,
    )

    stats = chunker.validate_chunks(chunks)
    output_path = chunker.write_json(
        chunks,
        OUTPUT_PATH,
    )

    print("=" * 80)
    print("MODULE 5 - BASELINE CHARACTER CHUNKER")
    print("=" * 80)
    print(f"Input file       : {INPUT_PATH}")
    print(f"Output file      : {output_path}")
    print(f"Chunk size       : {CHUNK_SIZE}")
    print(f"Overlap          : {OVERLAP_CHARS}")
    print(f"Chunks           : {stats['count']}")
    print(
        f"Average length   : "
        f"{stats['average_length']:.2f} chars"
    )
    print(
        f"Shortest length  : "
        f"{stats['shortest_length']} chars"
    )
    print(
        f"Longest length   : "
        f"{stats['longest_length']} chars"
    )
    print("Status           : SUCCESS")


if __name__ == "__main__":
    main()
