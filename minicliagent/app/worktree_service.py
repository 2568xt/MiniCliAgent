from __future__ import annotations

from dataclasses import dataclass

from minicliagent.core.tasks.board import TaskBoard
from minicliagent.core.worktree.manager import WorktreeManager
from minicliagent.core.worktree.models import WorktreeRecord


@dataclass
class WorktreeService:
    manager: WorktreeManager | None
    task_board: TaskBoard | None = None

    def create(self, name: str, branch: str, task_id: int | None = None) -> WorktreeRecord:
        if self.manager is None:
            raise RuntimeError("Worktree manager unavailable")
        record = self.manager.create(name=name, branch=branch, task_id=task_id)
        if task_id is not None and self.task_board is not None:
            self.task_board.update(task_id, worktree=name)
        return record

    def list_all(self) -> list[WorktreeRecord]:
        if self.manager is None:
            return []
        return self.manager.list_all()

    def run_command(self, name: str, command: str) -> str:
        if self.manager is None:
            raise RuntimeError("Worktree manager unavailable")
        return self.manager.run_command(name, command)
