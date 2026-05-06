from minicliagent.core.llm.types import ModelRequest, ModelResponse
from minicliagent.core.runtime.agent_runtime import AgentRuntime
from minicliagent.core.runtime.context_manager import ContextManager
from minicliagent.core.tools.registry import ToolRegistry


class CapturingProvider:
    def __init__(self) -> None:
        self.last_request: ModelRequest | None = None

    def create_response(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        return ModelResponse(stop_reason="end_turn", text="ok", tool_calls=[])


class RecordingMemoryService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[dict], str]] = []

    def remember_session(self, session_id: str, messages: list[dict], source: str):
        self.calls.append((session_id, list(messages), source))
        return type("Result", (), {"written": True})()


def test_runtime_triggers_memory_compact_hook_once_per_compacted_message_count() -> None:
    provider = CapturingProvider()
    memory_service = RecordingMemoryService()
    runtime = AgentRuntime(
        provider=provider,
        tool_registry=ToolRegistry(),
        system_prompt="system",
        context_manager=ContextManager(history_max_messages=1),
        memory_service=memory_service,
    )
    runtime.message_store.append("s1", {"role": "user", "content": "older"})
    runtime.message_store.append("s1", {"role": "assistant", "content": "old answer"})

    runtime.run_turn("s1", "new")
    runtime.run_turn("s1")

    assert [(session_id, source) for session_id, _, source in memory_service.calls] == [
        ("s1", "compact_hook"),
        ("s1", "compact_hook"),
    ]
    assert len(memory_service.calls[0][1]) == 3
    assert len(memory_service.calls[1][1]) == 4


def test_runtime_adds_memory_search_hint_to_system_prompt_when_memory_enabled() -> None:
    provider = CapturingProvider()
    runtime = AgentRuntime(
        provider=provider,
        tool_registry=ToolRegistry(),
        system_prompt="system",
        memory_service=RecordingMemoryService(),
    )

    runtime.run_turn("s1", "hello")

    assert provider.last_request is not None
    assert "memory_search" in provider.last_request.system
