from __future__ import annotations

import json
import subprocess
from pathlib import Path

from minicliagent.core.worktree.models import WorktreeRecord


def detect_repo_root(cwd: Path) -> Path | None:
    git_dir = cwd / ".git"
    if git_dir.exists():
        return cwd
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


class WorktreeManager:
    def __init__(self, repo_root: Path, state_dir: Path, event_bus=None) -> None:
        self.repo_root = repo_root
        self.state_dir = state_dir
        self.event_bus = event_bus
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.state_dir / "index.json"
        if not self.index_path.exists():
            self.index_path.write_text("[]")

    def _load_index(self) -> list[WorktreeRecord]:
        payload = json.loads(self.index_path.read_text())
        return [
            WorktreeRecord(
                name=item["name"],
                path=Path(item["path"]),
                branch=item["branch"],
                task_id=item.get("task_id"),
                status=item["status"],
            )
            for item in payload
        ]

    def _save_index(self, records: list[WorktreeRecord]) -> None:
        self.index_path.write_text(json.dumps([record.to_dict() for record in records], indent=2))

    def create(self, name: str, branch: str, task_id: int | None = None) -> WorktreeRecord:
        path = self.state_dir / name
        subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(path)],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        record = WorktreeRecord(name=name, path=path, branch=branch, task_id=task_id)
        records = self._load_index()
        records.append(record)
        self._save_index(records)
        if self.event_bus is not None:
            self.event_bus.emit("worktree_created", {"name": name, "branch": branch, "task_id": task_id})
        return record

    def list_all(self) -> list[WorktreeRecord]:
        return self._load_index()

    def close(self, name: str, keep_branch: bool = True) -> None:
        records = self._load_index()
        for record in records:
            if record.name == name:
                subprocess.run(
                    ["git", "worktree", "remove", str(record.path), "--force"],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                record.status = "closed"
                if self.event_bus is not None:
                    self.event_bus.emit("worktree_closed", {"name": name, "keep_branch": keep_branch})
                break
        self._save_index(records)

    def run_command(self, name: str, command: str) -> str:
        records = self._load_index()
        target = next(record for record in records if record.name == name)
        result = subprocess.run(command, shell=True, cwd=target.path, capture_output=True, text=True, check=True)
        return (result.stdout + result.stderr).strip()
