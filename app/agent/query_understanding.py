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
        "sổ đất",
    }
    VAGUE_PATTERNS = (
        re.compile(r"\btrường hợp (?:này|đó)\b", re.IGNORECASE),
        re.compile(r"\bnhư vậy\b", re.IGNORECASE),
        re.compile(r"^(?:tôi|mình) có được (?:làm|thực hiện) không\??$", re.IGNORECASE),
    )

    @staticmethod
    def _routing_requirements(question: str) -> tuple[list[str], list[str]]:
        """Identify missing evidence types without inferring a legal outcome.

        Source gaps require a concrete value, record or external-source request;
        merely mentioning a province, a procedure or a personal situation is not
        sufficient. General questions about statutory rules remain retrievable.
        """
        lower = question.casefold()
        sources: list[str] = []
        context: list[str] = []

        def has(pattern: str) -> bool:
            return bool(re.search(pattern, lower))

        if has(r"\b(?:lệ phí trước bạ|thuế thu nhập cá nhân)\b"):
            sources.append("tax_rules")
        if (
            has(r"\b(?:mẫu đơn|mẫu giấy|biểu mẫu).*(?:số mấy|nào|tải|bao nhiêu)\b")
            or has(r"\bbao nhiêu bản sao\b")
        ):
            sources.append("administrative_details")
        if has(r"\btheo (?:nghị định|thông tư)\b") or has(
            r"\b(?:nghị định|thông tư)\s+(?:số\s+)?\d"
        ):
            sources.append("implementing_regulations")
        if has(r"\b(?:thửa (?:đất )?số|tờ bản đồ)\s+\d+\b"):
            sources.append("personal_record")

        concrete_location = has(
            r"\b(?:chỗ tôi|ở đây|khu này|đất của tôi|tỉnh|thành phố|huyện|xã)\b"
        )
        exact_price = has(r"\b(?:giá đất|bảng giá đất|phí đo đạc)\b") and has(
            r"\b(?:bao nhiêu|một mét vuông|mỗi mét vuông|m2|m²|cụ thể)\b"
        )
        current_planning = has(r"\bquy hoạch\b") and concrete_location and has(
            r"\b(?:còn hiệu lực|bị bỏ|hủy|huỷ|hiện nay|mới nhất|có nằm trong)\b"
        )
        local_minimum = has(r"\bdiện tích tối thiểu\b") and concrete_location
        record_status = has(r"\b(?:quy hoạch|ngăn chặn giao dịch)\b") and has(
            r"\b(?:thửa|đất của tôi)\b"
        ) and has(r"\b(?:có bị|đang|hiện|nằm trong|kiểm tra)\b")
        if exact_price or current_planning or local_minimum:
            sources.append("local_current_rules")
        if record_status:
            sources.append("personal_record")

        personal = has(r"\b(?:tôi|nhà tôi|gia đình tôi|nhà mình|của mình)\b")
        deictic_parcel = has(r"\b(?:miếng đất|mảnh đất|thửa đất|đất|mảnh)\s+(?:này|đó)\b")
        general_eligibility = has(
            r"\b(?:điều kiện (?:gì|nào|để)|cần (?:đủ )?điều kiện|những điều kiện|nguyên tắc|quy định)\b"
        )
        if (deictic_parcel or personal) and has(
            r"\b(?:làm sổ|cấp sổ|cấp giấy chứng nhận)\b"
        ) and has(r"\b(?:được không|được chứ|có được|có làm)\b") and not general_eligibility:
            context.append("parcel_eligibility")
        if personal and has(r"\bchuyển đất\s*(?:không|được không|thì sao|được chứ)?[?.!]*$"):
            context.append("ambiguous_land_action")
        if personal and has(r"\bsổ(?: đất| đỏ)?\b.*\bcó vấn đề\b"):
            context.append("certificate_issue")
        case_assurance = personal and has(r"\b(?:chắc chắn|bảo đảm|đảm bảo|100\s*%)\b") and has(
            r"\b(?:sang tên|chuyển nhượng|thắng|được cấp|được bồi thường)\b"
        )
        dispute_outcome = has(r"\btranh chấp\b") and has(r"\bbên nào.*\bthắng\b")
        if case_assurance or dispute_outcome:
            context.append("case_outcome")
            sources.append("personal_record")
        if has(r"\b(?:bồi thường|đền bù|đền)\b") and has(
            r"\b(?:bao nhiêu tiền|được bao nhiêu|mấy tiền)\b"
        ):
            context.append("compensation_amount")
            sources.append("local_current_rules")
        if (deictic_parcel or personal) and has(r"\bxây nhà\b") and has(r"\b(?:bị phạt|được không)\b"):
            context.append("construction_facts")
            sources.append("implementing_regulations")

        return list(dict.fromkeys(sources)), list(dict.fromkeys(context))

    def __init__(self, rewriter: QueryRewriter | None = None) -> None:
        self.rewriter = rewriter or QueryRewriter()

    def analyze(self, question: str) -> QueryAnalysis:
        original = re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(question))).strip()
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
        missing_sources, missing_context = self._routing_requirements(original)
        if "construction_facts" in missing_context or (
            "local_current_rules" in missing_sources and "quy hoạch" in lower
        ):
            in_scope = True
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
        if missing_sources:
            reasons.append("requires_source_outside_current_corpus")
        if missing_context:
            requires_clarification = True
            if "missing_context" not in reasons:
                reasons.append("missing_context")

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
            missing_source_types=missing_sources,
            missing_context_types=missing_context,
        )
