from minicliagent.cli import main as cli_main


class FakeSkillService:
    def load_skill(self, name: str):
        raise KeyError(name)


class FakeTaskService:
    def update_task(self, task_id: int, status: str | None = None, owner: str | None = None):
        raise FileNotFoundError(f"task_{task_id}.json")


class FakeWorktreeService:
    def create(self, name: str, branch: str, task_id: int | None = None):
        raise RuntimeError("Worktree manager unavailable")


class FakeSkillServiceContainer:
    def __init__(self) -> None:
        self.skill_service = FakeSkillService()


class FakeTaskServiceContainer:
    def __init__(self) -> None:
        self.task_service = FakeTaskService()


class FakeWorktreeServiceContainer:
    def __init__(self) -> None:
        self.worktree_service = FakeWorktreeService()


def test_cli_skills_load_unknown_skill_returns_readable_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeSkillServiceContainer())

    exit_code = cli_main.main(["skills", "load", "--name", "missing"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Unknown skill" in captured.err


def test_cli_tasks_update_unknown_task_returns_readable_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeTaskServiceContainer())

    exit_code = cli_main.main(["tasks", "update", "--task-id", "99", "--status", "completed"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Task not found" in captured.err


def test_cli_worktree_create_without_git_repo_returns_readable_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeWorktreeServiceContainer())

    exit_code = cli_main.main(["worktree", "create", "--name", "demo", "--branch", "wt/demo"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Worktree is unavailable" in captured.err
