from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.concepts import (
    definition_clause,
    definition_term,
    parse_concept_request,
)
from app.rag.retriever import LegalRetriever


@pytest.mark.parametrize("question", [
    "đất đai là gì?",
    "hmm, đất đai là gì",
    "mình chỉ hỏi đất đai là gì thôi mà",
    "cho mình biết đất đai là gì với",
    "dat dai la gi?",
    "giải thích khái niệm đất đai",
    "Bạn giải thích đất đai là gì?",
    "Giải thích giúp mình khái niệm đất đai là gì?",
])
def test_ordinary_concept_variants(question: str) -> None:
    request = parse_concept_request(question)
    assert request is not None
    assert request.term == "đất đai"
    assert not request.statutory


@pytest.mark.parametrize("question", [
    "Theo Luật Đất đai, thửa đất là gì?",
    "Thửa đất là gì theo pháp luật?",
    "Định nghĩa pháp lý của thửa đất là gì?",
])
def test_explicit_statutory_definition(question: str) -> None:
    request = parse_concept_request(question)
    assert request is not None
    assert request.term.casefold() == "thửa đất"
    assert request.statutory


@pytest.mark.parametrize("question", [
    "Đất đai là gì theo pháp luật vậy?",
    "Đất đai là gì theo Luật Đất đai 2024?",
    "Đất đai là gì theo Luật Đất đai 2024 vậy?",
    "Đất đai là gì vậy theo pháp luật?",
])
def test_bounded_legal_and_polite_suffixes_in_either_order(question: str) -> None:
    request = parse_concept_request(question)
    assert request is not None
    assert request.term.casefold() == "đất đai"
    assert request.statutory
    assert request.explicit_definition


@pytest.mark.parametrize("question", [
    "Điều kiện chuyển nhượng đất là gì?",
    "Thủ tục cấp giấy chứng nhận là gì?",
    "Các nguyên tắc bồi thường, hỗ trợ và tái định cư khi Nhà nước thu hồi đất là gì?",
    "Nguyên tắc định giá đất là gì?",
    "Trình tự thu hồi đất là gì?",
    "Nghĩa vụ của người sử dụng đất là gì?",
    "Những trường hợp Nhà nước thu hồi đất là gì?",
    "Hồ sơ để được chuyển nhượng đất là gì?",
    "Cần làm gì để bán đất?",
    "Cần giấy tờ gì để chuyển nhượng là gì?",
    "Được cấp sổ đất là gì?",
    "Giá đất ở tỉnh tôi bao nhiêu?",
    "Thửa đất là gì và giá đất là gì?",
    "Thửa đất là gì, có bán được không?",
    "Giải thích thửa đất; đất này có được bán không?",
    "Giải thích thửa đất nếu đang có tranh chấp",
    "Giải thích việc thu hồi đất nhà tôi",
    "Giải thích đất của tôi đang bị thu hồi",
    "Giải thích thửa đất này",
    "Giải thích thua dat nay",
    "Giải thích miếng đất đó",
    "Giải thích đất đang bị thu hồi",
    "Giải thích trường hợp thu hồi đất",
    "Thửa đất này là gì?",
    "Đất chưa có sổ có bán được không?",
    "sao bạn trả lời thô quá v",
    "mình không",
    "",
])
def test_substantive_or_mixed_request_not_replaced_by_definition(question: str) -> None:
    assert parse_concept_request(question) is None


@pytest.mark.parametrize("question,explicit", [
    ("Giải thích thửa đất", False),
    ("Giải thích đất đang có tranh chấp", False),
    ("Giải thích khái niệm đất đang có tranh chấp", True),
    ("Định nghĩa đất đang có tranh chấp", True),
    ("Đất đang có tranh chấp là gì?", True),
    ("Giải thích một nội dung chưa biết", False),
])
def test_bare_explanation_can_fall_through_without_losing_source_terms(
    question: str, explicit: bool,
) -> None:
    request = parse_concept_request(question)
    assert request is not None
    assert request.explicit_definition is explicit


