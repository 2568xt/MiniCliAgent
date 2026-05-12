from __future__ import annotations

from pathlib import Path

from minicliagent.core.tools.models import ToolResult
from minicliagent.infra.fs.safe_paths import (
    PathNotFoundError,
    PathSecurityError,
    safe_workspace_path,
)


def read_text_file(workspace_root: Path, path: str) -> ToolResult:
    try:
        file_path = safe_workspace_path(workspace_root, path, must_exist=True)
        return ToolResult(content=file_path.read_text())
    except PathNotFoundError as exc:
        return ToolResult(content=str(exc), is_error=True)
    except PathSecurityError as exc:
        return ToolResult(content=str(exc), is_error=True)
    except Exception as exc:
        return ToolResult(content=f"Error reading file: {exc}", is_error=True)


def write_text_file(workspace_root: Path, path: str, content: str) -> ToolResult:
    try:
        file_path = safe_workspace_path(workspace_root, path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return ToolResult(content=f"Wrote {len(content)} bytes to {path}")
    except PathSecurityError as exc:
        return ToolResult(content=str(exc), is_error=True)
    except Exception as exc:
        return ToolResult(content=f"Error writing file: {exc}", is_error=True)


def edit_text_file(
    workspace_root: Path,
    path: str,
    old_text: str,
    new_text: str,
    replace_all: bool = False,
) -> ToolResult:
    try:
        file_path = safe_workspace_path(workspace_root, path, must_exist=True)
    except PathNotFoundError:
        return ToolResult(
            content=(
                f"File not found: '{path}'. "
                f"Use write_file to create the file first, or check if the path is correct."
            ),
            is_error=True,
        )
    except PathSecurityError as exc:
        return ToolResult(content=str(exc), is_error=True)

    try:
        source = file_path.read_text()
    except FileNotFoundError:
        # Race condition: deleted between must_exist check and read
        return ToolResult(
            content=f"File not found: '{path}'. The file was deleted or moved.",
            is_error=True,
        )
    except PermissionError:
        return ToolResult(
            content=f"Permission denied reading: '{path}'. Check file permissions.",
            is_error=True,
        )
    except Exception as exc:
        return ToolResult(content=f"Error reading file: {exc}", is_error=True)

    if old_text not in source:
        # Provide context to help the agent find the right string
        lines = source.splitlines()
        suggestions = []
        for i, line in enumerate(lines, 1):
            if old_text[:40] in line or line[:40] == old_text[:40]:
                suggestions.append(f"  Line {i}: {line[:80]}")
        hint = ""
        if suggestions:
            hint = f"\n\nSimilar lines found:\n" + "\n".join(suggestions[:3])
        return ToolResult(
            content=(
                f"Text not found in '{path}'. The old_text was not found in the file.{hint}\n"
                f"IMPORTANT: Re-read the file with read_file to get the exact content, "
                f"then copy the exact text including whitespace and punctuation."
            ),
            is_error=True,
        )

    # Apply the edit
    if replace_all:
        new_content = source.replace(old_text, new_text)
    else:
        new_content = source.replace(old_text, new_text, 1)

    try:
        file_path.write_text(new_content)
    except PermissionError:
        return ToolResult(
            content=f"Permission denied writing: '{path}'. Cannot modify this file.",
            is_error=True,
        )
    except Exception as exc:
        return ToolResult(content=f"Error writing file: {exc}", is_error=True)

    # VERIFICATION: read back and confirm the change was applied
    # This is the critical anti-hallucination guard
    try:
        verify = file_path.read_text()
        if replace_all:
            expected_count = source.count(old_text)
            actual_count = verify.count(new_text)
            if actual_count != expected_count:
                return ToolResult(
                    content=(
                        f"Edit may not have applied correctly: expected {expected_count} "
                        f"occurrence(s) of new text, found {actual_count}. "
                        f"File may have been modified concurrently. Re-read and retry."
                    ),
                    is_error=True,
                )
        else:
            # Single edit: new_text must be present
            if new_text not in verify:
                return ToolResult(
                    content=(
                        f"Verification failed: new_text was not found in file after edit. "
                        f"Re-read the file and retry the edit."
                    ),
                    is_error=True,
                )
            # old_text count should be exactly one less (only first occurrence replaced)
            if old_text in verify:
                expected_remaining = source.count(old_text) - 1
                actual_remaining = verify.count(old_text)
                if actual_remaining != expected_remaining:
                    return ToolResult(
                        content=(
                            f"Verification failed: edit replaced wrong occurrence(s). "
                            f"Expected {expected_remaining} remaining 'old_text', found {actual_remaining}. "
                            f"Re-read the file and retry."
                        ),
                        is_error=True,
                    )
    except Exception:
        # Verification failed but write succeeded — warn only, don't error
        pass

    # Success: include what changed for transparency
    change_desc = f"Replaced {old_text[:40]!r} -> {new_text[:40]!r}"
    if replace_all:
        count = source.count(old_text)
        change_desc = f"Replaced all {count} occurrence(s) of {old_text[:40]!r} -> {new_text[:40]!r}"
    return ToolResult(content=f"Edited {path}: {change_desc}")
