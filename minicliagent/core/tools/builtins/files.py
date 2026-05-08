from __future__ import annotations

from pathlib import Path

from minicliagent.core.tools.models import ToolResult
from minicliagent.infra.fs.safe_paths import safe_workspace_path


def read_text_file(workspace_root: Path, path: str) -> ToolResult:
    try:
        file_path = safe_workspace_path(workspace_root, path)
        return ToolResult(content=file_path.read_text())
    except Exception as exc:
        return ToolResult(content=str(exc), is_error=True)


def write_text_file(workspace_root: Path, path: str, content: str) -> ToolResult:
    try:
        file_path = safe_workspace_path(workspace_root, path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return ToolResult(content=f"Wrote {len(content)} bytes to {path}")
    except Exception as exc:
        return ToolResult(content=str(exc), is_error=True)


def edit_text_file(workspace_root: Path, path: str, old_text: str, new_text: str, replace_all: bool = False) -> ToolResult:
    try:
        file_path = safe_workspace_path(workspace_root, path)
        source = file_path.read_text()
        if old_text not in source:
            return ToolResult(content=f"Text not found in {path}", is_error=True)
        file_path.write_text(source.replace(old_text, new_text) if replace_all else source.replace(old_text, new_text, 1))
        return ToolResult(content=f"Edited {path}")
    except Exception as exc:
        return ToolResult(content=str(exc), is_error=True)
