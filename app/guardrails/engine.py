from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from app.agent.query_understanding import fold_vietnamese
from typing import Any
from hashlib import sha256

from app.citation import CitationEngine
from app.citation.models import Citation


@dataclass(slots=True)
class GuardrailDecision:
    allowed: bool
    code: str = "ok"
    message: str = ""
    validation_scope: str = "structural"
    semantic_support_verified: bool = False

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
        folded = fold_vietnamese(value)
        folded_patterns = (
            r"ignore (?:all |the )?previous instructions",
            r"bo qua (?:moi |tat ca )?(?:chi dan|huong dan)",
            r"(?:tiet lo|in ra).*(?:system prompt|chi dan he thong)",
            r"hay bia",
        )
        if any(pattern.search(value) for pattern in self.INJECTION_PATTERNS) or any(
            re.search(pattern, folded) for pattern in folded_patterns
        ):
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

    def check_grounded_output(
        self,
        answer: str,
        citations: list[Citation],
        *,
        extractive: bool = False,
    ) -> GuardrailDecision:
        """Verify retained quotes and, for extractive mode, exact rendering.

        Hosted prose can only receive structural checks here. A valid marker or
        a matching quote does not establish semantic entailment or legal truth.
        """
        structure = self.check_output(answer, len(citations))
        if not structure.allowed:
            return structure
        for citation in citations:
            if (
                not citation.quote.strip()
                or not citation.quote_sha256
                or citation.quote_truncated
                or citation.source_quote_chars != len(citation.quote)
                or sha256(citation.quote.encode("utf-8")).hexdigest() != citation.quote_sha256
            ):
                return GuardrailDecision(
                    False,
                    "citation_integrity_mismatch",
                    "Đoạn trích đã thay đổi hoặc bị cắt so với căn cứ đã giữ lại.",
                    validation_scope="citation_integrity",
                )
        if extractive:
            # Accept only verbatim canonical output for a prefix of available
            # citations. No unsupported sentence can piggyback on a valid [n].
            allowed_answers = {
                CitationEngine.format_extractive_answer(citations, max_evidence_blocks=count)
                for count in range(1, min(5, len(citations)) + 1)
            }
            if answer.strip() not in allowed_answers:
                return GuardrailDecision(
                    False,
                    "extractive_content_mismatch",
                    "Nội dung trích xuất không khớp nguyên văn các căn cứ đã cung cấp.",
                    validation_scope="exact_extractive_rendering",
                )
            return GuardrailDecision(
                True,
                "exact_extractive_evidence",
                validation_scope="exact_extractive_rendering",
            )
        return GuardrailDecision(
            True,
            "citation_structure_only",
            validation_scope="citation_labels_and_quote_integrity_only",
        )
