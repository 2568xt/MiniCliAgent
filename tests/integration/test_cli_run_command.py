import builtins
import io

from minicliagent.cli import main as cli_main


class FakeService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def run_prompt(self, prompt: str, session_id: str = "default") -> str:
        self.calls.append((prompt, session_id))
        return f"handled:{prompt}:{session_id}"


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


def test_cli_run_command_streams_chunks_without_reprinting_aggregate(monkeypatch) -> None:
    service = StreamingFakeService()
    stream = io.StringIO()
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: service)

    exit_code = cli_main.main(["run", "--prompt", "hello", "--session", "s1"], stdout=stream)

    assert exit_code == 0
    assert stream.getvalue() == "chunk-1chunk-2\n"
    assert service.calls == [("hello", "s1")]
