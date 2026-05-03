from __future__ import annotations

from dataclasses import dataclass

from minicliagent.core.tasks.board import TaskBoard
from minicliagent.core.tasks.models import TaskRecord


@dataclass
class TaskService:
    board: TaskBoard

    def create_task(self, subject: str, description: str) -> TaskRecord:
        return self.board.create(subject=subject, description=description)

    def update_task(
        self,
        task_id: int,
        status: str | None = None,
        owner: str | None = None,
        priority: str | None = None,
        labels: list[str] | None = None,
        add_blocked_by: list[int] | None = None,
        worktree: str | None = None,
    ) -> TaskRecord:
        return self.board.update(
            task_id=task_id,
            status=status,
            owner=owner,
            priority=priority,
            labels=labels,
            add_blocked_by=add_blocked_by,
            worktree=worktree,
        )

    def list_tasks(self) -> list[TaskRecord]:
        return self.board.list_all()
