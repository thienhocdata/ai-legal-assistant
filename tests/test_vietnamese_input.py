from __future__ import annotations

import json
from pathlib import Path
import unicodedata

import pytest

from app.agent import ClarificationEngine, QueryAnalyzer
from app.agent.query_understanding import QueryRewriter, fold_vietnamese


@pytest.mark.parametrize(
    ("accented", "unaccented"),
    [
        ("Tôi muốn tách thửa đất", "Toi muon tach thua dat"),
        ("Điều kiện chuyển nhượng quyền sử dụng đất là gì?",
         "Dieu kien chuyen nhuong quyen su dung dat la gi?"),
        ("Thuế thu nhập cá nhân khi bán đất tính ra sao?",
         "Thue thu nhap ca nhan khi ban dat tinh ra sao?"),
        ("Quy hoạch khu này còn hiệu lực không?",
         "Quy hoach khu nay con hieu luc khong?"),
        ("Tôi chuyển đất được không?", "Toi chuyen dat duoc khong?"),
        ("Miếng đất này có làm sổ được không?", "Mieng dat nay co lam so duoc khong?"),
        ("Bảng giá đất áp dụng cho nghĩa vụ tài chính gì?",
         "Bang gia dat ap dung cho nghia vu tai chinh gi?"),
        ("Sang tên đất cần mẫu đơn nào?", "Sang ten dat can mau don nao?"),
        ("Thu hồi đất thì đền bao nhiêu tiền?", "Thu hoi dat thi den bao nhieu tien?"),
    ],
)
def test_unaccented_routing_matches_accented_case(accented: str, unaccented: str) -> None:
    analyzer = QueryAnalyzer()
    left = analyzer.analyze(accented)
    right = analyzer.analyze(unaccented)
    engine = ClarificationEngine()
    assert engine.clarify(right).status == engine.clarify(left).status
    assert right.in_scope == left.in_scope
    assert right.intent == left.intent
    assert right.missing_source_types == left.missing_source_types
    assert right.missing_context_types == left.missing_context_types
    assert right.original_question == unaccented


def test_rewrite_restores_bounded_legal_phrases_not_entire_sentence() -> None:
    analysis = QueryAnalyzer().analyze("Toi muon tach thua dat")
    assert analysis.original_question == "Toi muon tach thua dat"
    assert analysis.rewritten_question == "Toi muon tách thửa đất"
    assert analysis.intent == "parcel"
    assert ClarificationEngine().clarify(analysis).status == "ready"


def test_unaccented_article_clause_and_point_references() -> None:
    analysis = QueryAnalyzer().analyze("Tra cuu dieu 45 khoan 1 diem d")
    assert analysis.article_refs == [45]
    assert analysis.clause_refs == [1]
    # d and đ are distinct legal point identifiers; never guess đ from ASCII d.
    assert analysis.point_refs == ["d"]
    assert "Điều 45 Khoản 1 Điểm d" in analysis.rewritten_question


@pytest.mark.parametrize(
    "question",
    ["So do to chuc cong ty", "Sơ đồ tổ chức công ty", "Toi thua tran bong",
     "Dat la ten cua toi", "Database server monitoring", "Sang ten xe may"],
)
def test_ambiguous_words_and_unrelated_questions_do_not_force_land_scope(question: str) -> None:
    analysis = QueryAnalyzer().analyze(question)
    assert analysis.in_scope is False
    assert ClarificationEngine().clarify(analysis).status == "out_of_scope"


def test_sodo_alias_requires_explicit_certificate_action_not_just_land_context() -> None:
    rewriter = QueryRewriter()
    assert rewriter.rewrite("So do to chuc") == "So do to chuc"
    assert "Giấy chứng nhận" not in rewriter.rewrite("So do cua thua dat")
    assert rewriter.rewrite("Sơ đồ thửa đất") == "Sơ đồ thửa đất"


@pytest.mark.parametrize(
    "question",
    ["So do quy hoach dat", "So do thua dat", "Toi muon ve so do mieng dat",
     "Xin cap so do quy hoach dat", "Cấp so do kỹ thuật thửa đất"],
)
def test_diagram_homonyms_are_not_rewritten_as_certificates(question: str) -> None:
    analysis = QueryAnalyzer().analyze(question)
    assert "Giấy chứng nhận" not in analysis.rewritten_question
    assert "sổ đỏ" not in analysis.rewritten_question
    assert analysis.intent != "certificate"


@pytest.mark.parametrize("question", ["Xin cap so do", "Cap so do dat can dieu kien gi?",
                                      "Xin cấp lại so do của thửa đất"])
def test_explicit_unaccented_certificate_issuance_still_routes(question: str) -> None:
    analysis = QueryAnalyzer().analyze(question)
    assert "Giấy chứng nhận" in analysis.rewritten_question
    assert analysis.intent == "certificate"
    assert analysis.in_scope


def test_fold_is_matching_only_and_preserves_canonical_user_input() -> None:
    assert fold_vietnamese("BẠN LÀ AI?") == "ban la ai?"
    canonical = "Đất Đồng Nai"
    assert fold_vietnamese(canonical) == "dat dong nai"
    assert fold_vietnamese(unicodedata.normalize("NFD", canonical)) == "dat dong nai"
    assert QueryRewriter().rewrite("Đồng Nai") == "Đồng Nai"
    assert QueryAnalyzer().analyze(canonical).original_question == canonical


def test_v1_v2_observed_routing_expectations_do_not_regress() -> None:
    root = Path(__file__).resolve().parents[1]
    analyzer = QueryAnalyzer()
    engine = ClarificationEngine()
    v1 = json.loads((root / "data/evaluation/test_questions_v1.json").read_text(encoding="utf-8"))
    v2 = json.loads((root / "data/evaluation/candidate_questions_v2_blind.json").read_text(encoding="utf-8"))["questions"]
    assert all(engine.clarify(analyzer.analyze(row["question"])).status == "ready" for row in v1)
    for row in v2:
        status = engine.clarify(analyzer.analyze(row["question"])).status
        if row["expected_behavior"] == "answer":
            assert status == "ready", row["question_id"]
        else:
            assert status in {"needs_clarification", "insufficient_coverage"}, row["question_id"]
