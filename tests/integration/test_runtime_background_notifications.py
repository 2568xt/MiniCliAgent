from pathlib import Path

from minicliagent.core.llm.types import ModelRequest, ModelResponse
from minicliagent.core.runtime.agent_runtime import AgentRuntime
from minicliagent.core.runtime.background_manager import BackgroundManager
from minicliagent.core.tools.registry import ToolRegistry


class NotificationCapturingProvider:
    def __init__(self) -> None:
        self.last_request: ModelRequest | None = None

    def create_response(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        return ModelResponse(stop_reason="end_turn", text="ok", tool_calls=[])


def test_runtime_injects_background_notifications_before_provider_call(tmp_path: Path) -> None:
    provider = NotificationCapturingProvider()
    manager = BackgroundManager(workspace_root=tmp_path)
    manager.start("python -c \"print('hi')\"")

    import time

    deadline = time.time() + 5
    while time.time() < deadline:
        if manager.list_tasks()[0].status != "running":
            break
        time.sleep(0.05)

    runtime = AgentRuntime(
        provider=provider,
        tool_registry=ToolRegistry(),
        system_prompt="system",
        background_manager=manager,
    )
    runtime.run_turn(session_id="s1", user_input="hello")

    assert provider.last_request is not None
    assert any(
        isinstance(message.get("content"), str) and "<background-results>" in message["content"]
        for message in provider.last_request.messages
    )
