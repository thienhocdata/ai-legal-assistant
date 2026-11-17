from __future__ import annotations

import re
import unicodedata

from .models import QueryAnalysis


def fold_vietnamese(value: str) -> str:
    """Fold Vietnamese for matching only; never use this as source-law text.

    This does not restore accents, correct spelling, or infer a place/person name.
    Canonical legal phrases in QueryRewriter are an explicit, bounded dictionary.
    """
    normalized = unicodedata.normalize("NFD", str(value)).casefold()
    return "".join(
        "d" if char == "đ" else char
        for char in normalized
        if unicodedata.category(char) != "Mn"
    )


def _contains_term(value: str, term: str) -> bool:
    return bool(re.search(r"\b" + re.escape(term) + r"\b", value))


class QueryRewriter:
    """Deterministic Vietnamese legal synonym expansion."""

    # Restore only known multiword domain phrases. In particular, do not turn
    # every "dat"/"thua" into đất/thửa or guess what an isolated "so do" means.
    ASCII_LEGAL_PHRASES = (
        ("giay chung nhan quyen su dung dat", "Giấy chứng nhận quyền sử dụng đất"),
        ("quyen su dung dat", "quyền sử dụng đất"),
        ("dang ky bien dong", "đăng ký biến động"),
        ("dang ky dat dai", "đăng ký đất đai"),
        ("chuyen muc dich", "chuyển mục đích"),
        ("dat nong nghiep", "đất nông nghiệp"),
        ("thu hoi dat", "thu hồi đất"),
        ("giay chung nhan", "Giấy chứng nhận"),
        ("boi thuong", "bồi thường"),
        ("tai dinh cu", "tái định cư"),
        ("chuyen nhuong", "chuyển nhượng"),
        ("chuyen doi", "chuyển đổi"),
        ("tang cho", "tặng cho"),
        ("thua ke", "thừa kế"),
        ("cho thue dat", "cho thuê đất"),
        ("giao dat", "giao đất"),
        ("chuyen dat", "chuyển đất"),
        ("mua dat", "mua đất"),
        ("ban dat", "bán đất"),
        ("su dung dat", "sử dụng đất"),
        ("tach thua dat", "tách thửa đất"),
        ("tach thua", "tách thửa"),
        ("hop thua dat", "hợp thửa đất"),
        ("hop thua", "hợp thửa"),
        ("thua dat", "thửa đất"),
        ("mieng dat", "miếng đất"),
        ("manh dat", "mảnh đất"),
        ("dat nay", "đất này"),
        ("dat do", "đất đó"),
        ("bang gia dat", "bảng giá đất"),
        ("gia dat", "giá đất"),
        ("dat dai", "đất đai"),
        ("tranh chap dat dai", "tranh chấp đất đai"),
        ("tranh chap", "tranh chấp"),
        ("hoa giai", "hòa giải"),
        ("khieu nai", "khiếu nại"),
        ("khoi kien", "khởi kiện"),
        ("dia chinh", "địa chính"),
    )
    ASCII_CONTEXTUAL_PHRASES = (
        ("so dat", "sổ đất"),
        ("sang ten", "sang tên"),
        ("tach so", "tách sổ"),
        ("gop so", "gộp sổ"),
        ("den bu", "đền bù"),
        ("giai toa", "giải tỏa"),
    )

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
        for source, target in sorted(
            self.ASCII_LEGAL_PHRASES, key=lambda item: len(item[0]), reverse=True
        ):
            value = re.sub(r"\b" + re.escape(source) + r"\b", target, value, flags=re.IGNORECASE)
        for source, target, following in (
            ("dieu", "Điều", r"\s+\d+\b"),
            ("khoan", "Khoản", r"\s+\d+\b"),
            ("diem", "Điểm", r"\s+[a-zđ]\b"),
        ):
            value = re.sub(
                r"\b" + source + "(?=" + following + ")",
                target, value, flags=re.IGNORECASE,
            )
        # A land cue alone cannot distinguish sơ đồ from sổ đỏ. Restore ASCII
        # "so do" only for an explicit certificate-issuance action, and keep it
        # untouched when diagram/planning cues remain. Even then this is a
        # bounded language aid, never a legal conclusion about eligibility.
        folded = fold_vietnamese(value)
        certificate_action = bool(re.search(r"\bcap(?: lai)? so do\b", folded))
        diagram_cue = bool(re.search(
            r"\b(?:quy hoach|ban do|ban ve|dia hinh|ky thuat|do dac)\b|\bso do to chuc\b",
            folded,
        ))
        if certificate_action and not diagram_cue:
            value = re.sub(r"\bso do\b", "sổ đỏ", value, flags=re.IGNORECASE)
        # Other contextual aliases (e.g. sang tên xe/đất) still need a land cue.
        folded = fold_vietnamese(value)
        land_context = any(
            _contains_term(folded, term)
            for term in ("dat", "thua", "dia chinh", "giay chung nhan", "quyen su dung")
        )
        if land_context:
            for source, target in self.ASCII_CONTEXTUAL_PHRASES:
                value = re.sub(r"\b" + re.escape(source) + r"\b", target, value, flags=re.IGNORECASE)
        for pattern, replacement in self.REPLACEMENTS:
            value = pattern.sub(replacement, value)
        return value


