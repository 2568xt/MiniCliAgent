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
    assert settings.memory_enabled is True
    assert settings.memory_summary_path == settings.state_root / "memory.md"
    assert settings.memory_dir == settings.state_root / "memory"
    assert settings.memory_index_dir == settings.state_root / "memory_index"
    assert settings.memory_dense_weight == 0.7
    assert settings.memory_bm25_weight == 0.3
    assert settings.memory_dense_top_k == 4
    assert settings.memory_bm25_top_k == 4
    assert settings.memory_final_top_k == 6
    assert settings.mcp_servers == []


def test_settings_can_disable_memory_and_override_search_config(tmp_path: Path) -> None:
    settings = Settings.from_env(
        {
            "MINICLIAGENT_WORKSPACE": str(tmp_path),
            "MINICLIAGENT_MEMORY_ENABLED": "0",
            "MINICLIAGENT_MEMORY_DENSE_WEIGHT": "0.6",
            "MINICLIAGENT_MEMORY_BM25_WEIGHT": "0.4",
            "MINICLIAGENT_MEMORY_DENSE_TOP_K": "8",
            "MINICLIAGENT_MEMORY_BM25_TOP_K": "7",
            "MINICLIAGENT_MEMORY_FINAL_TOP_K": "5",
        }
    )

    assert settings.memory_enabled is False
    assert settings.memory_dense_weight == 0.6
    assert settings.memory_bm25_weight == 0.4
    assert settings.memory_dense_top_k == 8
    assert settings.memory_bm25_top_k == 7
    assert settings.memory_final_top_k == 5