@pytest.mark.parametrize("question", [
    "Đất đai là gì theo pháp luật và tôi có được bán không?",
    "Đất đai là gì theo Luật Đất đai 2024 ở tỉnh tôi?",
])
def test_legal_suffix_does_not_swallow_following_case_question(question: str) -> None:
    assert parse_concept_request(question) is None


def test_alias_question_keeps_canonical_term_for_source_lookup() -> None:
    request = parse_concept_request("sổ đỏ là gì?")
    assert request is not None
    assert request.term == "Giấy chứng nhận quyền sử dụng đất"


def test_complete_definition_keeps_conditions_and_tail() -> None:
    clause = "7. Thuật ngữ mẫu là nội dung có điều kiện. Ngoại lệ: không áp dụng cho X."
    source = "Chương I. QUY ĐỊNH CHUNG\nĐiều 3. Giải thích từ ngữ\n" + clause
    assert definition_clause(source) == clause
    assert definition_term(source) == "Thuật ngữ mẫu"
    assert definition_clause("Điều 12. Sở hữu đất đai\nNội dung khác.") is None
    assert definition_clause("Điều 3. Giải thích từ ngữ\n1. A là X.\n2. B là Y.") is None


@pytest.fixture
def source_retriever() -> LegalRetriever:
    """Real source chunks, but no model, FAISS or embedding initialization."""
    chunks = json.loads((ROOT / "data/processed/legal_chunks.json").read_text(encoding="utf-8"))
    retriever = LegalRetriever(
        index_path=ROOT / "not-loaded.faiss",
        vector_metadata_path=ROOT / "not-loaded-metadata.json",
        embedding_manifest_path=ROOT / "not-loaded-manifest.json",
        chunks_path=ROOT / "not-loaded-chunks.json",
    )
    retriever._loaded = True
    retriever._chunks_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    return retriever


@pytest.mark.parametrize("term,clause_no", [
    ("thửa đất", 42),
    ("thua dat", 42),
    ("giá đất", 19),
    ("tranh chấp đất đai", 47),
    ("Giấy chứng nhận", 21),
    ("sổ đỏ", 21),
    ("thu hồi đất", 35),
    ("Nhà nước giao đất", 34),
    ("cho thuê đất", 32),
])
def test_exact_lookup_uses_complete_source_and_no_fake_dense_score(
    source_retriever: LegalRetriever, term: str, clause_no: int,
) -> None:
    result = source_retriever.lookup_definition(term)
    assert result is not None
    assert result["article_title"] == "Giải thích từ ngữ"
    assert result["clause_nos"] == [clause_no]
    assert result["retrieval_method"] == "exact_definition"
    assert result["score"] == 0.0
    assert "dense_score" not in result
    original = source_retriever._chunks_by_id[result["chunk_id"]]
    assert result["text"] == original["text"]
    assert result["clean_text"] == original["clean_text"]
    assert source_retriever._embedder is None


@pytest.mark.parametrize("term", ["đất đai", "thuật ngữ không tồn tại", "", "đất", "sổ"])
def test_missing_or_ambiguous_terms_do_not_use_nearest_unrelated_article(
    source_retriever: LegalRetriever, term: str,
) -> None:
    assert source_retriever.lookup_definition(term) is None


def test_duplicate_source_definition_does_not_silently_choose_one(
    source_retriever: LegalRetriever,
) -> None:
    original = source_retriever.lookup_definition("thửa đất")
    assert original is not None
    duplicate = {**original, "chunk_id": "ambiguous-other-source", "document_id": "other-law"}
    source_retriever._chunks_by_id[duplicate["chunk_id"]] = duplicate
    assert source_retriever.lookup_definition("thửa đất") is None


def test_source_term_with_parenthetical_short_name_is_complete() -> None:
    source = (
        "Điều 3. Giải thích từ ngữ\n32. Nhà nước cho thuê quyền sử dụng đất "
        "(sau đây gọi là Nhà nước cho thuê đất) là việc cơ quan có thẩm quyền ban hành quyết định."
    )
    assert definition_term(source) == "Nhà nước cho thuê quyền sử dụng đất"
