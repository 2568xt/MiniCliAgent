import json
from pathlib import Path

from minicliagent.core.llm.types import ModelRequest, ModelResponse, ToolCall
from minicliagent.core.runtime.agent_runtime import AgentRuntime
from minicliagent.core.runtime.event_bus import EventBus
from minicliagent.core.tools.models import ToolResult, ToolSpec
from minicliagent.core.tools.registry import ToolRegistry
from minicliagent.infra.logging.setup import JsonLogger, TranscriptRecorder


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def create_response(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            return ModelResponse(
                stop_reason="tool_use",
                text="",
                tool_calls=[ToolCall(id="t1", name="load_skill", input={"name": "demo"})],
            )
        return ModelResponse(stop_reason="end_turn", text="done", tool_calls=[])


def test_runtime_records_events_transcript_and_loaded_skills(tmp_path: Path) -> None:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="load_skill",
            description="Load skill",
            input_schema={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
            handler=lambda name: ToolResult(content=f"skill:{name}"),
            tags={"skills"},
        )
    )
    runtime = AgentRuntime(
        provider=FakeProvider(),
        tool_registry=registry,
        system_prompt="system",
        event_bus=EventBus(tmp_path / "events.jsonl"),
        logger=JsonLogger(tmp_path / "app.jsonl"),
        transcript_recorder=TranscriptRecorder(tmp_path / "transcripts"),
    )

    result = runtime.run_turn("s1", "hello")

    assert result.output_text == "done"
    events = (tmp_path / "events.jsonl").read_text()
    assert "tool_call" in events
    transcript = json.loads((tmp_path / "transcripts" / "s1.json").read_text())
    assert transcript[-1]["content"] == "done"
    assert runtime.loaded_skills["s1"] == ["demo"]
