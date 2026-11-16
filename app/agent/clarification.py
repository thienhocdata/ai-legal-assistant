from __future__ import annotations

from .models import ClarificationResult, QueryAnalysis


class ClarificationEngine:
    CONTEXT_QUESTIONS = {
        "parcel_eligibility": [
            "Bạn có thể mô tả nguồn gốc, thời điểm sử dụng đất và giấy tờ đang có không?",
            "Đất có tranh chấp hoặc có thông tin vi phạm nào cần đối chiếu không?",
        ],
        "ambiguous_land_action": [
            "Bạn muốn chuyển nhượng/chuyển đổi quyền sử dụng đất hay chuyển mục đích sử dụng đất?",
            "Loại đất hiện tại và việc bạn dự định thực hiện là gì?",
        ],
        "certificate_issue": [
            "Sổ gặp vấn đề gì: ghi sai thông tin, bị mất, cấp sai hay đang có tranh chấp?",
            "Bạn muốn tra cứu cách xử lý lỗi nào? Chỉ cần mô tả, không gửi thông tin định danh cá nhân.",
        ],
        "case_outcome": [
            "Bạn muốn tra cứu điều kiện pháp lý nào? Mình chưa thể bảo đảm kết quả vụ việc chỉ từ mô tả này.",
            "Bạn có thể bổ sung tình tiết và loại giấy tờ liên quan, đã ẩn thông tin cá nhân không?",
        ],
        "compensation_amount": [
            "Đất thuộc địa phương nào, loại đất và diện tích bị thu hồi là gì?",
            "Bạn muốn tính bồi thường về đất hay tài sản? Cần đối chiếu phương án/quyết định và giá áp dụng tại địa phương.",
        ],
        "construction_facts": [
            "Loại đất, mục đích sử dụng được ghi nhận và việc xây dựng dự kiến là gì?",
            "Cần kiểm tra thêm quy định xây dựng, giấy phép và chế tài áp dụng; kho hiện tại chưa đủ để kết luận mức phạt.",
        ],
    }
    SOURCE_QUESTIONS = {
        "tax_rules": "Cần đối chiếu quy định thuế/lệ phí áp dụng cho giao dịch và thời điểm nào?",
        "administrative_details": "Bạn cần biểu mẫu/hồ sơ của thủ tục nào, tại địa phương và thời điểm nào?",
        "implementing_regulations": "Bạn cần đối chiếu nghị định/thông tư hoặc thủ tục cụ thể nào?",
        "local_current_rules": "Bạn cần giá hoặc thông tin quy hoạch tại địa phương, vị trí, loại đất và thời điểm nào?",
        "personal_record": "Bạn cần kiểm tra thông tin nào của thửa đất? Chỉ mô tả đã ẩn danh; hồ sơ hiện hành cần được xác minh ở nguồn có thẩm quyền.",
    }
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
        if analysis.missing_context_types:
            context_type = analysis.missing_context_types[0]
            return ClarificationResult(
                status="needs_clarification",
                reason="Thiếu dữ kiện để xác định yêu cầu cụ thể; chưa đưa ra kết luận vụ việc.",
                questions=self.CONTEXT_QUESTIONS.get(
                    context_type,
                    ["Bạn có thể mô tả rõ loại đất, vấn đề cần giải quyết và dữ kiện liên quan không?"],
                )[:2],
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
                    self.SOURCE_QUESTIONS[source_type]
                    for source_type in analysis.missing_source_types[:2]
                    if source_type in self.SOURCE_QUESTIONS
                ] or ["Bạn có thể xác định văn bản hướng dẫn hoặc địa phương cần tra cứu để đối chiếu không?"],
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
