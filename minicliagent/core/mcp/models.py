from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MCPServerConfig:
    name: str
    command: list[str]
    cwd: Path | None = None
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    timeout_seconds: float = 10.0
    max_return_chars: int = 20000
    tool_prefix: str | None = None


@dataclass(frozen=True)
class MCPServerDiagnostic:
    name: str
    enabled: bool
    healthy: bool
    tool_count: int
    command: list[str]
    tool_prefix: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class MCPToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class MCPToolCallResult:
    content: str
    is_error: bool = False
    diagnostics: dict[str, Any] = field(default_factory=dict)
