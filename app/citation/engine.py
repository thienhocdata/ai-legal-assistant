from __future__ import annotations

from typing import Any

from .models import Citation


class CitationEngine:
    def __init__(self, *, max_quote_chars: int = 1600) -> None:
        if max_quote_chars < 200:
            raise ValueError("max_quote_chars quá nhỏ.")
        self.max_quote_chars = max_quote_chars

    def build(
        self,
        results: list[dict[str, Any]],
        *,
        max_citations: int = 5,
    ) -> list[Citation]:
        citations: list[Citation] = []
        seen: set[str] = set()
        for result in results:
            chunk_id = str(result.get("chunk_id", "")).strip()
            if not chunk_id or chunk_id in seen:
                continue
            seen.add(chunk_id)
            quote = str(result.get("text") or result.get("clean_text") or "").strip()
            if len(quote) > self.max_quote_chars:
                quote = quote[: self.max_quote_chars].rstrip() + "…"
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
