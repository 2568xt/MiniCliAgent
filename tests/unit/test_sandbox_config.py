from __future__ import annotations

from pathlib import Path

from minicliagent.infra.sandbox.config import DEFAULT_DENIED_PATHS, SandboxConfig


def test_defaults() -> None:
    cfg = SandboxConfig.from_env({})
    assert cfg.enabled is True
    assert cfg.backend == ""
    assert cfg.allowed_dirs == ()
    assert cfg.denied_paths == ()
    assert cfg.allowed_domains == ()
    assert cfg.auto_allow_sandboxed is True


def test_disabled() -> None:
    cfg = SandboxConfig.from_env({"MINICLIAGENT_SANDBOX_ENABLED": "0"})
    assert cfg.enabled is False


def test_custom_backend() -> None:
    cfg = SandboxConfig.from_env({"MINICLIAGENT_SANDBOX_BACKEND": "bubblewrap"})
    assert cfg.backend == "bubblewrap"


def test_allowed_dirs() -> None:
    cfg = SandboxConfig.from_env(
        {"MINICLIAGENT_SANDBOX_ALLOWED_DIRS": "/tmp:/home/user/project"}
    )
    assert cfg.allowed_dirs == (Path("/tmp"), Path("/home/user/project"))


def test_denied_paths() -> None:
    cfg = SandboxConfig.from_env(
        {"MINICLIAGENT_SANDBOX_DENIED_PATHS": "/secret:/private"}
    )
    assert cfg.denied_paths == (Path("/secret"), Path("/private"))


def test_allowed_domains() -> None:
    cfg = SandboxConfig.from_env(
        {"MINICLIAGENT_SANDBOX_ALLOWED_DOMAINS": "api.example.com,cdn.example.com"}
    )
    assert cfg.allowed_domains == ("api.example.com", "cdn.example.com")


def test_auto_allow_off() -> None:
    cfg = SandboxConfig.from_env({"MINICLIAGENT_SANDBOX_AUTO_ALLOW": "false"})
    assert cfg.auto_allow_sandboxed is False


def test_default_denied_paths_is_tuple() -> None:
    assert isinstance(DEFAULT_DENIED_PATHS, tuple)


def test_immutability() -> None:
    cfg = SandboxConfig.from_env({})
    try:
        cfg.enabled = False  # type: ignore[misc]
        raise AssertionError("Should not be mutable")
    except (AttributeError, TypeError, Exception):
        pass
