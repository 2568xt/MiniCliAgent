from minicliagent.cli import main as cli_main


class FakeMessage:
    def __init__(self, sender: str, content: str) -> None:
        self.sender = sender
        self.content = content


class FakeTeamService:
    def send_message(self, sender: str, recipient: str, content: str) -> None:
        self.sent = (sender, recipient, content)

    def read_inbox(self, recipient: str):
        return [FakeMessage("lead", "hello")]


class FakeService:
    def __init__(self) -> None:
        self.team_service = FakeTeamService()


def test_cli_team_send_command(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeService())

    exit_code = cli_main.main(["team", "send", "--from", "lead", "--to", "worker", "--content", "hello"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "sent" in captured.out.lower()


def test_cli_team_inbox_command(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeService())

    exit_code = cli_main.main(["team", "inbox", "--name", "worker"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "lead: hello" in captured.out
