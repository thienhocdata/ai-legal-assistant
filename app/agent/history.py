"""Validate untrusted, bounded, stateless history from any API client."""
from typing import Any


def validate_chat_history(history: Any) -> list[dict[str, str]]:
    if history is None:
        return []
    if not isinstance(history, list) or len(history) > 8:
        raise ValueError("Lịch sử chỉ nhận tối đa 8 tin nhắn.")
    result = []
    total = 0
    for turn in history:
        if (
            not isinstance(turn, dict) or set(turn) != {"role", "content"}
            or not isinstance(turn.get("role"), str)
            or turn.get("role") not in {"user", "assistant"}
            or not isinstance(turn.get("content"), str)
            or not turn["content"].strip() or len(turn["content"]) > 4000
        ):
            raise ValueError("Tin nhắn lịch sử không hợp lệ.")
        total += len(turn["content"])
        result.append({"role": turn["role"], "content": turn["content"].strip()})
    if total > 12000:
        raise ValueError("Lịch sử vượt tổng giới hạn 12000 ký tự.")
    return result
