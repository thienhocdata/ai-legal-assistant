"""Opt-in OpenRouter adapter restricted to free inference for this demo."""

from typing import Any

from .openai_compatible_provider import OpenAICompatibleProvider


DEFAULT_OPENROUTER_MODEL = "baidu/ernie-5.5-flash-preview:free"


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_OPENROUTER_MODEL,
        timeout_seconds: float = 45.0,
        max_output_tokens: int = 8192,
        max_retries: int = 0,
        client: Any | None = None,
    ) -> None:
        selected = model.strip()
        if selected != "openrouter/free" and not selected.endswith(":free"):
            raise ValueError("OpenRouter demo chỉ chấp nhận model miễn phí (:free hoặc openrouter/free).")
        super().__init__(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model=selected,
            provider_name="openrouter",
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
            max_retries=max_retries,
            client=client,
        )

    def _request_body(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        body = super()._request_body(system_prompt, user_prompt)
        # No paid model fallback or paid plugins. The endpoint also filters out
        # providers with a nonzero prompt/completion token price.
        body["provider"] = {"max_price": {"prompt": 0, "completion": 0, "request": 0}}
        # ERNIE requires reasoning on this endpoint. Leave the model's default;
        # explicitly disabling it makes OpenRouter reject the entire request.
        return body
