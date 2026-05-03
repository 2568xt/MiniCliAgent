import subprocess
from pathlib import Path

import pytest

from minicliagent.core.worktree.manager import WorktreeManager, detect_repo_root


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("hello")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


def test_detect_repo_root_returns_git_root(tmp_path: Path) -> None:
    init_git_repo(tmp_path)
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)

    assert detect_repo_root(nested) == tmp_path


def test_worktree_manager_create_and_close(tmp_path: Path) -> None:
    init_git_repo(tmp_path)
    manager = WorktreeManager(repo_root=tmp_path, state_dir=tmp_path / ".minicliagent" / "worktrees")

    record = manager.create("feature-one", branch="wt/feature-one", task_id=1)
    assert record.name == "feature-one"
    assert record.task_id == 1
    assert record.path.exists()

    manager.close("feature-one", keep_branch=True)
    records = manager.list_all()
    assert records[0].status == "closed"


def test_worktree_manager_captures_git_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict] = []
    manager = WorktreeManager(repo_root=tmp_path, state_dir=tmp_path / ".minicliagent" / "worktrees")

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})

        class Result:
            returncode = 0
            stdout = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    manager.create("feature-one", branch="wt/feature-one", task_id=1)

    assert calls
    assert calls[0]["capture_output"] is True
    assert calls[0]["text"] is True
