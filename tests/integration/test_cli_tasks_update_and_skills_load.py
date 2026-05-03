from minicliagent.cli import main as cli_main


class FakeTask:
    def __init__(self, task_id: int, subject: str, status: str = "pending") -> None:
        self.id = task_id
        self.subject = subject
        self.status = status


class FakeSkillDocument:
    def __init__(self, name: str, body: str) -> None:
        self.name = name
        self.body = body


class FakeService:
    def __init__(self) -> None:
        self.task_service = self
        self.skill_service = self

    def run_prompt(self, prompt: str, session_id: str = "default") -> str:
        return f"handled:{prompt}:{session_id}"

    def update_task(self, task_id: int, status: str | None = None, owner: str | None = None):
        return FakeTask(task_id, "Updated task", status or "pending")

    def load_skill(self, name: str):
        return FakeSkillDocument(name, "Loaded body")


def test_cli_tasks_update_command(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeService())

    exit_code = cli_main.main(["tasks", "update", "--task-id", "2", "--status", "completed"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "#2 Updated task [completed]" in captured.out


def test_cli_skills_load_command(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeService())

    exit_code = cli_main.main(["skills", "load", "--name", "demo"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Loaded body" in captured.out
