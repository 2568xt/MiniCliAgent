from __future__ import annotations

from minicliagent.app.worktree_service import WorktreeService
from minicliagent.core.tools.models import ToolResult


def worktree_create_tool(service: WorktreeService, name: str, branch: str, task_id: int | None = None) -> ToolResult:
    record = service.create(name=name, branch=branch, task_id=task_id)
    return ToolResult(content=f"{record.name} {record.status}")


def worktree_list_tool(service: WorktreeService) -> ToolResult:
    records = service.list_all()
    if not records:
        return ToolResult(content="")
    return ToolResult(content="\n".join(f"{record.name} {record.status}" for record in records))
