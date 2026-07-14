from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.chunker import LegalChunker


TREE_PATH = (
    ROOT
    / "data"
    / "processed"
    / "luat_dat_dai_2024.json"
)

CHUNKS_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_chunks.json"
)

MAX_CHARS = 5000
OVERLAP_CHARS = 200


def test_article_to_clause_to_point_fallback() -> None:
    document = {
        "document_id": "sample_law",
        "document_name": "Luật mẫu",
        "document_number": "01/2026/QH",
        "document_type": "Luật",
        "source_file": "sample.json",
        "chapters": [
            {
                "chapter_no": "I",
                "chapter_title": "QUY ĐỊNH CHUNG",
                "articles": [
                    {
                        "article_no": "1",
                        "article_title": "Phạm vi điều chỉnh",
                        "article_text": "",
                        "clauses": [
                            {
                                "clause_no": "1",
                                "clause_text": "Nội dung ngắn.",
                                "points": [],
                            },
                            {
                                "clause_no": "2",
                                "clause_text": "Khoản dài.",
                                "points": [
                                    {
                                        "point_no": "a",
                                        "point_text": "A" * 1800,
                                    },
                                    {
                                        "point_no": "b",
                                        "point_text": "B" * 1800,
                                    },
                                ],
                            },
                        ],
                    }
                ],
                "sections": [],
            }
        ],
    }

    chunker = LegalChunker(
        max_chars=1200,
        overlap_chars=100,
    )

    chunks = chunker.build_chunks(document)
    stats = chunker.validate_chunks(
        document,
        chunks,
    )

    assert stats["articles"] == 1
    assert stats["chunks"] >= 3
    assert stats["longest_length"] <= 1200
    assert all(
        chunk["clean_text"]
        for chunk in chunks
    )


def test_real_legal_tree() -> None:
    if not TREE_PATH.exists():
        raise FileNotFoundError(
            f"Chưa có legal tree: {TREE_PATH}"
        )

    chunker = LegalChunker(
        max_chars=MAX_CHARS,
        overlap_chars=OVERLAP_CHARS,
    )

    document = chunker.load_legal_tree(
        TREE_PATH
    )
    chunks = chunker.build_chunks(document)
    stats = chunker.validate_chunks(
        document,
        chunks,
    )

    assert stats["articles"] == 260
    assert stats["oversized_chunks"] == 0
    assert stats["empty_chunks"] == 0
    assert stats["duplicate_ids"] == 0
    assert stats["longest_length"] <= MAX_CHARS


def main() -> None:
    if not TREE_PATH.exists():
        raise FileNotFoundError(
            f"Chưa có legal tree: {TREE_PATH}"
        )

    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"Chưa có legal chunks: {CHUNKS_PATH}\n"
            "Chạy trước: "
            "python scripts\\build_legal_chunks.py"
        )

    document = LegalChunker.load_legal_tree(
        TREE_PATH
    )

    chunks = json.loads(
        CHUNKS_PATH.read_text(encoding="utf-8")
    )

    stats = LegalChunker(
        max_chars=MAX_CHARS,
        overlap_chars=OVERLAP_CHARS,
    ).validate_chunks(
        document,
        chunks,
    )

    print("=" * 80)
    print("MODULE 6 - FINAL VALIDATION")
    print("=" * 80)
    print(f"Articles covered : {stats['articles']}")
    print(f"Chunks           : {stats['chunks']}")
    print(f"Oversized chunks : {stats['oversized_chunks']}")
    print(f"Empty chunks     : {stats['empty_chunks']}")
    print(f"Duplicate IDs    : {stats['duplicate_ids']}")
    print(f"Longest length   : {stats['longest_length']}")
    print(f"Strategies       : {stats['strategies']}")
    print("Status           : SUCCESS")


if __name__ == "__main__":
    main()
