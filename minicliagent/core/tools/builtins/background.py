from __future__ import annotations

from minicliagent.core.runtime.background_manager import BackgroundManager
from minicliagent.core.tools.models import ToolResult


def background_run_tool(manager: BackgroundManager, command: str) -> ToolResult:
    task_id = manager.start(command)
    return ToolResult(content=f"Background task {task_id} started")


def background_check_tool(manager: BackgroundManager, task_id: str | None = None) -> ToolResult:
    if task_id:
        task = manager.get(task_id)
        return ToolResult(content=f"{task.task_id} {task.status} {task.command}")

    tasks = manager.list_tasks()
    if not tasks:
        return ToolResult(content="")
    return ToolResult(content="\n".join(f"{task.task_id} {task.status} {task.command}" for task in tasks))
