from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


@dataclass(slots=True)
class GuardrailDecision:
    allowed: bool
    code: str = "ok"
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GuardrailEngine:
    CITATION_RE = re.compile(r"\[(\d+)\]")
    INJECTION_PATTERNS = (
        re.compile(r"ignore (?:all |the )?previous instructions", re.IGNORECASE),
        re.compile(r"bỏ qua (?:mọi |tất cả )?(?:chỉ dẫn|hướng dẫn)", re.IGNORECASE),
        re.compile(r"(?:tiết lộ|in ra).*(?:system prompt|chỉ dẫn hệ thống)", re.IGNORECASE),
        re.compile(r"hãy bịa", re.IGNORECASE),
    )

    def __init__(
        self,
        *,
        max_question_chars: int = 2000,
        minimum_dense_score: float = 0.55,
    ) -> None:
        self.max_question_chars = max_question_chars
        self.minimum_dense_score = minimum_dense_score

    def check_input(self, question: str) -> GuardrailDecision:
        value = str(question).strip()
        if not value:
            return GuardrailDecision(False, "empty_question", "Câu hỏi đang để trống.")
        if len(value) > self.max_question_chars:
            return GuardrailDecision(False, "question_too_long", "Câu hỏi vượt giới hạn độ dài.")
        if any(pattern.search(value) for pattern in self.INJECTION_PATTERNS):
            return GuardrailDecision(
                False,
                "prompt_injection",
                "Yêu cầu chứa chỉ dẫn có thể làm sai lệch hệ thống tra cứu pháp luật.",
            )
        return GuardrailDecision(True)

    def check_evidence(
        self,
        results: list[dict[str, Any]],
        citations: list[Any],
    ) -> GuardrailDecision:
        if not results or not citations:
            return GuardrailDecision(False, "no_evidence", "Không tìm thấy căn cứ phù hợp.")
        top = results[0]
        dense_score = float(top.get("dense_score", top.get("score", 0.0)))
        if dense_score < self.minimum_dense_score:
            return GuardrailDecision(
                False,
                "low_retrieval_confidence",
                "Độ tương đồng của căn cứ tìm được chưa đủ để trả lời đáng tin cậy.",
            )
        return GuardrailDecision(True)

    def check_output(self, answer: str, citation_count: int) -> GuardrailDecision:
        labels = {int(value) for value in self.CITATION_RE.findall(str(answer))}
        if not labels:
            return GuardrailDecision(
                False,
                "missing_citation",
                "Câu trả lời sinh ra không có trích dẫn kiểm chứng được.",
            )
        if any(value < 1 or value > citation_count for value in labels):
            return GuardrailDecision(
                False,
                "invalid_citation",
                "Câu trả lời tham chiếu trích dẫn không tồn tại.",
            )
        return GuardrailDecision(True)
