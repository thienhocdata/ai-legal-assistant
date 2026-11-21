from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from .query_understanding import QueryRewriter, fold_vietnamese


@dataclass(frozen=True, slots=True)
class ConceptRequest:
    term: str
    statutory: bool = False
    explicit_definition: bool = True


# Ordinary vocabulary explanation, not a statutory definition or legal advice.
# Legal definitions below must be obtained from the verified source chunks.
LAND_GENERAL_EXPLANATION = (
    "Hiểu đơn giản, đất đai là phần đất trên bề mặt Trái Đất mà con người sử dụng "
    "để ở, sản xuất hoặc cho các hoạt động khác. Đây là cách giải thích nghĩa "
    "thông thường của từ này."
)
LAND_STATUTORY_ABSENCE = (
    "Mình chưa tìm thấy một định nghĩa riêng cho từ ‘đất đai’ trong phần giải "
    "thích từ ngữ của kho luật hiện có. Quy định về sở hữu đất đai là một nội "
    "dung khác, nên mình không dùng quy định đó làm định nghĩa."
)


def _clean_term(term: str) -> str:
    return term.strip().strip('"\'“”‘’').strip()


def parse_concept_request(question: str) -> ConceptRequest | None:
    """Recognize complete concept questions, not arbitrary legal eligibility.

    Matching is intentionally bounded. Unknown terms may be parsed, but only
    an exact source-definition match (or an explicit ordinary glossary entry)
    can supply an answer. This is not general conversational understanding.
    """
    value = QueryRewriter().rewrite(unicodedata.normalize("NFC", str(question)))
    value = value.strip().rstrip("?!。.! ")
    if not value:
        return None

    # Prefix/suffix spans are located on NFC folded text, preserving the
    # corresponding original term spelling rather than reconstructing accents.
    def remove_prefix(pattern: str) -> bool:
        nonlocal value
        match = re.match(pattern, fold_vietnamese(value))
        if not match:
            return False
        value = value[match.end():].strip(" ,:")
        return True

    for _ in range(4):
        if not remove_prefix(
            r"^(?:(?:h+m+|u+m+|um|uh|a|o|vay|the)\b[ ,:]*|"
            r"(?:minh|toi) (?:chi )?(?:muon )?hoi\b[ ,:]*|"
            r"(?:ban )?(?:cho (?:minh|toi) biet)\b[ ,:]*)"
        ):
            break

    statutory = False
    legal_context = (
        r"(?:theo (?:luat(?: dat dai)?(?: (?:19|20)\d{2})?|phap luat)|ve mat phap ly)"
    )
    if re.match(r"^" + legal_context + r"\b", fold_vietnamese(value)):
        remove_prefix(r"^" + legal_context + r"\b[ ,:]*")
        statutory = True
    # Legal qualifiers and polite particles can occur in either order. Remove
    # only these complete suffixes, never an arbitrary remainder of a question.
    for _ in range(5):
        suffix = re.search(
            r"\s+(?:thoi ma|thoi|vay|the|v|z|a|ha|nhi|nhe|nha|voi|"
            r"giup (?:minh|toi)|cho (?:minh|toi))$",
            fold_vietnamese(value),
        )
        if suffix:
            value = value[:suffix.start()].rstrip(" ,:")
            continue
        suffix = re.search(r"\s+" + legal_context + r"$", fold_vietnamese(value))
        if suffix:
            value = value[:suffix.start()].strip(" ,:")
            statutory = True
            continue
        break

    folded = fold_vietnamese(value)
    term = None
    explicit_definition = True
    match = re.fullmatch(r"(.+?)\s+(?:la gi|nghia la gi|duoc hieu la gi)", folded)
    if match:
        term = value[match.start(1):match.end(1)]
    else:
        match = re.fullmatch(
            r"(?:ban )?(giai thich|dinh nghia)(?: (khai niem|tu|thuat ngu))?\s+(.+)",
            folded,
        )
        if match:
            term = value[match.start(3):match.end(3)]
            explicit_definition = match[1] == "dinh nghia" or match[2] is not None
    if term is None:
        return None
    term = _clean_term(term)
    explanatory_prefix = re.match(
        r"^(?:ban )?giai thich(?: (?:giup|cho) (?:minh|toi))?"
        r"(?: (?:khai niem|tu|thuat ngu))?\s+",
        fold_vietnamese(term),
    )
    if explanatory_prefix:
        term = _clean_term(term[explanatory_prefix.end():])
    term_folded = fold_vietnamese(term)
    # Definition/categorization of a concrete case must continue through normal
    # legal routing. Do not drop a second question or a case-specific condition.
    if (
        not term
        or len(term) > 150
        or re.search(r"[?!;:]", term)
        or re.search(
            r"\b(?:dieu kien|thu tuc|ho so|nguyen tac|trinh tu|nghia vu|"
            r"quyen va nghia vu|truong hop|trach nhiem|tham quyen|"
            r"pham vi|cach thuc|doi tuong|bao nhieu|co duoc|duoc khong|"
            r"can|duoc|nen|phai|can lam|phai lam|de duoc|can gi|tai sao|vi sao|neu|nhung|"
            r"thi sao|la gi|la sao|o tinh|tai tinh)\b",
            term_folded,
        )
        or re.search(r"\b(?:toi|minh|cua ban|nha ban|gia dinh|truong hop)\b", term_folded)
        or re.match(r"^viec\b", term_folded)
        or re.search(r"\b(?:dang bi|da bi|sap bi)\b", term_folded)
        or re.search(
            r"\b(?:dat|thua|manh|mieng|giay|so|khoan)\s+(?:nay|do|ay)\b",
            term_folded,
        )
    ):
        return None
    # A legal-definition prefix is accepted only as a prefix to the term.
    prefix = re.match(r"^(?:khai niem|dinh nghia)(?: phap ly)?(?: cua)?\s+", term_folded)
    if prefix:
        statutory = statutory or "phap ly" in prefix.group()
        explicit_definition = True
        term = _clean_term(term[prefix.end():])
    if not term:
        return None
    return ConceptRequest(
        term=term, statutory=statutory, explicit_definition=explicit_definition,
    )


