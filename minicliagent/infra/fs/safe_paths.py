from __future__ import annotations

import os
from pathlib import Path


class PathSecurityError(ValueError):
    """Raised when a path escapes the workspace boundary."""
    pass


class PathNotFoundError(LookupError):
    """Raised when a required file does not exist."""
    pass


def safe_workspace_path(
    workspace_root: Path,
    relative_path: str,
    must_exist: bool = False,
) -> Path:
    """Resolve *relative_path* against *workspace_root*, blocking path traversal.

    SECURITY: Resolves the path and verifies it stays within *workspace_root*.
    Follows symlinks, so a symlink pointing outside the workspace is blocked.

    Args:
        workspace_root: The root directory to resolve relative paths against.
        relative_path: A relative or absolute path (absolute paths are also checked).
        must_exist: If True, raise PathNotFoundError when the file does not exist.
                   If False (default), non-existent paths are returned normally
                   (needed for write_file / new-file creation).

    Returns:
        The resolved Path within the workspace.

    Raises:
        PathSecurityError: The resolved path is outside workspace_root.
        PathNotFoundError: must_exist=True and the file does not exist.
    """
    ws_resolved = workspace_root.resolve()

    # Normalize: expand ~ and resolve . / .. components
    # Use os.path.normpath + Path() to handle . and .. without requiring the path to exist
    normalized = Path(os.path.normpath(os.path.expanduser(relative_path)))

    if normalized.is_absolute():
        candidate = normalized.resolve()
    else:
        candidate = (ws_resolved / normalized).resolve()

    if not candidate.is_relative_to(ws_resolved):
        raise PathSecurityError(
            f"Path '{relative_path}' resolves to '{candidate}' which is outside "
            f"workspace '{ws_resolved}'. Use paths inside the workspace only."
        )

    if must_exist and not candidate.exists():
        raise PathNotFoundError(
            f"File not found: '{relative_path}'. Check the path, or use write_file "
            f"to create a new file at that location."
        )

    return candidate
