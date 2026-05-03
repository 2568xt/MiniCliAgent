from minicliagent.core.llm.tool_adapter import tool_specs_to_anthropic
from minicliagent.core.tools.models import ToolResult, ToolSpec


def test_tool_specs_to_anthropic_shape() -> None:
    specs = [
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
    ]

    payload = tool_specs_to_anthropic(specs)

    assert payload == [
        {
            "name": "echo",
            "description": "Echo input",
            "input_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }
    ]
