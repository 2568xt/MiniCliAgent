"""Lightweight OS-level sandbox for shell command execution."""

from minicliagent.infra.sandbox.backend import (
    SandboxBackend,
    detect_backend,
    get_backend,
    register_backend,
)
from minicliagent.infra.sandbox.config import DEFAULT_DENIED_PATHS, SandboxConfig

# Trigger backend self-registration.
from minicliagent.infra.sandbox import bubblewrap_backend  # noqa: F401
from minicliagent.infra.sandbox import sandbox_exec_backend  # noqa: F401

__all__ = [
    "SandboxBackend",
    "SandboxConfig",
    "DEFAULT_DENIED_PATHS",
    "get_backend",
    "register_backend",
    "detect_backend",
]
