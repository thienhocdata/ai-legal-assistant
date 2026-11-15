from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent import ClarificationEngine, QueryAnalyzer


def test_colloquial_question_is_rewritten() -> None:
    analysis = QueryAnalyzer().analyze("Sang tên sổ đỏ cần điều kiện gì?")
    assert "đăng ký biến động" in analysis.rewritten_question
    assert "Giấy chứng nhận quyền sử dụng đất" in analysis.rewritten_question
    assert analysis.intent == "transfer"
    assert analysis.in_scope


def test_explicit_legal_references_are_extracted() -> None:
    analysis = QueryAnalyzer().analyze("Khoản 1 Điều 45 điểm a quy định gì về đất?")
    assert analysis.article_refs == [45]
    assert analysis.clause_refs == [1]
    assert analysis.point_refs == ["a"]


def test_vague_question_requires_clarification() -> None:
    analysis = QueryAnalyzer().analyze("Tôi có được làm không?")
    result = ClarificationEngine().clarify(analysis)
    assert result.status == "out_of_scope"
    assert result.questions


def test_current_corpus_gap_is_reported_before_retrieval() -> None:
    analysis = QueryAnalyzer().analyze(
        "Lệ phí trước bạ khi sang tên quyền sử dụng đất được tính ra sao?"
    )
    result = ClarificationEngine().clarify(analysis)
    assert analysis.in_scope
    assert result.status == "insufficient_coverage"
    assert "chưa có trong kho" in result.reason


def test_general_transfer_question_is_not_marked_as_corpus_gap() -> None:
    analysis = QueryAnalyzer().analyze("Điều kiện chuyển nhượng đất là gì?")
    assert "requires_source_outside_current_corpus" not in analysis.reasons
    assert ClarificationEngine().clarify(analysis).status == "ready"


def main() -> None:
    test_colloquial_question_is_rewritten()
    test_explicit_legal_references_are_extracted()
    test_vague_question_requires_clarification()
    print("MODULE 11-12 - QUERY & CLARIFICATION: SUCCESS")


if __name__ == "__main__":
    main()
