from __future__ import annotations

from typing import Any
from hashlib import sha256
import re

from app.agent.concepts import definition_clause, definition_term
from app.agent.query_understanding import fold_vietnamese
from .models import Citation


class CitationEngine:
    def __init__(self, *, max_quote_chars: int | None = None) -> None:
        if max_quote_chars is not None and max_quote_chars < 200:
            raise ValueError("max_quote_chars quá nhỏ.")
        self.max_quote_chars = max_quote_chars

    def build(
        self,
        results: list[dict[str, Any]],
        *,
        max_citations: int = 5,
    ) -> list[Citation]:
        if max_citations <= 0:
            raise ValueError("max_citations phải lớn hơn 0.")
        citations: list[Citation] = []
        seen: set[str] = set()
        for result in results:
            chunk_id = str(result.get("chunk_id", "")).strip()
            if not chunk_id or chunk_id in seen:
                continue
            seen.add(chunk_id)
            quote = str(result.get("text") or result.get("clean_text") or "").strip()
            if self.max_quote_chars is not None and len(quote) > self.max_quote_chars:
                raise ValueError(
                    "Đoạn căn cứ vượt max_quote_chars; không cắt ngầm điều kiện/ngoại lệ. "
                    "Tăng ngân sách hoặc chọn chunk phù hợp trước khi tạo citation."
                )
            citations.append(
                Citation(
                    citation_id=f"[{len(citations) + 1}]",
                    chunk_id=chunk_id,
                    document_id=str(result.get("document_id", "")),
                    document_name=str(result.get("document_name", "")),
                    article_no=int(result.get("article_no", 0)),
                    article_title=str(result.get("article_title", "")),
                    clause_nos=[int(value) for value in result.get("clause_nos", [])],
                    point_nos=[str(value) for value in result.get("point_nos", [])],
                    quote=quote,
                    score=float(result.get("score", 0.0)),
                    quote_sha256=sha256(quote.encode("utf-8")).hexdigest(),
                    source_quote_chars=len(quote),
                    quote_truncated=False,
                )
            )
            if len(citations) >= max_citations:
                break
        return citations

    @staticmethod
    def format_context(citations: list[Citation]) -> str:
        blocks = []
        for citation in citations:
            location = f"Điều {citation.article_no}"
            if citation.clause_nos:
                location += ", Khoản " + ", ".join(map(str, citation.clause_nos))
            if citation.point_nos:
                location += ", Điểm " + ", ".join(citation.point_nos)
            blocks.append(
                f"{citation.citation_id} {citation.document_name} - {location}: "
                f"{citation.article_title}\n{citation.quote}"
            )
        return "\n\n".join(blocks)

    @classmethod
    def format_extractive_answer(
        cls,
        citations: list[Citation],
        *,
        max_evidence_blocks: int = 3,
    ) -> str:
        """Canonical verbatim renderer; this makes no legal inference."""
        if not 1 <= max_evidence_blocks <= 5:
            raise ValueError("max_evidence_blocks phải từ 1 đến 5.")
        context = cls.format_context(citations[:max_evidence_blocks])
        if not context:
            return "Không tìm thấy căn cứ đủ rõ để trả lời."
        return (
            "Mình tìm được các đoạn luật liên quan dưới đây; "
            "chưa kết luận áp dụng cho vụ việc:\n\n"
            f"{context}\n\n"
            "Chưa kiểm tra hiệu lực hiện hành và văn bản sửa đổi. "
            "Vui lòng đối chiếu toàn văn trước khi áp dụng."
        )

    @staticmethod
    def format_definition_answer(citation: Citation) -> str:
        """Display one complete definition, retaining the original source quote.

        Only structural headers and the clause number are omitted in the answer.
        Conditions and all following sentences in that clause remain verbatim.
        """
        clause = definition_clause(citation.quote)
        if (
            clause is None
            or definition_term(citation.quote) is None
            or fold_vietnamese(citation.article_title) != "giai thich tu ngu"
            or citation.clause_nos != [int(clause.split(".", 1)[0])]
        ):
            raise ValueError("Căn cứ không phải một khoản định nghĩa đầy đủ.")
        content = re.sub(r"^\d+\.\s+", "", clause, count=1)
        return f"{content} {citation.citation_id}"
