from __future__ import annotations

from minicliagent.core.tasks.board import TaskBoard
from minicliagent.core.tools.models import ToolResult


def task_create_tool(board: TaskBoard, subject: str, description: str) -> ToolResult:
    task = board.create(subject=subject, description=description)
    return ToolResult(content=f"#{task.id} {task.subject} [{task.status}]")


def task_list_tool(board: TaskBoard) -> ToolResult:
    tasks = board.list_all()
    if not tasks:
        return ToolResult(content="")
    return ToolResult(content="\n".join(f"#{task.id} {task.subject} [{task.status}]" for task in tasks))


def task_update_tool(
    board: TaskBoard,
    task_id: int,
    status: str | None = None,
    owner: str | None = None,
) -> ToolResult:
    task = board.update(task_id=task_id, status=status, owner=owner)
    return ToolResult(content=f"#{task.id} {task.subject} [{task.status}] owner={task.owner}")
