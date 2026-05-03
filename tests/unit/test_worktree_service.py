import subprocess
from pathlib import Path

from minicliagent.app.worktree_service import WorktreeService
from minicliagent.core.tasks.board import TaskBoard
from minicliagent.core.worktree.manager import WorktreeManager


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("hello")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


def test_worktree_service_binds_task_and_runs_command(tmp_path: Path) -> None:
    init_git_repo(tmp_path)
    board = TaskBoard(tmp_path / ".minicliagent" / "tasks")
    task = board.create("feature", "desc")
    manager = WorktreeManager(tmp_path, tmp_path / ".minicliagent" / "worktrees")
    service = WorktreeService(manager=manager, task_board=board)

    record = service.create("feature-one", "wt/feature-one", task_id=task.id)
    output = service.run_command("feature-one", "pwd")

    updated = board.list_all()[0]
    assert updated.worktree == "feature-one"
    assert record.name == "feature-one"
    assert "feature-one" in output