class QueryAnalyzer:
    ARTICLE_RE = re.compile(r"\b(?:Điều|dieu)\s+(\d+)\b", re.IGNORECASE)
    CLAUSE_RE = re.compile(r"\b(?:Khoản|khoan)\s+(\d+)\b", re.IGNORECASE)
    POINT_RE = re.compile(r"\b(?:Điểm|diem)\s+([a-zđ])\b", re.IGNORECASE)
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
    AMBIGUOUS_FOLDED_TERMS = {"sổ đỏ", "sổ đất", "cấp sổ"}

    @staticmethod
    def _routing_requirements(question: str) -> tuple[list[str], list[str]]:
        """Identify missing evidence types without inferring a legal outcome.

        Source gaps require a concrete value, record or external-source request;
        merely mentioning a province, a procedure or a personal situation is not
        sufficient. General questions about statutory rules remain retrievable.
        """
        lower = fold_vietnamese(question)
        sources: list[str] = []
        context: list[str] = []

        def has(pattern: str) -> bool:
            return bool(re.search(fold_vietnamese(pattern), lower))

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
        lower = rewritten.casefold()
        folded_lower = fold_vietnamese(rewritten)

        intent = "general_legal_lookup"
        for name, terms in self.INTENTS.items():
            if any(
                _contains_term(lower, term)
                or (
                    term not in self.AMBIGUOUS_FOLDED_TERMS
                    and _contains_term(folded_lower, fold_vietnamese(term))
                )
                for term in terms
            ):
                intent = name
                break

        article_refs = sorted({int(value) for value in self.ARTICLE_RE.findall(rewritten)})
        clause_refs = sorted({int(value) for value in self.CLAUSE_RE.findall(rewritten)})
        point_refs = sorted({value.lower() for value in self.POINT_RE.findall(rewritten)})
        in_scope = any(
            _contains_term(lower, term)
            or (
                " " in term
                and term not in self.AMBIGUOUS_FOLDED_TERMS
                and _contains_term(folded_lower, fold_vietnamese(term))
            )
            for term in self.SCOPE_TERMS
        ) or bool(article_refs)
        missing_sources, missing_context = self._routing_requirements(original)
        if "construction_facts" in missing_context or (
            "local_current_rules" in missing_sources
            and _contains_term(folded_lower, "quy hoach")
        ):
            in_scope = True
        reasons: list[str] = []
        requires_clarification = False

        if len(original) < 8:
            requires_clarification = True
            reasons.append("question_too_short")
        if any(re.search(fold_vietnamese(pattern.pattern), fold_vietnamese(original))
               for pattern in self.VAGUE_PATTERNS):
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
