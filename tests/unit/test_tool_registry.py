import pytest

from minicliagent.core.tools.models import ToolResult, ToolSpec
from minicliagent.core.tools.registry import ToolRegistry


def test_tool_registry_registers_and_dispatches() -> None:
    registry = ToolRegistry()

    registry.register(
        ToolSpec(
            name="echo",
            description="Echo input",
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
            handler=lambda text: ToolResult(content=text),
            tags={"test"},
        )
    )

    result = registry.execute("echo", {"text": "hello"})

    assert result.content == "hello"


def test_tool_registry_rejects_duplicate_names() -> None:
    registry = ToolRegistry()
    spec = ToolSpec(
        name="echo",
        description="Echo input",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=lambda: ToolResult(content="ok"),
        tags=set(),
    )

    registry.register(spec)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(spec)
