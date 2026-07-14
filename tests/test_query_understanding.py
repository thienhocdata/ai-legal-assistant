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


def main() -> None:
    test_colloquial_question_is_rewritten()
    test_explicit_legal_references_are_extracted()
    test_vague_question_requires_clarification()
    print("MODULE 11-12 - QUERY & CLARIFICATION: SUCCESS")


if __name__ == "__main__":
    main()
