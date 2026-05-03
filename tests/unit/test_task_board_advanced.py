from pathlib import Path

from minicliagent.core.tasks.board import TaskBoard


def test_task_board_supports_priority_labels_and_dependencies(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path)
    first = board.create(subject="Base", description="d")
    second = board.create(subject="Dependent", description="d")

    updated = board.update(
        second.id,
        status="pending",
        owner="lead",
        priority="high",
        labels=["runtime"],
        add_blocked_by=[first.id],
    )

    assert updated.priority == "high"
    assert updated.labels == ["runtime"]
    assert updated.blocked_by == [first.id]
