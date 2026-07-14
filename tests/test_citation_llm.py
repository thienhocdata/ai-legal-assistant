from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.citation import CitationEngine
from app.llm_provider import ExtractiveProvider


def test_citation_context_and_offline_provider() -> None:
    results = [
        {
            "chunk_id": "c1",
            "document_id": "doc",
            "document_name": "Luật mẫu",
            "article_no": 45,
            "article_title": "Điều kiện chuyển nhượng",
            "clause_nos": [1],
            "point_nos": ["a"],
            "text": "Nội dung căn cứ pháp luật.",
            "score": 0.9,
        }
    ]
    engine = CitationEngine()
    citations = engine.build(results)
    context = engine.format_context(citations)
    response = ExtractiveProvider().generate(system_prompt="", user_prompt=context)
    assert citations[0].citation_id == "[1]"
    assert "Điều 45" in context
    assert "[1]" in response.text


def main() -> None:
    test_citation_context_and_offline_provider()
    print("MODULE 13 - CITATION & LLM PROVIDER: SUCCESS")


if __name__ == "__main__":
    main()
