from __future__ import annotations

from minicliagent.core.tools.models import ToolResult, ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool '{spec.name}' already registered")
        self._tools[spec.name] = spec

    def execute(self, name: str, payload: dict) -> ToolResult:
        spec = self._tools[name]
        return spec.handler(**payload)

    def list_specs(self) -> list[ToolSpec]:
        return list(self._tools.values())
