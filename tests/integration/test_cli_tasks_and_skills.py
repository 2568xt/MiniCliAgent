from minicliagent.cli import main as cli_main


class FakeTask:
    def __init__(self, task_id: int, subject: str) -> None:
        self.id = task_id
        self.subject = subject


class FakeSkill:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeService:
    def __init__(self) -> None:
        self.task_service = self
        self.skill_service = self

    def run_prompt(self, prompt: str, session_id: str = "default") -> str:
        return f"handled:{prompt}:{session_id}"

    def create_task(self, subject: str, description: str):
        return FakeTask(1, subject)

    def list_tasks(self):
        return [FakeTask(1, "Ship task board")]

    def list_skills(self):
        return [FakeSkill("demo-skill")]


def test_cli_tasks_create_command(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeService())

    exit_code = cli_main.main(["tasks", "create", "--subject", "Build", "--description", "Desc"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "#1 Build" in captured.out


def test_cli_skills_list_command(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "create_agent_service", lambda env=None: FakeService())

    exit_code = cli_main.main(["skills", "list"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "demo-skill" in captured.out
