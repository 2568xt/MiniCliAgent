from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

from minicliagent.infra.sandbox.backend import get_backend
from minicliagent.infra.sandbox.bubblewrap_backend import READONLY_SYSTEM_DIRS, BubblewrapBackend
from minicliagent.infra.sandbox.config import SandboxConfig


def make_config(**kwargs: object) -> SandboxConfig:
    defaults = {
        "enabled": True,
        "backend": "bubblewrap",
        "allowed_dirs": (),
        "denied_paths": (),
    }
    defaults.update(kwargs)
    return SandboxConfig(**defaults)  # type: ignore[arg-type]


def test_backend_is_registered() -> None:
    backend = get_backend("bubblewrap")
    assert isinstance(backend, BubblewrapBackend)


def test_wrap_basic() -> None:
    cfg = make_config()
    args = get_backend("bubblewrap").wrap("echo hello", cfg)
    assert args[0] == "bwrap"
    assert "--unshare-user" in args
    assert "--unshare-net" in args
    assert args[-3:] == ["/bin/sh", "-c", "echo hello"]


def test_wrap_includes_allowed_dirs() -> None:
    cfg = make_config(allowed_dirs=(Path("/my/project"),))
    args = get_backend("bubblewrap").wrap("ls", cfg)
    assert "--bind" in args
    idx = args.index("--bind")
    assert args[idx + 1] == "/my/project"


def test_wrap_binds_home() -> None:
    cfg = make_config()
    args = get_backend("bubblewrap").wrap("ls", cfg)
    home = str(Path.home())
    assert home in args


def test_wrap_binds_tmpfs() -> None:
    cfg = make_config()
    args = get_backend("bubblewrap").wrap("ls", cfg)
    assert "--tmpfs" in args
    idx = args.index("--tmpfs")
    assert args[idx + 1] == "/tmp"


def test_wrap_mounts_proc() -> None:
    cfg = make_config()
    args = get_backend("bubblewrap").wrap("ls", cfg)
    assert "--proc" in args


def test_wrap_denied_devnull_bind() -> None:
    denied_dir = Path("/tmp/test_denied_bwrap")
    denied_dir.mkdir(parents=True, exist_ok=True)
    cfg = make_config(denied_paths=(denied_dir,))
    try:
        args = get_backend("bubblewrap").wrap("ls", cfg)
        assert "/dev/null" in args
        assert str(denied_dir) in args
    finally:
        denied_dir.rmdir()


def test_cleanup_is_noop() -> None:
    cfg = make_config()
    backend = get_backend("bubblewrap")
    backend.cleanup()  # does not raise


def test_readonly_dirs_is_tuple() -> None:
    assert isinstance(READONLY_SYSTEM_DIRS, tuple)
