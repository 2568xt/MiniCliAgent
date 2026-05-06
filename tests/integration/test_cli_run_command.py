import builtins
import io
from datetime import datetime
from types import SimpleNamespace

from minicliagent.app.agent_service import create_agent_service
from minicliagent.cli import main as cli_main


class FakeService:
    def __init__(self, sessions_dir=None) -> None:
        self.calls: list[tuple[str, str]] = []
        self.finalized_sessions: list[str] = []
        self.settings = SimpleNamespace(sessions_dir=sessions_dir)

    def run_prompt(self, prompt: str, session_id: str = "default") -> str:
        self.calls.append((prompt, session_id))
        return f"handled:{prompt}:{session_id}"

    def finalize_session(self, session_id: str) -> None:
        self.finalized_sessions.append(session_id)


class StreamingFakeService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def run_prompt(self, prompt: str, session_id: str = "default", on_text_delta=None) -> str:
        self.calls.append((prompt, session_id))
        if on_text_delta is not None:
            on_text_delta("chunk-1")
            on_text_delta("chunk-2")
        return "aggregate-output"


def test_cli_run_command_uses_agent_service(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeService())

    exit_code = cli_main.main(["run", "--prompt", "hello", "--session", "s1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "handled:hello:s1" in captured.out


def test_cli_run_without_session_uses_started_at_session_id(monkeypatch, tmp_path) -> None:
    service = FakeService(sessions_dir=tmp_path)
    stream = io.StringIO()
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: service)
    monkeypatch.setattr(
        cli_main,
        "datetime",
        type("FixedDatetime", (), {"now": staticmethod(lambda: datetime(2026, 5, 4, 1, 32, 45))}),
        raising=False,
    )

    exit_code = cli_main.main(["run", "--prompt", "hello"], stdout=stream)

    assert exit_code == 0
    assert "Session: 20260504-013245\n" in stream.getvalue()
    assert service.calls == [("hello", "20260504-013245")]


def test_cli_run_without_session_avoids_existing_timestamp_collision(monkeypatch, tmp_path) -> None:
    (tmp_path / "20260504-013245.json").write_text("[]")
    service = FakeService(sessions_dir=tmp_path)
    stream = io.StringIO()
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: service)
    monkeypatch.setattr(
        cli_main,
        "datetime",
        type("FixedDatetime", (), {"now": staticmethod(lambda: datetime(2026, 5, 4, 1, 32, 45))}),
        raising=False,
    )

    exit_code = cli_main.main(["run", "--prompt", "hello"], stdout=stream)

    assert exit_code == 0
    assert "Session: 20260504-013245-2\n" in stream.getvalue()
    assert service.calls == [("hello", "20260504-013245-2")]
    assert (tmp_path / "20260504-013245-2.json").read_text() == "[]"


def test_cli_run_without_prompt_enters_interactive_mode(monkeypatch, capsys) -> None:
    service = FakeService()
    inputs = iter(["hello", "", "quit"])
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: service)
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    exit_code = cli_main.main(["run", "--session", "chat"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "handled:hello:chat" in captured.out
    assert service.calls == [("hello", "chat")]
    assert service.finalized_sessions == ["chat"]


def test_cli_run_prompt_does_not_finalize_session(monkeypatch) -> None:
    service = FakeService()
    stream = io.StringIO()
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: service)

    exit_code = cli_main.main(["run", "--prompt", "hello", "--session", "s1"], stdout=stream)

    assert exit_code == 0
    assert service.finalized_sessions == []


def test_cli_run_command_streams_chunks_without_reprinting_aggregate(monkeypatch) -> None:
    service = StreamingFakeService()
    stream = io.StringIO()
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: service)

    exit_code = cli_main.main(["run", "--prompt", "hello", "--session", "s1"], stdout=stream)

    assert exit_code == 0
    assert stream.getvalue() == "chunk-1chunk-2\n"
    assert service.calls == [("hello", "s1")]


class MemoryServiceStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[dict], str]] = []
        self.summarizer = None

    def remember_session(self, session_id: str, messages: list[dict], source: str):
        self.calls.append((session_id, list(messages), source))
        return type("Result", (), {"written": True})()


class FakeMemorySummarizer:
    def summarize(self, session_id: str, messages: list[dict], source: str) -> list[str]:
        return ["Remember: the user likes markdown-first notes."]


