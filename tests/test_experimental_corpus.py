from __future__ import annotations

from pathlib import Path

import pytest

from app.kb.legal_parser import LegalStructureParser
from scripts.run_experimental_corpus import ROOT, _safe_output_dir


def test_parser_supports_versioned_document_identity() -> None:
    parser = LegalStructureParser(
        document_id="test_consolidated_law",
        document_number="TEST/VBHN",
        document_name="Test consolidated law",
        document_type="Văn bản hợp nhất",
        expected_articles=1,
    )
    document = parser.parse_text(
        "Chương I\nQUY ĐỊNH CHUNG\nĐiều 1. Phạm vi\nNội dung.",
        source_file="test.pdf",
    )

    assert document.document_id == "test_consolidated_law"
    assert document.document_number == "TEST/VBHN"
    assert parser.validate(document)["articles"] == 1


def test_experimental_output_cannot_replace_production() -> None:
    with pytest.raises(ValueError):
        _safe_output_dir(ROOT / "data" / "processed")
    with pytest.raises(ValueError):
        _safe_output_dir(ROOT / "data" / "vector_db")

    safe = _safe_output_dir(Path("data/experiments/example"))
    assert safe == (ROOT / "data" / "experiments" / "example").resolve()


def test_sequence_guard_skips_quoted_articles_from_amending_laws() -> None:
    parser = LegalStructureParser(expected_articles=2, enforce_article_sequence=True)
    document = parser.parse_text(
        "\n".join(
            [
                "Chương I",
                "QUY ĐỊNH CHUNG",
                "Điều 1. Điều chính",
                "1. Nội dung chính.",
                "Điều 50. Điều được trích trong chú thích",
                "1. Nội dung chú thích phải bỏ qua.",
                "Điều 2. Điều chính tiếp theo",
                "1. Nội dung tiếp theo.",
            ]
        ),
        source_file="test.pdf",
    )

    articles = parser.collect_articles(document)
    assert [article.article_no for article in articles] == ["1", "2"]
    assert "chú thích" not in articles[0].clauses[0].clause_text
