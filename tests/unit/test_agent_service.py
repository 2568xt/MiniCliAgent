import subprocess
from pathlib import Path

from minicliagent.app.agent_service import AgentService, create_agent_service
from minicliagent.core.config.settings import Settings


class FakeRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, object]] = []

    def run_turn(self, session_id: str, user_input: str | None = None, on_text_delta=None):
        self.calls.append((session_id, user_input or "", on_text_delta))
        return type("Result", (), {"output_text": "done"})()


def test_agent_service_run_prompt_passes_stream_callback() -> None:
    runtime = FakeRuntime()
    service = AgentService(
        settings=Settings.from_env({"MINICLIAGENT_WORKSPACE": ".", "MINICLIAGENT_MODEL": "claude-test"}),
        runtime=runtime,
        task_service=None,
        skill_service=None,
        team_bus=None,
        team_service=None,
        worktree_service=None,
    )
    fragments: list[str] = []

    output = service.run_prompt("hello", session_id="s1", on_text_delta=fragments.append)

    assert output == "done"
    assert runtime.calls == [("s1", "hello", fragments.append)]


def test_create_agent_service_wires_file_message_store(tmp_path: Path) -> None:
    service = create_agent_service(
        env={
            "MINICLIAGENT_WORKSPACE": str(tmp_path),
            "MINICLIAGENT_MODEL": "claude-test",
        }
    )

    assert service.settings.workspace_root == tmp_path
    assert service.runtime.message_store.sessions_dir == tmp_path / ".minicliagent" / "sessions"
    assert service.settings.worktrees_dir == tmp_path / ".minicliagent" / "worktrees"
    assert service.settings.logs_dir == tmp_path / ".minicliagent" / "logs"
    tool_names = [tool.name for tool in service.runtime.tool_registry.list_specs()]
    assert "bash" in tool_names
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "edit_file" in tool_names
    assert "list_skills" in tool_names
    assert "load_skill" in tool_names
    assert "task_create" in tool_names
    assert "task_list" in tool_names
    assert "task_update" in tool_names
    assert "background_run" in tool_names
    assert "background_check" in tool_names
    assert "team_send" in tool_names
    assert "team_inbox" in tool_names
    assert "worktree_create" not in tool_names
    assert "worktree_list" not in tool_names
    assert service.task_service.board.tasks_dir == tmp_path / ".minicliagent" / "tasks"
    assert service.skill_service.list_skills() == []
    assert service.team_bus.inbox_dir == tmp_path / ".minicliagent" / "team" / "inbox"


def test_create_agent_service_registers_worktree_tools_inside_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hello")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)

    service = create_agent_service(
        env={
            "MINICLIAGENT_WORKSPACE": str(tmp_path),
            "MINICLIAGENT_MODEL": "claude-test",
        }
    )

    tool_names = [tool.name for tool in service.runtime.tool_registry.list_specs()]
    assert "worktree_create" in tool_names
    assert "worktree_list" in tool_names
