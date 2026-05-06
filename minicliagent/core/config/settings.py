from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from minicliagent.core.mcp.models import MCPServerConfig


@dataclass(frozen=True)
class Settings:
    model: str
    workspace_root: Path
    state_root: Path
    sessions_dir: Path
    tasks_dir: Path
    team_dir: Path
    worktrees_dir: Path
    logs_dir: Path
    memory_enabled: bool
    memory_summary_path: Path
    memory_dir: Path
    memory_index_dir: Path
    memory_dense_weight: float
    memory_bm25_weight: float
    memory_dense_top_k: int
    memory_bm25_top_k: int
    memory_final_top_k: int
    mcp_servers: list[MCPServerConfig]

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "Settings":
        workspace_root = Path(env.get("MINICLIAGENT_WORKSPACE", ".")).resolve()
        state_root = workspace_root / ".minicliagent"
        return cls(
            model=env.get("MINICLIAGENT_MODEL", "claude-3-7-sonnet-latest"),
            workspace_root=workspace_root,
            state_root=state_root,
            sessions_dir=state_root / "sessions",
            tasks_dir=state_root / "tasks",
            team_dir=state_root / "team",
            worktrees_dir=state_root / "worktrees",
            logs_dir=state_root / "logs",
            memory_enabled=_env_bool(env.get("MINICLIAGENT_MEMORY_ENABLED", "1")),
            memory_summary_path=state_root / "memory.md",
            memory_dir=state_root / "memory",
            memory_index_dir=state_root / "memory_index",
            memory_dense_weight=float(env.get("MINICLIAGENT_MEMORY_DENSE_WEIGHT", "0.7")),
            memory_bm25_weight=float(env.get("MINICLIAGENT_MEMORY_BM25_WEIGHT", "0.3")),
            memory_dense_top_k=int(env.get("MINICLIAGENT_MEMORY_DENSE_TOP_K", "4")),
            memory_bm25_top_k=int(env.get("MINICLIAGENT_MEMORY_BM25_TOP_K", "4")),
            memory_final_top_k=int(env.get("MINICLIAGENT_MEMORY_FINAL_TOP_K", "6")),
            mcp_servers=_parse_mcp_servers(env.get("MINICLIAGENT_MCP_SERVERS", "")),
        )


def _env_bool(value: str) -> bool:
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _parse_mcp_servers(raw: str) -> list[MCPServerConfig]:
    if not raw.strip():
        return []
    servers: list[MCPServerConfig] = []
    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [part.strip() for part in chunk.split(",") if part.strip()]
        if len(parts) < 2:
            continue
        name, command = parts[0], parts[1]
        tool_prefix = parts[2] if len(parts) >= 3 else None
        enabled = True
        timeout_seconds = 10.0
        max_return_chars = 20000
        cwd = None
        env = {}
        for item in parts[3:]:
            if item.startswith("timeout="):
                timeout_seconds = float(item.split("=", 1)[1])
            elif item.startswith("max_return_chars="):
                max_return_chars = int(item.split("=", 1)[1])
            elif item.startswith("cwd="):
                cwd = Path(item.split("=", 1)[1]).expanduser().resolve()
            elif item.startswith("enabled="):
                enabled = _env_bool(item.split("=", 1)[1])
            elif item.startswith("env."):
                key, value = item[4:].split("=", 1)
                env[key] = value
        servers.append(
            MCPServerConfig(
                name=name,
                command=command.split(),
                cwd=cwd,
                env=env,
                enabled=enabled,
                timeout_seconds=timeout_seconds,
                max_return_chars=max_return_chars,
                tool_prefix=tool_prefix,
            )
        )
    return servers
