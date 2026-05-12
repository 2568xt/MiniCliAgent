"""Linux bubblewrap sandbox backend."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from minicliagent.infra.sandbox.backend import SandboxBackend, register_backend
from minicliagent.infra.sandbox.config import DEFAULT_DENIED_PATHS, SandboxConfig

logger = logging.getLogger(__name__)

READONLY_SYSTEM_DIRS: tuple[str, ...] = (
    "/usr",
    "/lib",
    "/lib64",
    "/bin",
    "/sbin",
    "/etc/alternatives",
    "/etc/ssl",
    "/etc/ca-certificates",
    "/var/empty",
)


class BubblewrapBackend(SandboxBackend):
    """Linux sandbox using bubblewrap with user namespace isolation."""

    name = "bubblewrap"

    def wrap(self, command: str, config: SandboxConfig) -> list[str]:
        args: list[str] = [
            "bwrap",
            "--unshare-user",
            "--unshare-net",
            "--unshare-ipc",
            "--unshare-pid",
            "--die-with-parent",
            "--new-session",
        ]

        for d in config.allowed_dirs:
            args.extend(["--bind", str(d), str(d)])

        for d in READONLY_SYSTEM_DIRS:
            if os.path.exists(d):
                args.extend(["--ro-bind", d, d])

        args.extend(["--tmpfs", "/tmp"])
        args.extend(["--proc", "/proc"])

        home = Path.home()
        args.extend(["--bind", str(home), str(home)])

        for denied_rel in DEFAULT_DENIED_PATHS:
            denied_abs = home / denied_rel if not denied_rel.startswith("/") else Path(denied_rel)
            if denied_abs.exists():
                args.extend(["--bind", "/dev/null", str(denied_abs)])

        for extra_denied in config.denied_paths:
            if extra_denied.exists():
                args.extend(["--bind", "/dev/null", str(extra_denied)])

        args.extend(["--", "/bin/sh", "-c", command])
        return args


register_backend(BubblewrapBackend())
