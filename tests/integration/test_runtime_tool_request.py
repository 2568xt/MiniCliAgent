from minicliagent.core.llm.types import ModelRequest, ModelResponse
from minicliagent.core.runtime.agent_runtime import AgentRuntime
from minicliagent.core.tools.models import ToolResult, ToolSpec
from minicliagent.core.tools.registry import ToolRegistry


class CapturingProvider:
    def __init__(self) -> None:
        self.last_request: ModelRequest | None = None

    def create_response(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        return ModelResponse(stop_reason="end_turn", text="ok", tool_calls=[])


def test_runtime_sends_registered_tools_to_provider() -> None:
    provider = CapturingProvider()
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="echo",
            description="Echo input",
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
            handler=lambda text: ToolResult(content=text),
            tags={"test"},
        )
    )

    runtime = AgentRuntime(provider=provider, tool_registry=registry, system_prompt="system")
    runtime.run_turn(session_id="s1", user_input="hello")

    assert provider.last_request is not None
    assert provider.last_request.tools == [
        {
            "name": "echo",
            "description": "Echo input",
            "input_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }
    ]
