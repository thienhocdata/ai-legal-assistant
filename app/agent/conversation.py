from __future__ import annotations

import re
from typing import Any

from .models import QueryAnalysis
from .query_understanding import fold_vietnamese as fold_text


def validate_clarification_context(context: dict[str, Any] | None) -> dict[str, Any] | None:
    if context is None:
        return None
    if not isinstance(context, dict):
        raise ValueError("clarification_context phải là object.")
    question, answers = context.get("question"), context.get("answers", [])
    if not isinstance(question, str) or not question.strip() or len(question) > 2000:
        raise ValueError("Câu hỏi gốc trong context không hợp lệ.")
    if not isinstance(answers, list) or len(answers) > 3 or any(
        not isinstance(answer, str) or not answer.strip() or len(answer) > 2000
        for answer in answers
    ):
        raise ValueError("Context chỉ nhận tối đa 3 lượt bổ sung, mỗi lượt 2000 ký tự.")
    if len(question) + sum(map(len, answers)) > 6000:
        raise ValueError("Context vượt giới hạn 6000 ký tự.")
    return {"question": question.strip(), "answers": [answer.strip() for answer in answers]}


def apply_clarification_reply(
    analysis: QueryAnalysis,
    previous: QueryAnalysis,
    replies: list[str],
) -> None:
    """Resolve only explicitly supplied clarification facts, never a legal outcome.

    Current prices, personal records and guaranteed case outcomes still require
    external evidence, even after the user provides a place or more case details.
    """
    supplied = fold_text(" ".join(replies))
    newly_missing = [kind for kind in analysis.missing_context_types
                     if kind not in previous.missing_context_types]
    unresolved = []
    for context_type in previous.missing_context_types:
        resolved = False
        if context_type == "ambiguous_land_action":
            resolved = bool(re.search(
                r"\b(chuyen nhuong|tang cho|thua ke|chuyen doi|chuyen muc dich|sang dat o)\b",
                supplied,
            ))
        elif context_type == "certificate_issue":
            resolved = bool(re.search(r"\b(ghi sai|sai ten|mat so|bi mat|dinh chinh|thu hoi|huy)\b", supplied))
        elif context_type == "parcel_eligibility":
            has_date = bool(re.search(r"\b(?:nam|tu)\s*(?:19|20)\d{2}\b", supplied))
            has_papers = bool(re.search(r"\b(giay|giay to|viet tay|thua ke|tang cho)\b", supplied))
            resolved = has_date and has_papers
        elif context_type in {"compensation_amount", "construction_facts", "case_outcome"}:
            # A reply can clarify the request, but cannot create missing official
            # sources. Keep the source-gap route instead of inventing a conclusion.
            resolved = bool(supplied.strip())
        if not resolved:
            unresolved.append(context_type)
    analysis.missing_context_types = list(dict.fromkeys(unresolved + newly_missing))
    analysis.missing_source_types = list(dict.fromkeys(
        previous.missing_source_types + analysis.missing_source_types
    ))
    analysis.in_scope = previous.in_scope or analysis.in_scope
    generic_missing_context = not previous.missing_context_types and previous.requires_clarification
    generic_resolved = bool(re.search(
        r"\b(chuyen nhuong|chuyen muc dich|tach thua|hop thua|cap giay|cap so|boi thuong|thu hoi|tranh chap)\b",
        supplied,
    ))
    analysis.requires_clarification = bool(analysis.missing_context_types) or (
        generic_missing_context and not generic_resolved
    )
    analysis.reasons = [reason for reason in analysis.reasons if reason not in {
        "missing_context", "question_too_short", "outside_land_law_scope",
        "requires_source_outside_current_corpus",
    }]
    if analysis.requires_clarification:
        analysis.reasons.append("missing_context")
    if analysis.missing_source_types:
        analysis.reasons.append("requires_source_outside_current_corpus")
    analysis.reasons.append("clarification_context_applied")
