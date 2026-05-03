from pathlib import Path

from minicliagent.app.agent_service import create_agent_service


def test_process_env_workspace_takes_precedence_over_dotenv(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MINICLIAGENT_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("MINICLIAGENT_MODEL", "claude-test")

    service = create_agent_service()

    assert service.settings.workspace_root == tmp_path
