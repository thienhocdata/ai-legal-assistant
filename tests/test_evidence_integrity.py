from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.citation import CitationEngine
from app.guardrails import GuardrailEngine
from app.llm_provider import ExtractiveProvider


def _result(index: int = 1, text: str = "Nội dung căn cứ giữ nguyên.") -> dict:
    return {
        "chunk_id": f"chunk-{index}",
        "document_id": "test-law",
        "document_name": "Văn bản kiểm thử",
        "article_no": index,
        "article_title": f"Điều kiện {index}",
        "clause_nos": [1, 2],
        "point_nos": [],
        "text": text,
        "score": .9,
    }


def test_full_quote_retains_tail_condition_and_integrity_metadata() -> None:
    text = "Điều kiện áp dụng. " * 100 + "Ngoại lệ cuối: không áp dụng trong trường hợp X."
    assert len(text) > 1600
    citation = CitationEngine().build([_result(text=text)])[0]
    assert citation.quote == text
    assert citation.quote.endswith("Ngoại lệ cuối: không áp dụng trong trường hợp X.")
    assert citation.source_quote_chars == len(text)
    assert citation.quote_sha256 == sha256(text.encode("utf-8")).hexdigest()
    assert citation.quote_truncated is False
    response = ExtractiveProvider().generate(
        system_prompt="", user_prompt=CitationEngine.format_context([citation])
    )
    assert text in response.text
    assert GuardrailEngine().check_grounded_output(response.text, [citation], extractive=True).allowed


def test_explicit_quote_budget_fails_instead_of_silently_truncating() -> None:
    with pytest.raises(ValueError, match="không cắt ngầm"):
        CitationEngine(max_quote_chars=1600).build([_result(text="a" * 1700)])


@pytest.mark.parametrize("limit", [1, 2, 3, 4, 5])
def test_canonical_extractive_output_matches_provider_and_passes_exact_check(limit: int) -> None:
    engine = CitationEngine()
    citations = engine.build([_result(index) for index in range(1, 6)])
    response = ExtractiveProvider(max_evidence_blocks=limit).generate(
        system_prompt="", user_prompt=engine.format_context(citations)
    )
    assert response.text == engine.format_extractive_answer(citations, max_evidence_blocks=limit)
    decision = GuardrailEngine().check_grounded_output(response.text, citations, extractive=True)
    assert decision.allowed
    assert decision.code == "exact_extractive_evidence"
    assert decision.semantic_support_verified is False


def test_valid_marker_cannot_hide_added_unsupported_extractive_claim() -> None:
    citations = CitationEngine().build([_result()])
    valid = CitationEngine.format_extractive_answer(citations)
    decision = GuardrailEngine().check_grounded_output(
        valid + "\nMột nhận định không có trong đoạn trích [1].", citations, extractive=True
    )
    assert not decision.allowed
    assert decision.code == "extractive_content_mismatch"


def test_quote_mutation_is_detected_before_output_is_accepted() -> None:
    citations = CitationEngine().build([_result()])
    citations[0].quote += " Nội dung bị thay đổi."
    modified = CitationEngine.format_extractive_answer(citations)
    decision = GuardrailEngine().check_grounded_output(modified, citations, extractive=True)
    assert not decision.allowed
    assert decision.code == "citation_integrity_mismatch"


def test_edited_extractive_quote_is_rejected_even_with_valid_citation_number() -> None:
    citations = CitationEngine().build([_result()])
    modified = CitationEngine.format_extractive_answer(citations).replace(
        "Nội dung căn cứ giữ nguyên.", "Nội dung khác."
    )
    decision = GuardrailEngine().check_grounded_output(modified, citations, extractive=True)
    assert not decision.allowed
    assert decision.code == "extractive_content_mismatch"


def test_hosted_marker_check_explicitly_does_not_claim_semantic_verification() -> None:
    citations = CitationEngine().build([_result()])
    decision = GuardrailEngine().check_grounded_output("Một nhận định chưa được chấm nội dung [1].", citations)
    assert decision.allowed
    assert decision.code == "citation_structure_only"
    assert decision.validation_scope == "citation_labels_and_quote_integrity_only"
    assert decision.semantic_support_verified is False
    invalid = GuardrailEngine().check_grounded_output("Nội dung [2].", citations)
    assert not invalid.allowed
    assert invalid.code == "invalid_citation"


def test_no_empty_quote_can_pass_as_evidence() -> None:
    citations = CitationEngine().build([_result(text="")])
    decision = GuardrailEngine().check_grounded_output("Nội dung [1]", citations)
    assert not decision.allowed
    assert decision.code == "citation_integrity_mismatch"
