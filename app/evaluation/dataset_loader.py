from __future__ import annotations

from typing import Any


def extract_questions(payload: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Accept legacy arrays or versioned datasets with metadata + questions."""
    if isinstance(payload, list):
        questions = payload
        metadata: dict[str, Any] = {}
    elif isinstance(payload, dict) and isinstance(payload.get("questions"), list):
        questions = payload["questions"]
        raw_metadata = payload.get("dataset_metadata", {})
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    else:
        raise ValueError(
            "Dataset phải là JSON array hoặc object chứa mảng questions."
        )
    if not questions or any(not isinstance(item, dict) for item in questions):
        raise ValueError("Dataset questions phải là mảng object không rỗng.")
    return questions, metadata
