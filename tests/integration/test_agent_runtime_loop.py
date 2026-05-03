from minicliagent.core.llm.types import ModelRequest, ModelResponse, ToolCall
from minicliagent.core.runtime.agent_runtime import AgentRuntime
from minicliagent.core.tools.models import ToolResult, ToolSpec
from minicliagent.core.tools.registry import ToolRegistry


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def create_response(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            return ModelResponse(
                stop_reason="tool_use",
                text="",
                tool_calls=[ToolCall(id="tool-1", name="echo", input={"text": "hello"})],
            )
        return ModelResponse(
            stop_reason="end_turn",
            text="done",
            tool_calls=[],
        )


class CapturingToolLoopProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.requests: list[ModelRequest] = []

    def create_response(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        self.requests.append(request)
        if self.calls == 1:
            return ModelResponse(
                stop_reason="tool_use",
                text="",
                tool_calls=[ToolCall(id="tool-1", name="echo", input={"text": "hello"})],
            )
        return ModelResponse(stop_reason="end_turn", text="done", tool_calls=[])


class StreamingProvider:
    def create_response(self, request: ModelRequest, on_text_delta=None) -> ModelResponse:
        if on_text_delta is not None:
            on_text_delta("hel")
            on_text_delta("lo")
        return ModelResponse(stop_reason="end_turn", text="hello", tool_calls=[])


def test_agent_runtime_executes_tool_calls_until_end_turn() -> None:
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

    runtime = AgentRuntime(provider=FakeProvider(), tool_registry=registry, system_prompt="system")
    result = runtime.run_turn(session_id="s1", user_input="say hello")

    assert result.output_text == "done"
    assert len(result.messages) >= 3


def test_agent_runtime_replays_tool_use_before_tool_result() -> None:
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
    provider = CapturingToolLoopProvider()
    runtime = AgentRuntime(provider=provider, tool_registry=registry, system_prompt="system")

    runtime.run_turn(session_id="s1", user_input="say hello")

    second_request = provider.requests[1]
    assistant_message = second_request.messages[-2]
    tool_result_message = second_request.messages[-1]

    assert assistant_message["role"] == "assistant"
    assert assistant_message["content"] == [
        {"type": "tool_use", "id": "tool-1", "name": "echo", "input": {"text": "hello"}}
    ]
    assert tool_result_message["role"] == "user"
    assert tool_result_message["content"] == [
        {"type": "tool_result", "tool_use_id": "tool-1", "content": "hello", "is_error": False}
    ]


def test_agent_runtime_streams_text_deltas_while_preserving_final_output() -> None:
    runtime = AgentRuntime(provider=StreamingProvider(), tool_registry=ToolRegistry(), system_prompt="system")
    fragments: list[str] = []

    result = runtime.run_turn(session_id="s1", user_input="say hello", on_text_delta=fragments.append)

    assert fragments == ["hel", "lo"]
    assert result.output_text == "hello"
