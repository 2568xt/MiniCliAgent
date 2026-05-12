from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

from minicliagent.infra.sandbox.backend import get_backend
from minicliagent.infra.sandbox.config import DEFAULT_DENIED_PATHS, SandboxConfig
from minicliagent.infra.sandbox.sandbox_exec_backend import (
    READONLY_SYSTEM_DIRS,
    SandboxExecBackend,
)


def make_config(**kwargs: object) -> SandboxConfig:
    defaults = {
        "enabled": True,
        "backend": "sandbox_exec",
        "allowed_dirs": (),
        "denied_paths": (),
    }
    defaults.update(kwargs)
    return SandboxConfig(**defaults)  # type: ignore[arg-type]


def test_backend_is_registered() -> None:
    backend = get_backend("sandbox_exec")
    assert isinstance(backend, SandboxExecBackend)


def test_wrap_basic() -> None:
    cfg = make_config()
    backend = get_backend("sandbox_exec")
    args = backend.wrap("echo hello", cfg)
    try:
        assert args[0] == "sandbox-exec"
        assert "-f" in args
        assert args[-3:] == ["/bin/sh", "-c", "echo hello"]
    finally:
        backend.cleanup()


def test_wrap_creates_temp_profile() -> None:
    cfg = make_config()
    backend = get_backend("sandbox_exec")
    args = backend.wrap("true", cfg)
    try:
        profile_path = args[2]
        assert os.path.isfile(profile_path)
        with open(profile_path) as f:
            content = f.read()
        assert "(version 1)" in content
        assert "(deny default)" in content
    finally:
        backend.cleanup()


def test_profile_contains_deny_rules() -> None:
    cfg = make_config(denied_paths=(Path("/secret"),))
    backend = get_backend("sandbox_exec")
    args = backend.wrap("true", cfg)
    try:
        with open(args[2]) as f:
            content = f.read()
        assert '(deny file* (subpath "/secret"))' in content
    finally:
        backend.cleanup()


def test_profile_contains_allow_rules() -> None:
    cfg = make_config(allowed_dirs=(Path("/my/project"),))
    backend = get_backend("sandbox_exec")
    args = backend.wrap("true", cfg)
    try:
        with open(args[2]) as f:
            content = f.read()
        assert '(allow file* (subpath "/my/project"))' in content
    finally:
        backend.cleanup()


def test_profile_contains_system_readonly() -> None:
    cfg = make_config()
    backend = get_backend("sandbox_exec")
    args = backend.wrap("true", cfg)
    try:
        with open(args[2]) as f:
            content = f.read()
        for sys_dir in READONLY_SYSTEM_DIRS:
            assert f'(allow file-read* (subpath "{sys_dir}"))' in content
    finally:
        backend.cleanup()


def test_cleanup_removes_profile() -> None:
    cfg = make_config()
    backend = get_backend("sandbox_exec")
    args = backend.wrap("true", cfg)
    profile_path = args[2]
    assert os.path.isfile(profile_path)
    backend.cleanup()
    assert not os.path.isfile(profile_path)


def test_cleanup_is_idempotent() -> None:
    cfg = make_config()
    backend = get_backend("sandbox_exec")
    args = backend.wrap("true", cfg)
    backend.cleanup()
    backend.cleanup()  # does not raise


def test_wrap_profile_contains_network_allow() -> None:
    cfg = make_config()
    backend = get_backend("sandbox_exec")
    args = backend.wrap("true", cfg)
    try:
        with open(args[2]) as f:
            content = f.read()
        assert "(allow network*)" in content
    finally:
        backend.cleanup()
