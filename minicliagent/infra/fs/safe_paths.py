from __future__ import annotations

from pathlib import Path


def safe_workspace_path(workspace_root: Path, relative_path: str) -> Path:
    candidate = (workspace_root / relative_path).resolve()
    if not candidate.is_relative_to(workspace_root.resolve()):
        raise ValueError(f"Path escapes workspace: {relative_path}")
    return candidate
