from __future__ import annotations

from pathlib import Path
import sys

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm_provider import OpenAICompatibleProvider, ProviderRequestError, ProviderResponseError


def test_openai_compatible_provider_parses_answer_and_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.url.path.endswith("/chat/completions")
        assert b'"max_tokens":800' in request.content
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Kết luận [1]."}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 10},
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
        provider_name="qwen",
        client=client,
    )
    response = provider.generate(system_prompt="system", user_prompt="question")
    assert response.text == "Kết luận [1]."
    assert response.provider == "qwen"
    assert response.metadata["usage"]["prompt_tokens"] == 100


def test_openai_compatible_provider_rejects_malformed_payload() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"choices": []}))
    )
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
        provider_name="qwen",
        client=client,
    )
    try:
        provider.generate(system_prompt="system", user_prompt="question")
    except RuntimeError as exc:
        assert "payload" in str(exc)
    else:
        raise AssertionError("Malformed provider payload must be rejected.")


def test_provider_retries_429_once() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, json={"error": "rate limited"})
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Đáp án [1]."}}]},
        )

    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
        provider_name="qwen",
        max_retries=1,
        retry_backoff_seconds=0,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    assert provider.generate(system_prompt="system", user_prompt="question").text
    assert calls == 2


def test_provider_retries_timeout_once() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout("timed out", request=request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Đáp án [1]."}}]},
        )

    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
        provider_name="qwen",
        max_retries=1,
        retry_backoff_seconds=0,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    assert provider.generate(system_prompt="system", user_prompt="question").text
    assert calls == 2


def test_provider_does_not_retry_authentication_error() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(401, json={"error": "unauthorized"})

    provider = OpenAICompatibleProvider(
        api_key="bad-key",
        base_url="https://example.test/v1",
        model="test-model",
        provider_name="qwen",
        max_retries=2,
        retry_backoff_seconds=0,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ProviderRequestError):
        provider.generate(system_prompt="system", user_prompt="question")
    assert calls == 1


def test_factory_builds_qwen_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.llm_provider import create_llm_provider

    monkeypatch.setenv("QWEN_API_KEY", "test-key")
    monkeypatch.setenv("QWEN_MODEL", "qwen-test")
    provider = create_llm_provider("qwen")
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.model == "qwen-test"


def _provider_with_choice(choice: dict) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
        provider_name="qwen",
        client=httpx.Client(transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json={"choices": [choice]}),
        )),
    )


def test_provider_rejects_truncated_answer_even_with_citation_marker() -> None:
    provider = _provider_with_choice({
        "message": {"content": "Kết luận [1], với điều kiện"},
        "finish_reason": "length",
    })
    with pytest.raises(ProviderResponseError, match="bị cắt"):
        provider.generate(system_prompt="system", user_prompt="question")


@pytest.mark.parametrize("content", [None, 123, ["Đáp án [1]."], {"text": "Đáp án [1]."}, "", "  "])
def test_provider_rejects_missing_or_nontext_content(content) -> None:
    provider = _provider_with_choice({
        "message": {"content": content}, "finish_reason": "stop",
    })
    with pytest.raises(ProviderResponseError, match="nội dung văn bản"):
        provider.generate(system_prompt="system", user_prompt="question")


def test_provider_preserves_successful_finish_reason() -> None:
    provider = _provider_with_choice({
        "message": {"content": "  Đáp án đầy đủ [1].  "}, "finish_reason": "stop",
    })
    response = provider.generate(system_prompt="system", user_prompt="question")
    assert response.text == "Đáp án đầy đủ [1]."
    assert response.metadata["finish_reason"] == "stop"
