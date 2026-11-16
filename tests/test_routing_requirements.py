from __future__ import annotations

import json
from pathlib import Path
import sys
import unicodedata

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent import ClarificationEngine, QueryAnalyzer


@pytest.mark.parametrize(
    ("question", "context_type"),
    [
        ("Mảnh đất đó có cấp sổ được không?", "parcel_eligibility"),
        ("Tôi có được cấp giấy chứng nhận đất không?", "parcel_eligibility"),
        ("Tôi chuyển đất được không?", "ambiguous_land_action"),
        ("Sổ đỏ của tôi có vấn đề, phải tìm ai?", "certificate_issue"),
        ("Nhà tôi tranh chấp đất, có chắc chắn thắng không?", "case_outcome"),
        ("Tranh chấp đất ranh giới thì bên nào thắng?", "case_outcome"),
        ("Tôi mua đất giấy tay, có đảm bảo sang tên được không?", "case_outcome"),
        ("Thu hồi đất nông nghiệp thì đền bao nhiêu tiền?", "compensation_amount"),
        ("Xây nhà trên mảnh đó có bị phạt không?", "construction_facts"),
        ("Đất này xây nhà có bị phạt không?", "construction_facts"),
    ],
)
def test_missing_case_facts_request_targeted_clarification(
    question: str, context_type: str
) -> None:
    analysis = QueryAnalyzer().analyze(question)
    result = ClarificationEngine().clarify(analysis)
    assert context_type in analysis.missing_context_types
    assert analysis.requires_clarification
    assert result.status == "needs_clarification"
    assert 1 <= len(result.questions) <= 2


@pytest.mark.parametrize(
    ("question", "source_type"),
    [
        ("Giá đất ở đây hiện bao nhiêu mỗi mét vuông?", "local_current_rules"),
        ("Quy hoạch khu này còn hiệu lực không?", "local_current_rules"),
        ("Diện tích tối thiểu tách thửa tại tỉnh này là bao nhiêu?", "local_current_rules"),
        ("Thuế thu nhập cá nhân khi bán đất tính ra sao?", "tax_rules"),
        ("Sang tên đất cần mẫu đơn nào?", "administrative_details"),
        ("Đăng ký đất đai theo Nghị định 123 thì sao?", "implementing_regulations"),
        ("Thửa đất số 789 đang bị ngăn chặn giao dịch không?", "personal_record"),
    ],
)
def test_missing_source_types_are_distinguished(
    question: str, source_type: str
) -> None:
    analysis = QueryAnalyzer().analyze(question)
    assert source_type in analysis.missing_source_types
    result = ClarificationEngine().clarify(analysis)
    assert result.status == "insufficient_coverage"
    assert result.questions


@pytest.mark.parametrize(
    "question",
    [
        "Bảng giá đất của tỉnh được sử dụng trong các trường hợp nào?",
        "Bảng giá đất áp dụng cho nghĩa vụ tài chính gì?",
        "Các nguyên tắc bồi thường đất là gì?",
        "Cá nhân muốn chuyển đất nông nghiệp sang đất ở thì cần xin phép không?",
        "Tôi muốn biết điều kiện để được cấp giấy chứng nhận đất.",
        "Sổ đất nhà tôi ghi sai tên thì quy định đính chính ở đâu?",
        "Trình tự thu hồi đất được luật quy định thế nào?",
        "Thủ tục hòa giải tranh chấp đất đai được quy định ra sao?",
        "Quy hoạch sử dụng đất phải được công khai thế nào?",
        "Những cơ quan nào chịu trách nhiệm quản lý đất đai?",
    ],
)
def test_general_statutory_questions_stay_retrievable(question: str) -> None:
    analysis = QueryAnalyzer().analyze(question)
    assert analysis.missing_context_types == []
    assert analysis.missing_source_types == []
    assert ClarificationEngine().clarify(analysis).status == "ready"


def test_all_v1_development_questions_remain_retrievable() -> None:
    questions = json.loads(
        (ROOT / "data" / "evaluation" / "test_questions_v1.json").read_text(
            encoding="utf-8"
        )
    )
    blocked = []
    for row in questions:
        analysis = QueryAnalyzer().analyze(row["question"])
        if ClarificationEngine().clarify(analysis).status != "ready":
            blocked.append(row["question_id"])
    assert blocked == []


def test_routing_normalizes_decomposed_vietnamese() -> None:
    question = "Quy hoạch chỗ tôi còn hiệu lực không?"
    canonical = QueryAnalyzer().analyze(question)
    decomposed = QueryAnalyzer().analyze(unicodedata.normalize("NFD", question))
    assert canonical.to_dict() == decomposed.to_dict()


def test_unrelated_planning_remains_out_of_scope() -> None:
    analysis = QueryAnalyzer().analyze("Quy hoạch nhân sự năm tới cần làm thế nào?")
    assert ClarificationEngine().clarify(analysis).status == "out_of_scope"
