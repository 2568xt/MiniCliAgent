from __future__ import annotations

from minicliagent.core.tools.models import ToolSpec


def tool_specs_to_anthropic(specs: list[ToolSpec]) -> list[dict]:
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "input_schema": spec.input_schema,
        }
        for spec in specs
    ]
