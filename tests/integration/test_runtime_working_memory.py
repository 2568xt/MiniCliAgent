from minicliagent.core.llm.types import ModelRequest, ModelResponse
from minicliagent.core.runtime.agent_runtime import AgentRuntime
from minicliagent.core.tools.registry import ToolRegistry


class CapturingProvider:
    def __init__(self) -> None:
        self.last_request: ModelRequest | None = None

    def create_response(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        return ModelResponse(stop_reason="end_turn", text="ok", tool_calls=[])


def test_runtime_passes_working_memory_to_context_manager() -> None:
    provider = CapturingProvider()
    runtime = AgentRuntime(provider=provider, tool_registry=ToolRegistry(), system_prompt="system")
    runtime.session_state["s1"] = {"loaded_skills": ["demo"], "active_task": 1}

    runtime.run_turn("s1", "hello")

    assert provider.last_request is not None
    assert provider.last_request.messages[0]["role"] == "user"
    assert provider.last_request.messages[0]["content"] == "hello"
    assert "loaded_skills" in provider.last_request.system
