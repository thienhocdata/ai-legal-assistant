"""Bounded handling for conversational turns that do not ask for legal facts.

This is a current-message classifier, not a conversational language model. A
mixed message with a legal question must continue through the normal legal
pipeline. Callers must run the input guardrail before using this classifier.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from .query_understanding import fold_vietnamese


@dataclass(frozen=True)
class ChatIntentReply:
    intent: str
    answer: str


# Only conversational filler may surround a complete recognized expression;
# never use an arbitrary ".*" suffix that could consume a second question.
_TAIL = r"(?: (?:a|ah|ha|nha|nhe|nhi|nua|roi|di|thoi|ma|v|z|vay|the|oi|ni|chu|do|day|sao|nhe ban|nha ban))*"
_PREFIX = r"(?:(?:hmm|hm|um|ua|nay|oi) )*"
_LEGAL_CONTENT = re.compile(
    r"\b(?:dat|thua|so do|so hong|so dat|cap so|giay to|giay chung nhan|"
    r"quyen su dung|chuyen nhuong|sang ten|boi thuong|thu hoi|tai dinh cu|"
    r"tranh chap|hoa giai|quy hoach|thue|ly hon|hop dong|thua ke|"
    r"nghi dinh|thong tu|dieu \d+|khoan \d+|ho so)\b"
)


def _normalized_message(question: str) -> str:
    folded = fold_vietnamese(question)
    folded = re.sub(r"\b(?:ko|k0|hong)\b", "khong", folded)
    folded = re.sub(r"\bdc\b", "duoc", folded)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", folded)).strip()


def _matches(message: str, expression: str) -> bool:
    return re.fullmatch(_PREFIX + "(?:" + expression + ")" + _TAIL, message) is not None


def classify_chat_intent(question: str) -> ChatIntentReply | None:
    """Return a non-legal reply only for an explicitly recognized whole turn.

    The returned response neither retrieves law nor asserts legal conclusions.
    No preference or history is persisted, and unknown messages return None.
    """
    message = _normalized_message(question)
    if not message:
        return None

    if _matches(message, r"(?:ban|cau|anh|chi) la ai(?: (?:va )?(?:ban )?(?:ho tro|lam duoc|giup duoc) (?:nhung )?gi)?|"
                r"(?:ban|cau) (?:lam duoc|giup duoc|ho tro) (?:nhung )?gi|"
                r"(?:ban|cau) co the (?:lam|giup|ho tro) (?:nhung )?gi|"
                r"gioi thieu (?:ve )?(?:ban|ban than)|"
                r"(?:day|ung dung nay) la gi|ban co biet luat dat dai khong"):
        return ChatIntentReply(
            "about",
            "Mình là trợ lý tra cứu pháp luật đất đai của Minh Long. "
            "Bạn có thể hỏi về chuyển nhượng, cấp Giấy chứng nhận, thu hồi, "
            "bồi thường hoặc tranh chấp đất đai. Mình giúp tìm và giải thích "
            "căn cứ trong kho hiện có; thông tin chỉ phục vụ tham khảo.",
        )

    # Feedback may mention the assistant's response, but a message that also
    # supplies legal content is left intact for the legal/question-aware path.
    # "diễn đạt" contains ASCII "dat" after folding but is feedback about
    # wording, not an independent reference to đất.
    if _LEGAL_CONTENT.search(re.sub(r"\bdien dat\b", "", message)):
        return None

    conversation = (
        r"(?:ban|cau) (?:(?:co the|co|khong the|khong) )?"
        r"(?:noi chuyen|tro chuyen|doi thoai|tra loi tu nhien|tra loi binh thuong)"
        r"(?: (?:voi|cung) (?:minh|toi))?(?: duoc khong| duoc| khong)?|"
        r"(?:minh|toi) (?:chi )?(?:muon )?(?:noi chuyen|tro chuyen|doi thoai)"
        r"(?: (?:voi|cung) (?:ban|cau))?|"
        r"(?:noi chuyen|tro chuyen|doi thoai)(?: (?:voi|cung) (?:minh|toi))?"
    )
    if _matches(message, conversation):
        return ChatIntentReply(
            "conversation_capability",
            "Mình vẫn nhận lời chào và góp ý, nhưng chế độ hiện tại hiểu hội thoại "
            "còn hạn chế. Phần đối thoại linh hoạt bằng mô hình chưa được bật.",
        )

    if _matches(message, r"(?:xin chao|chao|hello|hi|hey)(?: ban|cau|anh|chi|ong)?"):
        return ChatIntentReply(
            "greeting", "Chào bạn! Mình có thể giúp bạn tìm hiểu và tra cứu về pháp luật đất đai. Bạn đang muốn tìm hiểu vấn đề gì?",
        )

    if _matches(message, r"(?:minh|toi|em|anh|chi) (?:khong|khong can|khong muon|chua can)|"
                r"khong(?: can| can dau| can cam on| can dau cam on| cam on| dau| muon| muon nua)?|"
                r"thoi(?: khong can| bo qua)?|bo qua"):
        return ChatIntentReply(
            "decline", "Được nhé. Khi cần tìm hiểu điều gì khác, bạn cứ nhắn mình.",
        )

    if _matches(message, r"(?:cam on|thank you|thanks)(?: ban|cau|nhieu| rat nhieu)?|"
                r"(?:minh|toi|em) cam on(?: ban|cau)?"):
        return ChatIntentReply("thanks", "Không có gì nhé. Mong là phần giải thích giúp ích cho bạn.")

    if _matches(message, r"tam biet|hen gap lai|bye|goodbye|chao tam biet"):
        return ChatIntentReply("goodbye", "Tạm biệt bạn, khi cần tra cứu bạn cứ quay lại nhé.")

    acknowledgement = (
        r"ok|oke|okay|duoc|duoc roi|hieu roi|(?:minh|toi) hieu roi|"
        r"(?:duoc )?(?:(?:nghe|co ve|thay) )?"
        r"(?:on(?: ap)?|hop ly|tot|hay|de hieu|ro rang)(?: qua| lam)?"
        r"(?: cam on(?: ban)?)?"
    )
    if _matches(message, acknowledgement):
        return ChatIntentReply("acknowledgement", "Ừ, bạn cứ nhắn nếu còn điều gì muốn làm rõ nhé.")

    negative_feedback = (
        r"(?:(?:(?:minh|toi) (?:thay|nghe)|nghe|co ve) )?"
        r"(?:chua on|khong on|chua hop ly|khong hop ly|chua tot|chua hay|"
        r"khong hay|chua tu nhien)(?: lam| qua)?"
    )
    if _matches(message, negative_feedback):
        return ChatIntentReply(
            "feedback_relevance",
            "Cảm ơn bạn góp ý. Bạn chỉ giúp mình phần chưa ổn hoặc ý muốn làm rõ nhé, "
            "để mình tập trung vào đúng chỗ đó.",
        )

    tone = (
        r"(?:(?:sao|tai sao) )?(?:ban |cau )?(?:tra loi|noi|giai thich) "
        r"(?:tho|coc loc|kho chiu|bat lich su|kho khan|may moc|rap khuon)(?: qua| the)?|"
        r"(?:cau tra loi|cach (?:tra loi|noi|dien dat))(?: cua ban)? "
        r"(?:qua )?(?:tho|coc loc|kho chiu|bat lich su|kho khan|may moc|rap khuon)(?: qua)?"
    )
    if _matches(message, tone):
        return ChatIntentReply(
            "feedback_tone",
            "Xin lỗi bạn, cách diễn đạt đó hơi khô và máy móc. "
            "Bạn có thể gửi lại câu hỏi hoặc đoạn muốn làm rõ để mình giải thích gần gũi, dễ hiểu hơn.",
        )

    relevance = (
        r"(?:ban |cau )?(?:tra loi|noi|giai thich) "
        r"(?:khong dung trong tam|lac de|khong dung y|khong lien quan|sai trong tam|sai roi)|"
        r"(?:cau tra loi|phan tra loi)(?: cua ban)? "
        r"(?:khong dung trong tam|lac de|khong dung y|khong lien quan)|"
        r"(?:ban |cau )?(?:hieu|tra loi) sai y (?:minh|toi)|"
        r"(?:minh|toi) khong hoi (?:vay|nhu vay)"
    )
    if _matches(message, relevance):
        return ChatIntentReply(
            "feedback_relevance",
            "Mình hiểu, câu trả lời vừa rồi chưa đúng ý bạn. "
            "Bạn gửi lại câu hỏi và ý muốn làm rõ nhé, để mình tập trung vào đúng phần đó.",
        )

    reformulation = (
        r"(?:ban |cau )?(?:co the )?(?:tra loi|noi|viet|giai thich)(?: lai)? "
        r"(?:ngan gon|ngan|don gian|de hieu|cu the|ro rang)(?: hon)?(?: duoc khong)?|"
        r"(?:ban |cau )?(?:tra loi|noi|viet|giai thich) dai(?: dong| qua)?|"
        r"(?:minh|toi) (?:khong hieu|chua hieu)|"
        r"(?:cau tra loi|phan giai thich)(?: cua ban)? (?:dai qua|kho hieu qua|kho hieu)"
    )
    if _matches(message, reformulation):
        return ChatIntentReply(
            "rephrase_request",
            "Được nhé. Bạn gửi lại câu hỏi hoặc đoạn cần giải thích, "
            "mình sẽ tập trung vào ý chính và dùng lời dễ hiểu hơn.",
        )

    return None
