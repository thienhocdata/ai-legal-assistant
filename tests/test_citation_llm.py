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


def test_extractive_returns_multiple_evidence_without_question_or_instructions() -> None:
    prompt = (
        "CÂU HỎI: [1] không phải evidence\n\nCĂN CỨ TRUY XUẤT:\n"
        "[1] Văn bản - Điều 45: Điều kiện\nNội dung một.\n\n"
        "[2] Văn bản - Điều 133: Đăng ký\nNội dung hai.\n\n"
        "[3] Văn bản - Điều 220: Tách thửa\nNội dung ba.\n\n"
        "[4] Văn bản - Điều 159: Giá\nNội dung bốn.\n\n"
        "YÊU CẦU TRẢ LỜI:\nLời hướng dẫn riêng."
    )
    response = ExtractiveProvider().generate(system_prompt="", user_prompt=prompt)
    assert "Nội dung một." in response.text
    assert "Nội dung hai." in response.text
    assert "Nội dung ba." in response.text
    assert "Nội dung bốn." not in response.text
    assert "Lời hướng dẫn riêng." not in response.text
    assert "không phải evidence" not in response.text
    assert "Chưa kiểm tra hiệu lực" in response.text


def test_extractive_empty_context_does_not_invent_citation() -> None:
    response = ExtractiveProvider().generate(system_prompt="", user_prompt="Không có căn cứ")
    assert "[1]" not in response.text