def definition_clause(text: str) -> str | None:
    """Return a complete numbered definition after its structural header.

    No sentence, condition or exception is cut. This helper does not establish
    source authenticity; callers must use verified definition-source chunks.
    """
    value = unicodedata.normalize("NFC", str(text)).strip()
    header = re.search(r"\bgiải thích từ ngữ\b\s*", value, re.IGNORECASE)
    if header:
        value = value[header.end():].strip()
    if not re.match(r"^\d+\.\s+\S", value):
        return None
    if len(re.findall(r"(?:^|\n)\s*\d+\.\s+", value)) != 1:
        return None
    return value


def definition_term(text: str) -> str | None:
    """Derive the term from the source's complete ‘number. term là …’ clause."""
    clause = definition_clause(text)
    if clause is None:
        return None
    match = re.match(
        r"^\d+\.\s+((?:[^()]|\([^)]*\))+?)\s+là\s+\S",
        clause, re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return None
    # Parenthetical shorthand is an alias in the source, not part of the term.
    return re.sub(r"\s*\(sau đây gọi là[^)]*\)\s*$", "", match[1], flags=re.IGNORECASE).strip()


def definition_match_term(term: str) -> str:
    """Normalize only explicit, unambiguous domain aliases for exact lookup."""
    folded = fold_vietnamese(QueryRewriter().rewrite(term)).strip()
    aliases = {
        "giay chung nhan": "giay chung nhan quyen su dung dat, quyen so huu tai san gan lien voi dat",
        "giay chung nhan quyen su dung dat": "giay chung nhan quyen su dung dat, quyen so huu tai san gan lien voi dat",
        "thu hoi dat": "nha nuoc thu hoi dat",
        "giao dat": "nha nuoc giao quyen su dung dat",
        "nha nuoc giao dat": "nha nuoc giao quyen su dung dat",
        "cho thue dat": "nha nuoc cho thue quyen su dung dat",
        "nha nuoc cho thue dat": "nha nuoc cho thue quyen su dung dat",
    }
    return aliases.get(folded, folded)
