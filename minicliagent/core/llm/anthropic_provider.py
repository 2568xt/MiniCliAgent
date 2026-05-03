from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from anthropic import Anthropic

from minicliagent.core.llm.types import ModelRequest, ModelResponse, TextDeltaCallback, ToolCall


class AnthropicProvider:
    def __init__(self, model: str, base_url: str | None = None) -> None:
        self.model = model
        self.client = Anthropic(base_url=_normalize_base_url(base_url))

    def create_response(
        self,
        request: ModelRequest,
        on_text_delta: TextDeltaCallback | None = None,
    ) -> ModelResponse:
        if on_text_delta is None:
            raw_response = self.client.messages.create(
                model=self.model,
                system=request.system,
                messages=request.messages,
                tools=request.tools,
                max_tokens=request.max_tokens,
            )
            return _model_response_from_message(raw_response)

        with self.client.messages.stream(
            model=self.model,
            system=request.system,
            messages=request.messages,
            tools=request.tools,
            max_tokens=request.max_tokens,
        ) as stream:
            for text in stream.text_stream:
                on_text_delta(text)
            final_message = stream.get_final_message()
        return _model_response_from_message(final_message)


def _model_response_from_message(raw_message) -> ModelResponse:
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    for block in raw_message.content:
        if getattr(block, "type", None) == "text":
            text_parts.append(block.text)
        elif getattr(block, "type", None) == "tool_use":
            tool_calls.append(ToolCall(id=block.id, name=block.name, input=block.input))
    return ModelResponse(
        stop_reason=raw_message.stop_reason,
        text="".join(text_parts),
        tool_calls=tool_calls,
    )


def _normalize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return base_url

    parsed = urlparse(base_url)
    if parsed.netloc != "api.minimaxi.com":
        return base_url

    normalized_path = parsed.path.rstrip("/") or "/"
    if normalized_path in {"/v1", "/v1/messages", "/anthropic/v1", "/anthropic/v1/messages"}:
        return urlunparse((parsed.scheme, parsed.netloc, "/anthropic", "", "", ""))

    return base_url
