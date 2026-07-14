from __future__ import annotations

import re

from .base import BaseLLMProvider, LLMResponse


class ExtractiveProvider(BaseLLMProvider):
    """Offline fallback that returns retrieved evidence without inventing facts."""

    BLOCK_RE = re.compile(r"(\[1\].*?)(?=\n\[2\]|\Z)", re.DOTALL)

    def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        match = self.BLOCK_RE.search(user_prompt)
        evidence = match.group(1).strip() if match else ""
        if evidence:
            text = (
                "Hệ thống đang chạy ở chế độ trích xuất cục bộ. "
                "Căn cứ gần nhất tìm được là:\n\n"
                f"{evidence}\n\n"
                "Vui lòng đối chiếu toàn văn và tình trạng hiệu lực trước khi áp dụng."
            )
        else:
            text = "Không tìm thấy căn cứ đủ rõ để trả lời."
        return LLMResponse(
            text=text,
            provider="extractive",
            model="deterministic-v1",
        )
