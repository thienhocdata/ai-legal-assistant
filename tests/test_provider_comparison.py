from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation.provider_comparison import ProviderComparisonRunner


SCRIPT_SPEC = importlib.util.spec_from_file_location(
    "compare_answer_providers",
    ROOT / "scripts" / "compare_answer_providers.py",
)
assert SCRIPT_SPEC and SCRIPT_SPEC.loader
SCRIPT_MODULE = importlib.util.module_from_spec(SCRIPT_SPEC)
SCRIPT_SPEC.loader.exec_module(SCRIPT_MODULE)


class _FakeService:
    def __init__(self, provider: str) -> None:
        self.provider = provider

    def answer(self, question: str):
        return {
            "status": "success",
            "answer": f"Câu trả lời cho {question} [1]",
            "provider": self.provider,
            "model": f"{self.provider}-model",
            "latency_ms": 12.0,
            "citations": [{"article_no": 45}, {"article_no": 45}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
            },
            "generation_fallback_reason": None,
        }


def test_comparison_omits_question_and_answer_text_by_default() -> None:
    runner = ProviderComparisonRunner(lambda provider: _FakeService(provider))
    report = runner.run(
        [{"question_id": "Q1", "question": "Điều kiện chuyển nhượng?"}],
        ["extractive", "qwen"],
        dataset_sha256="abc",
    )
    assert report["question_text_stored"] is False
    qwen = report["providers"][1]
    row = qwen["rows"][0]
    assert "question" not in row
    assert "answer" not in row
    assert row["total_tokens"] == 120
    assert row["cited_articles"] == [45]
    assert qwen["summary"]["success_count"] == 1
    assert qwen["summary"]["native_response_count"] == 1


def test_comparison_can_include_answer_for_explicit_synthetic_review() -> None:
    runner = ProviderComparisonRunner(lambda provider: _FakeService(provider))
    report = runner.run(
        [{"question_id": "Q1", "question": "Câu hỏi tổng hợp"}],
        ["gemini"],
        dataset_sha256="abc",
        include_answer_text=True,
    )
    assert report["answer_text_stored"] is True
    assert "Câu trả lời" in report["providers"][0]["rows"][0]["answer"]


def test_fallback_is_not_counted_as_native_provider_response() -> None:
    class _FallbackService:
        def answer(self, question: str):
            return {
                "status": "success",
                "answer": "Extractive fallback [1]",
                "provider": "extractive",
                "citations": [{"article_no": 45}],
                "generation_fallback_reason": "ProviderRequestError",
            }

    report = ProviderComparisonRunner(lambda provider: _FallbackService()).run(
        [{"question_id": "Q1", "question": "Câu hỏi tổng hợp"}],
        ["qwen"],
        dataset_sha256="abc",
    )
    summary = report["providers"][0]["summary"]
    assert summary["fallback_count"] == 1
    assert summary["native_response_count"] == 0


def test_unconfigured_provider_is_reported_without_secret_or_message() -> None:
    def factory(provider: str):
        if provider == "qwen":
            raise ValueError("secret-bearing setup message")
        return _FakeService(provider)

    report = ProviderComparisonRunner(factory).run(
        [{"question_id": "Q1", "question": "Câu hỏi tổng hợp"}],
        ["extractive", "qwen"],
        dataset_sha256="abc",
    )
    qwen = report["providers"][1]
    assert qwen["setup_status"] == "not_configured"
    assert qwen["setup_error_code"] == "ValueError"
    assert "message" not in qwen


def test_duplicate_question_ids_and_unsupported_provider_are_rejected() -> None:
    runner = ProviderComparisonRunner(lambda provider: _FakeService(provider))
    with pytest.raises(ValueError):
        runner.run(
            [
                {"question_id": "Q1", "question": "Một"},
                {"question_id": "Q1", "question": "Hai"},
            ],
            ["extractive"],
            dataset_sha256="abc",
        )
    with pytest.raises(ValueError):
        runner.run(
            [{"question_id": "Q1", "question": "Một"}],
            ["unknown"],
            dataset_sha256="abc",
        )


def test_script_restricts_input_and_output_to_safe_directories(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        SCRIPT_MODULE._resolve_questions(tmp_path / "private_questions.json")
    with pytest.raises(ValueError):
        SCRIPT_MODULE._resolve_output(tmp_path / "comparison.json")
