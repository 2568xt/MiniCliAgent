import time
from pathlib import Path

from minicliagent.core.runtime.event_bus import EventBus
from minicliagent.core.runtime.background_manager import BackgroundManager


def test_background_manager_runs_command_and_drains_notification(tmp_path: Path) -> None:
    manager = BackgroundManager(workspace_root=tmp_path)

    task_id = manager.start("python -c \"print('hi')\"")

    deadline = time.time() + 5
    while time.time() < deadline:
        task = manager.get(task_id)
        if task.status != "running":
            break
        time.sleep(0.05)

    task = manager.get(task_id)
    assert task.status == "completed"
    assert "hi" in task.result

    notifications = manager.drain_notifications()
    assert len(notifications) == 1
    assert notifications[0]["task_id"] == task_id


def test_background_manager_lists_tasks(tmp_path: Path) -> None:
    manager = BackgroundManager(workspace_root=tmp_path)
    task_id = manager.start("python -c \"print('hi')\"")

    listing = manager.list_tasks()

    assert len(listing) == 1
    assert listing[0].task_id == task_id


def test_background_manager_can_cancel_pending_task_record(tmp_path: Path) -> None:
    manager = BackgroundManager(workspace_root=tmp_path)
    task_id = manager.start("python -c \"import time; time.sleep(1)\"")

    cancelled = manager.cancel(task_id)

    assert cancelled.status == "cancelled"


def test_background_manager_emits_events(tmp_path: Path) -> None:
    event_bus = EventBus(tmp_path / "events.jsonl")
    manager = BackgroundManager(workspace_root=tmp_path, event_bus=event_bus)
    task_id = manager.start("python -c \"print('hi')\"")

    deadline = time.time() + 5
    while time.time() < deadline:
        if manager.get(task_id).status != "running":
            break
        time.sleep(0.05)

    assert "background_started" in (tmp_path / "events.jsonl").read_text()
