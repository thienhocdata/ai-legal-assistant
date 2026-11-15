from __future__ import annotations

from .models import ClarificationResult, QueryAnalysis


class ClarificationEngine:
    INTENT_QUESTIONS = {
        "transfer": [
            "Bạn đang hỏi về chuyển nhượng, tặng cho hay thừa kế quyền sử dụng đất?",
            "Thửa đất đã có Giấy chứng nhận và hiện có tranh chấp hoặc bị kê biên không?",
        ],
        "certificate": [
            "Đất đã có giấy tờ về quyền sử dụng đất hay chưa?",
            "Bạn bắt đầu sử dụng đất từ thời điểm nào và đất hiện có tranh chấp không?",
        ],
        "recovery": [
            "Đất bị thu hồi vì mục đích nào và bạn đã nhận quyết định thu hồi chưa?",
            "Bạn muốn hỏi về căn cứ thu hồi, bồi thường hay trình tự thực hiện?",
        ],
        "compensation": [
            "Bạn muốn xác định điều kiện được bồi thường, mức bồi thường hay hỗ trợ tái định cư?",
            "Loại đất và giấy tờ pháp lý của thửa đất hiện tại là gì?",
        ],
        "dispute": [
            "Tranh chấp liên quan đến ranh giới, quyền sử dụng, thừa kế hay giao dịch đất đai?",
            "Vụ việc đã được hòa giải tại Ủy ban nhân dân cấp xã chưa?",
        ],
    }

    def clarify(self, analysis: QueryAnalysis) -> ClarificationResult:
        if not analysis.in_scope:
            return ClarificationResult(
                status="out_of_scope",
                reason="Câu hỏi chưa thể hiện nội dung thuộc pháp luật đất đai.",
                questions=["Bạn có thể nêu rõ vấn đề liên quan đến đất đai cần tra cứu không?"],
            )
        if "requires_source_outside_current_corpus" in analysis.reasons:
            return ClarificationResult(
                status="insufficient_coverage",
                reason=(
                    "Câu hỏi cần dữ liệu thủ tục, thuế, hồ sơ vụ việc hoặc quy định "
                    "địa phương chưa có trong kho hiện tại. Hệ thống không nên suy đoán "
                    "chỉ từ Văn bản hợp nhất Luật Đất đai."
                ),
                questions=[
                    "Bạn có thể cung cấp văn bản hướng dẫn hoặc địa phương cần tra cứu để đối chiếu không?"
                ],
            )
        if not analysis.requires_clarification:
            return ClarificationResult(status="ready")
        questions = self.INTENT_QUESTIONS.get(
            analysis.intent,
            ["Bạn có thể mô tả rõ chủ thể, loại đất và vấn đề pháp lý cần giải quyết không?"],
        )
        return ClarificationResult(
            status="needs_clarification",
            questions=questions[:2],
            reason=", ".join(analysis.reasons),
        )
