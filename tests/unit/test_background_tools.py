from pathlib import Path

from minicliagent.core.runtime.background_manager import BackgroundManager
from minicliagent.core.tools.builtins.background import background_check_tool, background_run_tool


def test_background_run_tool_returns_task_id(tmp_path: Path) -> None:
    manager = BackgroundManager(workspace_root=tmp_path)

    result = background_run_tool(manager, "python -c \"print('hi')\"")

    assert result.is_error is False
    assert "started" in result.content


def test_background_check_tool_lists_tasks(tmp_path: Path) -> None:
    manager = BackgroundManager(workspace_root=tmp_path)
    manager.start("python -c \"print('hi')\"")

    result = background_check_tool(manager)

    assert result.is_error is False
    assert "running" in result.content or "completed" in result.content
