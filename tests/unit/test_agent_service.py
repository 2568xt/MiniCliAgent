from pathlib import Path

from minicliagent.app.agent_service import create_agent_service
from minicliagent.core.runtime.message_store import FileMessageStore


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
    assert "memory_search" in tool_names
    assert isinstance(service.runtime.message_store, FileMessageStore)
    assert service.memory_service is not None


def test_create_agent_service_can_disable_memory(tmp_path: Path) -> None:
    service = create_agent_service(
        env={
            "MINICLIAGENT_WORKSPACE": str(tmp_path),
            "MINICLIAGENT_MODEL": "claude-test",
            "MINICLIAGENT_MEMORY_ENABLED": "0",
        }
    )

    tool_names = [tool.name for tool in service.runtime.tool_registry.list_specs()]
    assert "memory_search" not in tool_names
    assert service.memory_service is None


def test_create_agent_service_registers_worktree_tools_inside_git_repo(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    service = create_agent_service(
        env={
            "MINICLIAGENT_WORKSPACE": str(tmp_path),
            "MINICLIAGENT_MODEL": "claude-test",
        }
    )

    tool_names = [tool.name for tool in service.runtime.tool_registry.list_specs()]
    assert "worktree_create" in tool_names
    assert "worktree_list" in tool_names
