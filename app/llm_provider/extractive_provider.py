from __future__ import annotations

import re

from .base import BaseLLMProvider, LLMResponse


class ExtractiveProvider(BaseLLMProvider):
    """Offline fallback that returns retrieved evidence without inventing facts."""

    BLOCK_RE = re.compile(
        r"(^\[\d+\] .*?)(?=\n\n\[\d+\] |\Z)", re.DOTALL | re.MULTILINE
    )

    def __init__(self, *, max_evidence_blocks: int = 3) -> None:
        if not 1 <= max_evidence_blocks <= 5:
            raise ValueError("max_evidence_blocks phải từ 1 đến 5.")
        self.max_evidence_blocks = max_evidence_blocks

    def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        # Only extract the evidence section, never the question or the following
        # generation instructions. CitationEngine also supports standalone context.
        context = user_prompt.rsplit("CĂN CỨ TRUY XUẤT:\n", 1)[-1]
        context = context.split("\n\nYÊU CẦU TRẢ LỜI:\n", 1)[0]
        blocks = self.BLOCK_RE.findall(context)
        evidence = "\n\n".join(
            block.strip() for block in blocks[: self.max_evidence_blocks]
        )
        if evidence:
            text = (
                "Mình tìm được các đoạn luật liên quan dưới đây; "
                "chưa kết luận áp dụng cho vụ việc:\n\n"
                f"{evidence}\n\n"
                "Chưa kiểm tra hiệu lực hiện hành và văn bản sửa đổi. "
                "Vui lòng đối chiếu toàn văn trước khi áp dụng."
            )
        else:
            text = "Không tìm thấy căn cứ đủ rõ để trả lời."
        return LLMResponse(
            text=text,
            provider="extractive",
            model="deterministic-v2",
        )
