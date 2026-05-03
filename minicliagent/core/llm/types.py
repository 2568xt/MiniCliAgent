from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


TextDeltaCallback = Callable[[str], None]


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ModelRequest:
    system: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] = field(default_factory=list)
    max_tokens: int = 4096


@dataclass
class ModelResponse:
    stop_reason: str
    text: str
    tool_calls: list[ToolCall]
