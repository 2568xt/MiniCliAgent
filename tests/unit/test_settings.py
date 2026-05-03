from pathlib import Path

from minicliagent.core.config.settings import Settings


def test_settings_build_workspace_state_paths(tmp_path: Path) -> None:
    settings = Settings.from_env(
        {
            "MINICLIAGENT_WORKSPACE": str(tmp_path),
            "MINICLIAGENT_MODEL": "claude-test",
        }
    )

    assert settings.workspace_root == tmp_path
    assert settings.state_root == tmp_path / ".minicliagent"
    assert settings.sessions_dir == settings.state_root / "sessions"
    assert settings.tasks_dir == settings.state_root / "tasks"
