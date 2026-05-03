import os

import pytest

from minicliagent.core.llm.anthropic_provider import AnthropicProvider
from minicliagent.core.llm.types import ModelRequest


@pytest.mark.skipif(os.getenv("RUN_ANTHROPIC_SMOKE") != "1", reason="set RUN_ANTHROPIC_SMOKE=1 to enable")
def test_anthropic_provider_smoke() -> None:
    provider = AnthropicProvider(
        model=os.environ["MINICLIAGENT_MODEL"],
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )
    response = provider.create_response(
        ModelRequest(
            system="You are a test assistant.",
            messages=[{"role": "user", "content": "Reply with ok"}],
            tools=[],
            max_tokens=32,
        )
    )

    assert isinstance(response.text, str)
    assert response.stop_reason in {"end_turn", "max_tokens", "tool_use"}
