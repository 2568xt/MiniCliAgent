import json
from pathlib import Path

from minicliagent.core.runtime.event_bus import EventBus


def test_event_bus_emits_jsonl_events(tmp_path: Path) -> None:
    bus = EventBus(tmp_path / "events.jsonl")
    bus.emit("tool_call", {"name": "bash"})

    payload = json.loads((tmp_path / "events.jsonl").read_text().strip())
    assert payload["event"] == "tool_call"
    assert payload["payload"]["name"] == "bash"
