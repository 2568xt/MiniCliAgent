from pathlib import Path

from minicliagent.app.task_service import TaskService
from minicliagent.core.tasks.board import TaskBoard


def test_task_service_creates_and_lists_tasks(tmp_path: Path) -> None:
    service = TaskService(board=TaskBoard(tmp_path))

    task = service.create_task("Ship task board", "Persist JSON tasks")

    assert task.id == 1
    assert service.list_tasks()[0].subject == "Ship task board"
