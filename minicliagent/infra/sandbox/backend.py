"""Sandbox backend ABC, registry, and auto-detection."""

from __future__ import annotations

import logging
import shutil
from abc import ABC, abstractmethod

from minicliagent.infra.sandbox.config import SandboxConfig

logger = logging.getLogger(__name__)

_backends: dict[str, SandboxBackend] = {}


class SandboxBackend(ABC):
    """Abstract base for sandbox backends (bubblewrap, sandbox-exec, disabled)."""

    name: str = ""

    @abstractmethod
    def wrap(self, command: str, config: SandboxConfig) -> list[str]:
        """Wrap a shell command into sandbox invocation args for subprocess."""
        ...

    def cleanup(self) -> None:
        """Clean up sandbox artifacts after command execution."""


class DisabledBackend(SandboxBackend):
    """No-op fallback backend. Passes commands through unchanged (regex-only mode)."""

    name = "disabled"

    def wrap(self, command: str, config: SandboxConfig) -> list[str]:
        return [command]


def register_backend(backend: SandboxBackend) -> None:
    """Register a sandbox backend implementation."""
    _backends[backend.name] = backend


def get_backend(name: str) -> SandboxBackend:
    """Get a registered sandbox backend by name."""
    backend = _backends.get(name)
    if backend is None:
        raise KeyError(
            f"Sandbox backend '{name}' not registered. "
            f"Available: {sorted(_backends.keys())}"
        )
    return backend


def detect_backend() -> str:
    """Auto-detect the best available sandbox backend for the current platform.

    Returns the backend name string: 'bubblewrap', 'sandbox_exec', or 'disabled'.
    """
    import platform

    system = platform.system()

    if system == "Linux":
        if shutil.which("bwrap"):
            return "bubblewrap"
        logger.warning(
            "bwrap not found in PATH. Sandbox backend 'bubblewrap' not available."
        )

    elif system == "Darwin":
        if shutil.which("sandbox-exec"):
            return "sandbox_exec"
        logger.warning(
            "sandbox-exec not found. "
            "Sandbox backend 'sandbox_exec' not available."
        )

    else:
        logger.warning(
            "Platform '%s' has no native sandbox backend. Falling back to regex-only mode.",
            system,
        )

    return "disabled"


# Register the fallback backend at import time.
register_backend(DisabledBackend())
