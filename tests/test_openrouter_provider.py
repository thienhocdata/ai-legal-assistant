import json

import httpx
import pytest

from app.llm_provider.factory import create_llm_provider
from app.llm_provider.openrouter_provider import DEFAULT_OPENROUTER_MODEL, OpenRouterProvider
from app.llm_provider.base import ProviderResponseError


def test_factory_builds_openrouter_without_inheriting_qwen_credentials(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-test-key")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("LLM_MAX_RETRIES", raising=False)
    monkeypatch.delenv("LLM_MAX_OUTPUT_TOKENS", raising=False)
    monkeypatch.setenv("QWEN_API_KEY", "unrelated-key")
    provider = create_llm_provider()
    assert isinstance(provider, OpenRouterProvider)
    assert provider.api_key == "router-test-key"
    assert provider.model == DEFAULT_OPENROUTER_MODEL
    assert provider.base_url == "https://openrouter.ai/api/v1"
    assert provider.max_retries == 0
    assert provider.max_output_tokens == 8192


def test_factory_requires_separate_openrouter_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("QWEN_API_KEY", "unrelated-key")
    with pytest.raises(ValueError, match="Thiếu API key"):
        create_llm_provider("openrouter")


@pytest.mark.parametrize("model", ["", "baidu/ernie-5.5-flash-preview", "openrouter/auto"])
def test_paid_or_automatic_paid_models_are_rejected_before_request(model):
    with pytest.raises(ValueError, match="miễn phí"):
        OpenRouterProvider(api_key="test-key", model=model)


@pytest.mark.parametrize("model", [DEFAULT_OPENROUTER_MODEL, "openrouter/free"])
def test_free_request_has_zero_price_cap_and_reports_actual_model(model):
    def handler(request):
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["model"] == model
        assert "models" not in body
        assert "plugins" not in body
        assert body["provider"]["max_price"] == {"prompt": 0, "completion": 0, "request": 0}
        assert "reasoning" not in body
        assert body["max_tokens"] == 8192
        assert body["messages"][0]["content"] == "source-only system"
        return httpx.Response(200, json={
            "model": DEFAULT_OPENROUTER_MODEL,
            "choices": [{"message": {"content": "Câu trả lời [1]."}, "finish_reason": "stop"}],
            "usage": {"cost": 0, "prompt_tokens": 123, "completion_tokens": 12},
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        response = OpenRouterProvider(api_key="test-key", model=model, client=client).generate(
            system_prompt="source-only system", user_prompt="question with retrieved sources",
        )
    assert response.provider == "openrouter"
    assert response.model == DEFAULT_OPENROUTER_MODEL
    assert response.metadata["requested_model"] == model
    assert response.metadata["usage"]["cost"] == 0


@pytest.mark.parametrize("extra", [
    {"error": {"message": "private upstream error"}},
    {"choices": [{"message": {"content": "Partial answer [1]."}, "finish_reason": "error"}]},
])
def test_http_200_generation_errors_reject_partial_answers(extra):
    body = {"choices": [{"message": {"content": "Partial answer [1]."}}], **extra}
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))) as client:
        provider = OpenRouterProvider(api_key="test-key", client=client)
        with pytest.raises(ProviderResponseError, match="báo lỗi") as raised:
            provider.generate(system_prompt="system", user_prompt="question")
    assert "private upstream error" not in str(raised.value)
