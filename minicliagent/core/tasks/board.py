from __future__ import annotations

import json
from pathlib import Path

from minicliagent.core.tasks.models import TaskRecord


class TaskBoard:
    def __init__(self, tasks_dir: Path) -> None:
        self.tasks_dir = tasks_dir
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: int) -> Path:
        return self.tasks_dir / f"task_{task_id}.json"

    def _next_id(self) -> int:
        ids = []
        for path in self.tasks_dir.glob("task_*.json"):
            try:
                ids.append(int(path.stem.split("_")[1]))
            except Exception:
                continue
        return max(ids, default=0) + 1

    def _load(self, task_id: int) -> TaskRecord:
        payload = json.loads(self._path(task_id).read_text())
        return TaskRecord(**payload)

    def _save(self, task: TaskRecord) -> TaskRecord:
        self._path(task.id).write_text(json.dumps(task.to_dict(), indent=2))
        return task

    def create(self, subject: str, description: str) -> TaskRecord:
        return self._save(TaskRecord(id=self._next_id(), subject=subject, description=description))

    def update(
        self,
        task_id: int,
        status: str | None = None,
        owner: str | None = None,
        priority: str | None = None,
        labels: list[str] | None = None,
        add_blocked_by: list[int] | None = None,
        worktree: str | None = None,
    ) -> TaskRecord:
        task = self._load(task_id)
        if status is not None:
            task.status = status
        if owner is not None:
            task.owner = owner
        if priority is not None:
            task.priority = priority
        if labels is not None:
            task.labels = labels
        if add_blocked_by is not None:
            task.blocked_by = add_blocked_by
        if worktree is not None:
            task.worktree = worktree
        return self._save(task)

    def list_all(self) -> list[TaskRecord]:
        tasks: list[TaskRecord] = []
        for path in sorted(self.tasks_dir.glob("task_*.json")):
            payload = json.loads(path.read_text())
            tasks.append(TaskRecord(**payload))
        return tasks
