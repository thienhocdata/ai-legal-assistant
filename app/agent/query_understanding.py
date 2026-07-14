from __future__ import annotations

import re
import unicodedata

from .models import QueryAnalysis


class QueryRewriter:
    """Deterministic Vietnamese legal synonym expansion."""

    REPLACEMENTS = (
        (re.compile(r"\bsổ đỏ\b", re.IGNORECASE), "Giấy chứng nhận quyền sử dụng đất"),
        (re.compile(r"\bsang tên\b", re.IGNORECASE), "đăng ký biến động chuyển nhượng quyền sử dụng đất"),
        (re.compile(r"\bđền bù\b", re.IGNORECASE), "bồi thường"),
        (re.compile(r"\bgiải tỏa\b", re.IGNORECASE), "thu hồi đất"),
        (re.compile(r"\btách sổ\b", re.IGNORECASE), "tách thửa đất"),
        (re.compile(r"\bgộp sổ\b", re.IGNORECASE), "hợp thửa đất"),
    )

    def rewrite(self, question: str) -> str:
        value = unicodedata.normalize("NFC", str(question))
        value = re.sub(r"\s+", " ", value).strip()
        for pattern, replacement in self.REPLACEMENTS:
            value = pattern.sub(replacement, value)
        return value


class QueryAnalyzer:
    ARTICLE_RE = re.compile(r"\bĐiều\s+(\d+)\b", re.IGNORECASE)
    CLAUSE_RE = re.compile(r"\b(?:Khoản|khoản)\s+(\d+)\b")
    POINT_RE = re.compile(r"\b(?:Điểm|điểm)\s+([a-zđ])\b", re.IGNORECASE)
    TOKEN_RE = re.compile(r"[0-9a-zA-ZÀ-ỹĐđ]+", re.UNICODE)

    INTENTS = {
        "transfer": ("chuyển nhượng", "tặng cho", "thừa kế", "chuyển đổi"),
        "certificate": ("giấy chứng nhận", "cấp sổ", "sổ đỏ"),
        "registration": ("đăng ký đất đai", "đăng ký biến động", "sang tên"),
        "recovery": ("thu hồi đất", "giải tỏa", "cưỡng chế"),
        "compensation": ("bồi thường", "hỗ trợ", "tái định cư", "đền bù"),
        "land_price": ("giá đất", "bảng giá đất", "tiền sử dụng đất", "tiền thuê đất"),
        "land_use": ("chuyển mục đích", "sử dụng đất", "giao đất", "cho thuê đất"),
        "parcel": ("tách thửa", "hợp thửa", "thửa đất"),
        "dispute": ("tranh chấp", "hòa giải", "khiếu nại", "khởi kiện"),
    }
    SCOPE_TERMS = {
        "đất", "thửa", "giấy chứng nhận", "sổ đỏ", "địa chính", "tái định cư",
        "bồi thường", "chuyển nhượng", "quyền sử dụng", "giá đất", "tranh chấp",
    }
    VAGUE_PATTERNS = (
        re.compile(r"\btrường hợp (?:này|đó)\b", re.IGNORECASE),
        re.compile(r"\bnhư vậy\b", re.IGNORECASE),
        re.compile(r"^(?:tôi|mình) có được (?:làm|thực hiện) không\??$", re.IGNORECASE),
    )

    def __init__(self, rewriter: QueryRewriter | None = None) -> None:
        self.rewriter = rewriter or QueryRewriter()

    def analyze(self, question: str) -> QueryAnalysis:
        original = re.sub(r"\s+", " ", str(question)).strip()
        if not original:
            raise ValueError("Câu hỏi không được để trống.")
        rewritten = self.rewriter.rewrite(original)
        lower = rewritten.lower()

        intent = "general_legal_lookup"
        for name, terms in self.INTENTS.items():
            if any(term in lower for term in terms):
                intent = name
                break

        article_refs = sorted({int(value) for value in self.ARTICLE_RE.findall(rewritten)})
        clause_refs = sorted({int(value) for value in self.CLAUSE_RE.findall(rewritten)})
        point_refs = sorted({value.lower() for value in self.POINT_RE.findall(rewritten)})
        in_scope = any(term in lower for term in self.SCOPE_TERMS) or bool(article_refs)
        reasons: list[str] = []
        requires_clarification = False

        if len(original) < 8:
            requires_clarification = True
            reasons.append("question_too_short")
        if any(pattern.search(original) for pattern in self.VAGUE_PATTERNS):
            requires_clarification = True
            reasons.append("missing_context")
        if not in_scope:
            reasons.append("outside_land_law_scope")

        tokens = [
            token.lower()
            for token in self.TOKEN_RE.findall(rewritten)
            if len(token) > 2
        ]
        return QueryAnalysis(
            original_question=original,
            rewritten_question=rewritten,
            intent=intent,
            keywords=list(dict.fromkeys(tokens)),
            article_refs=article_refs,
            clause_refs=clause_refs,
            point_refs=point_refs,
            in_scope=in_scope,
            requires_clarification=requires_clarification,
            reasons=reasons,
        )
