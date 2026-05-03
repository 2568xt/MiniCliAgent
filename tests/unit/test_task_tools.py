from pathlib import Path

from minicliagent.core.tasks.board import TaskBoard
from minicliagent.core.tools.builtins.tasks import task_create_tool, task_list_tool, task_update_tool


def test_task_create_and_list_tools(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path)

    created = task_create_tool(board, subject="Build runtime", description="Add task tool")
    listed = task_list_tool(board)

    assert created.is_error is False
    assert "Build runtime" in created.content
    assert "Build runtime" in listed.content


def test_task_update_tool_changes_status(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path)
    board.create(subject="Build runtime", description="Add task tool")

    updated = task_update_tool(board, task_id=1, status="in_progress", owner="lead")

    assert updated.is_error is False
    assert "in_progress" in updated.content
    assert "lead" in updated.content