class FullFlowService:
    def __init__(self, sessions_dir) -> None:
        self.settings = SimpleNamespace(sessions_dir=sessions_dir)
        self.calls: list[tuple[str, str]] = []
        self.finalized_sessions: list[str] = []
        self.messages_by_session: dict[str, list[dict]] = {}
        self.memory_service = MemoryServiceStub()
        self.memory_service.summarizer = FakeMemorySummarizer()
        self.task_service = SimpleNamespace()
        self.skill_service = SimpleNamespace()
        self.team_service = SimpleNamespace()
        self.worktree_service = SimpleNamespace()

    def run_prompt(self, prompt: str, session_id: str = "default") -> str:
        self.calls.append((prompt, session_id))
        self.messages_by_session.setdefault(session_id, []).append({"role": "user", "content": prompt})
        self.messages_by_session[session_id].append({"role": "assistant", "content": "ack"})
        return "ack"

    def finalize_session(self, session_id: str) -> None:
        self.finalized_sessions.append(session_id)
        messages = self.messages_by_session.get(session_id, [])
        self.memory_service.remember_session(session_id, messages, "exit_hook")


def test_cli_run_command_full_memory_flow(monkeypatch, tmp_path, capsys) -> None:
    service = FullFlowService(tmp_path / ".minicliagent" / "sessions")
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: service)
    inputs = iter(["remember markdown-first notes", "quit"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    exit_code = cli_main.main(["run", "--session", "s1"], stdout=io.StringIO())

    assert exit_code == 0
    assert service.calls == [("remember markdown-first notes", "s1")]
    assert service.finalized_sessions == ["s1"]
    assert service.memory_service.calls == [("s1", service.messages_by_session["s1"], "exit_hook")]


def test_memory_integration_with_real_create_agent_service(monkeypatch, tmp_path) -> None:
    """Exercise the memory path through the actual create_agent_service assembly.

    This test verifies that when memory is enabled and a provider is available,
    the real create_agent_service properly wires memory_service into AgentService,
    and finalize_session triggers the exit hook.
    """
    from minicliagent.app.agent_service import create_agent_service
    from minicliagent.core.llm.anthropic_provider import AnthropicProvider
    from minicliagent.core.llm.types import ModelResponse, ModelRequest

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    env = {
        "MINICLIAGENT_WORKSPACE": str(workspace),
        "MINICLIAGENT_MEMORY_ENABLED": "1",
        "MINICLIAGENT_MODEL": "fake-model",
        "ANTHROPIC_API_KEY": "fake-key",
    }

    class FakeAnthropicProvider:
        def __init__(self, model=None, base_url=None):
            self.model = model
            self.base_url = base_url
            self.requests: list[ModelRequest] = []

        def create_response(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            return ModelResponse(stop_reason="end_turn", text="ok", tool_calls=[])

    monkeypatch.setattr(
        "minicliagent.app.agent_service.AnthropicProvider",
        FakeAnthropicProvider,
    )

    service = create_agent_service(env)

    assert service.memory_service is not None
    assert service.settings.memory_enabled is True
    assert service.settings.memory_summary_path == workspace / ".minicliagent" / "memory.md"
    assert service.settings.memory_dir == workspace / ".minicliagent" / "memory"

    result = service.run_prompt("hello world", session_id="s1")
    assert result == "ok"

    service.finalize_session("s1")

    # Verify memory fragment was written
    fragments = list((workspace / ".minicliagent" / "memory").glob("*.md"))
    assert len(fragments) >= 1
    content = fragments[0].read_text()
    assert content.strip() != ""


def test_memory_disabled_does_not_create_memory_service(monkeypatch, tmp_path) -> None:
    """When MINICLIAGENT_MEMORY_ENABLED=0, memory_service should be None."""
    from minicliagent.app.agent_service import create_agent_service

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    class FakeProvider:
        def __init__(self, model=None, base_url=None):
            pass

        def create_response(self, request):
            from minicliagent.core.llm.types import ModelResponse
            return ModelResponse(stop_reason="end_turn", text="ok", tool_calls=[])

    monkeypatch.setattr(
        "minicliagent.app.agent_service.AnthropicProvider",
        FakeProvider,
    )

    env = {
        "MINICLIAGENT_WORKSPACE": str(workspace),
        "MINICLIAGENT_MEMORY_ENABLED": "0",
        "MINICLIAGENT_MODEL": "fake",
        "ANTHROPIC_API_KEY": "fake-key",
    }

    service = create_agent_service(env)
    assert service.memory_service is None

    # run_prompt and finalize_session should not throw
    result = service.run_prompt("hello", session_id="s1")
    assert result == "ok"
    service.finalize_session("s1")
