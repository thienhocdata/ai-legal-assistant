from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.chunk_validator import ChunkValidator


CHUNKS_PATH = ROOT / "data" / "processed" / "legal_chunks.json"


def test_validator_detects_duplicate_and_oversized_chunks() -> None:
    chunks = [
        {
            "chunk_id": "a",
            "document_id": "doc",
            "clean_text": "valid",
            "article_no": 1,
            "article_title": "Title",
            "strategy": "article",
        },
        {
            "chunk_id": "a",
            "document_id": "doc",
            "clean_text": "x" * 11,
            "article_no": 1,
            "article_title": "Title",
            "strategy": "article",
        },
    ]
    report = ChunkValidator(max_chars=10).validate(
        chunks, require_legal_metadata=True
    )
    assert not report.valid
    assert report.duplicate_ids == ["a"]
    assert report.oversized_chunks == ["a"]


def test_generated_legal_chunks_are_valid() -> None:
    validator = ChunkValidator(max_chars=5000)
    report = validator.validate(
        validator.load(CHUNKS_PATH), require_legal_metadata=True
    )
    assert report.valid
    assert report.chunk_count == 441


def main() -> None:
    test_validator_detects_duplicate_and_oversized_chunks()
    test_generated_legal_chunks_are_valid()
    print("MODULE 7 - CHUNK VALIDATOR: SUCCESS")


if __name__ == "__main__":
    main()
