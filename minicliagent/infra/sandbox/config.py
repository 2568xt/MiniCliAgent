from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DENIED_PATHS: tuple[str, ...] = (
    "/etc",
    "/boot",
    "/root",
    "/proc",
    "/sys",
    "/dev",
    "settings.json",
    ".claude/skills",
    ".git/objects",
    ".git/refs",
)


@dataclass(frozen=True)
class SandboxConfig:
    enabled: bool = True
    backend: str = ""
    allowed_dirs: tuple[Path, ...] = ()
    denied_paths: tuple[Path, ...] = ()
    allowed_domains: tuple[str, ...] = ()
    auto_allow_sandboxed: bool = True

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "SandboxConfig":
        if env is None:
            env = dict(os.environ)

        return cls(
            enabled=_env_bool(env.get("MINICLIAGENT_SANDBOX_ENABLED", "1")),
            backend=env.get("MINICLIAGENT_SANDBOX_BACKEND", "").strip(),
            allowed_dirs=tuple(
                Path(p) for p in env.get("MINICLIAGENT_SANDBOX_ALLOWED_DIRS", "").split(":")
                if p.strip()
            ),
            denied_paths=tuple(
                Path(p) for p in env.get("MINICLIAGENT_SANDBOX_DENIED_PATHS", "").split(":")
                if p.strip()
            ),
            allowed_domains=tuple(
                d.strip() for d in env.get("MINICLIAGENT_SANDBOX_ALLOWED_DOMAINS", "").split(",")
                if d.strip()
            ),
            auto_allow_sandboxed=_env_bool(
                env.get("MINICLIAGENT_SANDBOX_AUTO_ALLOW", "1")
            ),
        )


def _env_bool(value: str) -> bool:
    return value.strip().lower() not in {"0", "false", "no", "off"}
