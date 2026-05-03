import json
from pathlib import Path

from minicliagent.infra.logging.setup import JsonLogger, TranscriptRecorder


def test_json_logger_writes_jsonl(tmp_path: Path) -> None:
    logger = JsonLogger(tmp_path / "app.jsonl")
    logger.log("info", "hello", source="test")

    payload = json.loads((tmp_path / "app.jsonl").read_text().strip())
    assert payload["level"] == "info"
    assert payload["message"] == "hello"


def test_transcript_recorder_writes_session_messages(tmp_path: Path) -> None:
    recorder = TranscriptRecorder(tmp_path)
    recorder.record("s1", [{"role": "user", "content": "hello"}])

    payload = json.loads((tmp_path / "s1.json").read_text())
    assert payload[0]["content"] == "hello"
