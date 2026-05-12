"""macOS sandbox-exec backend using Seatbelt profiles."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from textwrap import dedent

from minicliagent.infra.sandbox.backend import SandboxBackend, register_backend
from minicliagent.infra.sandbox.config import DEFAULT_DENIED_PATHS, SandboxConfig

logger = logging.getLogger(__name__)

READONLY_SYSTEM_DIRS: tuple[str, ...] = (
    "/usr",
    "/bin",
    "/sbin",
    "/System/Library",
    "/Library",
)


class SandboxExecBackend(SandboxBackend):
    """macOS sandbox using sandbox-exec with Seatbelt profile."""

    name = "sandbox_exec"

    def __init__(self) -> None:
        super().__init__()
        self._profile_path: Path | None = None

    def _build_profile(self, config: SandboxConfig) -> str:
        # Filter out home directory paths to prevent access to ~/.ssh/id_rsa and similar
        home = os.path.expanduser("~")
        allowed = [str(d) for d in config.allowed_dirs if not str(d).startswith(home)]
        denied = list(DEFAULT_DENIED_PATHS)
        denied.extend(str(p) for p in config.denied_paths)

        deny_rules = ""
        for d in denied:
            deny_rules += f'(deny file-write* (subpath "{d}"))\n'
            deny_rules += f'(deny file-read* (subpath "{d}"))\n'

        allow_rules = ""
        for d in allowed:
            allow_rules += f'(allow file-write* (subpath "{d}"))\n'
            allow_rules += f'(allow file-read* (subpath "{d}"))\n'

        for sys_dir in READONLY_SYSTEM_DIRS:
            allow_rules += f'(allow file-read* (subpath "{sys_dir}"))\n'

        profile = dedent(f"""\
        (version 1)
        (deny default)
        (allow process-fork)
        (allow process-exec)
        (allow sysctl-read)
        (allow signal)
        {deny_rules}
        {allow_rules}
        (allow file-write* (subpath "/tmp"))
        (allow file-read* (subpath "/tmp"))
        (allow file-write* (subpath "/private/tmp"))
        (allow file-read* (subpath "/private/tmp"))
        (allow file-read* (subpath "/dev/null"))
        (allow file-read* (subpath "/dev/zero"))
        (allow file-read* (subpath "/dev/random"))
        (allow file-read* (subpath "/dev/urandom"))
        (allow file-read* (subpath "/dev/dtracehelper"))
        (allow network*)
        (allow file-read*)
        """)
        return profile

    def wrap(self, command: str, config: SandboxConfig) -> list[str]:
        profile = self._build_profile(config)
        fd, path = tempfile.mkstemp(suffix=".sb", prefix="sandbox_")
        with os.fdopen(fd, "w") as f:
            f.write(profile)
        self._profile_path = Path(path)
        return ["sandbox-exec", "-f", str(self._profile_path), "/bin/sh", "-c", command]

    def cleanup(self) -> None:
        if self._profile_path is not None:
            try:
                self._profile_path.unlink(missing_ok=True)
            except OSError:
                logger.debug("Failed to remove sandbox profile: %s", self._profile_path)
            self._profile_path = None


register_backend(SandboxExecBackend())
