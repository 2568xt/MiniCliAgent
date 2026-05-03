from pathlib import Path

from minicliagent.core.tasks.board import TaskBoard


def test_task_board_create_and_update_task(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path)

    created = board.create(subject="Add skill loading", description="Implement local skill scanning")
    updated = board.update(created.id, status="in_progress", owner="lead")

    assert created.id == 1
    assert updated.status == "in_progress"
    assert updated.owner == "lead"
    listed = board.list_all()
    assert listed[0].subject == "Add skill loading"
    assert (tmp_path / "task_1.json").exists()
