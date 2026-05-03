from types import SimpleNamespace

from minicliagent.core.llm.anthropic_provider import AnthropicProvider, _normalize_base_url
from minicliagent.core.llm.types import ModelRequest


def test_normalize_minimax_v1_base_url() -> None:
    assert _normalize_base_url("https://api.minimaxi.com/v1") == "https://api.minimaxi.com/anthropic"


def test_normalize_minimax_anthropic_v1_base_url() -> None:
    assert _normalize_base_url("https://api.minimaxi.com/anthropic/v1") == "https://api.minimaxi.com/anthropic"


def test_leave_other_provider_base_url_unchanged() -> None:
    base_url = "https://api.anthropic.com/v1"

    assert _normalize_base_url(base_url) == base_url


class FakeStream:
    def __init__(self) -> None:
        self.text_stream = iter(["hel", "lo"])
        self.final_message = SimpleNamespace(
            stop_reason="tool_use",
            content=[
                SimpleNamespace(type="text", text="hello"),
                SimpleNamespace(type="tool_use", id="tool-1", name="echo", input={"text": "hi"}),
            ],
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        return None

    def get_final_message(self):
        return self.final_message


def test_anthropic_provider_streams_text_and_preserves_aggregated_response(monkeypatch) -> None:
    provider = AnthropicProvider.__new__(AnthropicProvider)
    provider.model = "claude-test"
    provider.client = SimpleNamespace(messages=SimpleNamespace(stream=lambda **kwargs: FakeStream()))
    fragments: list[str] = []

    response = provider.create_response(
        ModelRequest(system="system", messages=[{"role": "user", "content": "hello"}]),
        on_text_delta=fragments.append,
    )

    assert fragments == ["hel", "lo"]
    assert response.stop_reason == "tool_use"
    assert response.text == "hello"
    assert response.tool_calls[0].name == "echo"
