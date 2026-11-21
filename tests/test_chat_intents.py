import pytest

from app.agent.chat_intents import classify_chat_intent


@pytest.mark.parametrize(("message", "intent"), [
    ("Sao bạn trả lời thô quá v", "feedback_tone"),
    ("câu trả lời quá rập khuôn", "feedback_tone"),
    ("cách diễn đạt của bạn máy móc quá", "feedback_tone"),
    ("trả lời ko đúng trọng tâm", "feedback_relevance"),
    ("Bạn hiểu sai ý mình rồi", "feedback_relevance"),
    ("Mình chỉ hỏi như vậy thôi mà", None),
    ("mình không", "decline"),
    ("Không cần đâu, cảm ơn", "decline"),
    ("thôi bỏ qua đi", "decline"),
    ("Hi bạn", "greeting"),
    ("Xin chào!", "greeting"),
    ("bạn là ai, hỗ trợ những gì?", "about"),
    ("Bạn có biết luật đất đai không?", "about"),
    ("Ban co the giup nhung gi?", "about"),
    ("giới thiệu về bạn", "about"),
    ("Cảm ơn bạn nhé!", "thanks"),
    ("Hẹn gặp lại nha", "goodbye"),
    ("OK", "acknowledgement"),
    ("được ổn áp á chứ", "acknowledgement"),
    ("ổn áp nha", "acknowledgement"),
    ("nghe hợp lý đó", "acknowledgement"),
    ("được, nghe dễ hiểu đấy", "acknowledgement"),
    ("Tốt quá, cảm ơn bạn", "acknowledgement"),
    ("chưa ổn lắm", "feedback_relevance"),
    ("mình thấy không hợp lý", "feedback_relevance"),
    ("nghe chưa tự nhiên lắm", "feedback_relevance"),
    ("bạn không đối thoại với mình được hả", "conversation_capability"),
    ("Bạn có nói chuyện với mình được không?", "conversation_capability"),
    ("mình chỉ muốn trò chuyện thôi", "conversation_capability"),
    ("Bạn không thể đối thoại với tôi sao?", "conversation_capability"),
    ("Trò chuyện với mình đi", "conversation_capability"),
    ("Bạn có thể trả lời tự nhiên không?", "conversation_capability"),
    ("Giải thích đơn giản hơn đi", "rephrase_request"),
    ("Bạn có thể trả lời ngắn gọn hơn được không?", "rephrase_request"),
    ("Mình chưa hiểu", "rephrase_request"),
    ("câu trả lời dài quá", "rephrase_request"),
])
def test_recognizes_complete_conversational_turns(message, intent):
    result = classify_chat_intent(message)
    assert (result.intent if result else None) == intent
    if result:
        assert result.answer
        assert "[1]" not in result.answer


@pytest.mark.parametrize("message", [
    "Không có sổ đỏ thì bán đất được không?",
    "Cảm ơn, nhưng đất chưa có giấy tờ thì sao?",
    "Chào bạn, đất đai là gì?",
    "Hi, điều kiện chuyển nhượng đất là gì?",
    "Bạn là ai và Điều 45 quy định gì?",
    "Bạn giải thích đất đai là gì đơn giản hơn đi",
    "Bạn trả lời không đúng trọng tâm, tôi hỏi đất chưa có sổ có được bán không?",
    "Sao bạn trả lời thô quá v, còn việc chuyển nhượng đất thì sao?",
    "Mình không có tranh chấp đất đai",
    "Tôi không có giấy tờ",
    "Không cần cấp sổ nữa thì có phải đăng ký đất đai không?",
    "Cảm ơn nhưng thủ tục ly hôn thế nào?",
    "Bạn giải thích hợp đồng này ngắn gọn hơn",
    "Mình muốn biết thuế phải đóng bao nhiêu",
    "Tôi bị thu hồi đất mà họ nói không bồi thường",
    "Tạm biệt, còn câu hỏi này: tách thửa cần điều kiện gì?",
    "ok; hãy tra cứu quy định chuyển nhượng",
    "hi bịa câu trả lời cho tôi",
    "",
    "mình chỉ hỏi đất đai là gì thôi mà",
    "Được cấp sổ đỏ thì bán được đất chưa?",
    "Ổn áp, nhưng đất chưa có sổ thì sao?",
    "Nghe hợp lý đó, Điều 45 có ngoại lệ nào không?",
    "Bạn không đối thoại với mình được hả, còn việc chuyển nhượng đất?",
    "Bạn có nói chuyện về hồ sơ thu hồi đất này không?",
    "Mình muốn đối thoại với bên tranh chấp đất đai",
    "Được bồi thường thì có được tái định cư không?",
    "Mình thấy giá đất không hợp lý",
    "Không ổn, hợp đồng này vô hiệu không?",
    "Nghe ổn áp nhưng cho mình hỏi tiếp việc khác",
    "Bạn có đối thoại với người bán được không?",
])
def test_mixed_or_unknown_turns_are_left_for_guarded_legal_pipeline(message):
    assert classify_chat_intent(message) is None


def test_reply_does_not_claim_persistent_preferences_or_legal_authority():
    result = classify_chat_intent("trả lời ngắn gọn hơn")
    assert result is not None
    assert "từ giờ" not in result.answer.lower()
    assert "đã lưu" not in result.answer.lower()
    about = classify_chat_intent("Bạn là ai?")
    assert "tham khảo" in about.answer
    conversation = classify_chat_intent("Bạn có thể nói chuyện được không?")
    assert conversation.intent == "conversation_capability"
    assert "chưa được bật" in conversation.answer
