from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SettingsPaths:
    workspace_root: Path
    state_root: Path
    sessions_dir: Path
    tasks_dir: Path
    team_dir: Path
    worktrees_dir: Path
    logs_dir: Path
