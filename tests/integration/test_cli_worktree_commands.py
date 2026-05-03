from minicliagent.cli import main as cli_main


class FakeWorktreeRecord:
    def __init__(self, name: str, status: str = "active") -> None:
        self.name = name
        self.status = status


class FakeWorktreeService:
    def create(self, name: str, branch: str, task_id: int | None = None):
        return FakeWorktreeRecord(name)

    def list_all(self):
        return [FakeWorktreeRecord("feature-one")]


class FakeService:
    def __init__(self) -> None:
        self.worktree_service = FakeWorktreeService()


def test_cli_worktree_create(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeService())
    exit_code = cli_main.main(["worktree", "create", "--name", "feature-one", "--branch", "wt/feature-one", "--task-id", "1"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "feature-one" in captured.out


def test_cli_worktree_list(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeService())
    exit_code = cli_main.main(["worktree", "list"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "feature-one" in captured.out
