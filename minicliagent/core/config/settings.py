from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    model: str
    workspace_root: Path
    state_root: Path
    sessions_dir: Path
    tasks_dir: Path
    team_dir: Path
    worktrees_dir: Path
    logs_dir: Path

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "Settings":
        workspace_root = Path(env.get("MINICLIAGENT_WORKSPACE", ".")).resolve()
        state_root = workspace_root / ".minicliagent"
        return cls(
            model=env.get("MINICLIAGENT_MODEL", "claude-3-7-sonnet-latest"),
            workspace_root=workspace_root,
            state_root=state_root,
            sessions_dir=state_root / "sessions",
            tasks_dir=state_root / "tasks",
            team_dir=state_root / "team",
            worktrees_dir=state_root / "worktrees",
            logs_dir=state_root / "logs",
        )
