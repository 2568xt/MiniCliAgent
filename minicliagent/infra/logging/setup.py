from __future__ import annotations

import json
import time
from pathlib import Path


class JsonLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, level: str, message: str, **extra) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {"ts": time.time(), "level": level, "message": message, **extra},
                    ensure_ascii=False,
                )
                + "\n"
            )


class TranscriptRecorder:
    def __init__(self, transcript_dir: Path) -> None:
        self.transcript_dir = transcript_dir
        self.transcript_dir.mkdir(parents=True, exist_ok=True)

    def record(self, session_id: str, messages: list[dict]) -> None:
        (self.transcript_dir / f"{session_id}.json").write_text(
            json.dumps(messages, indent=2, ensure_ascii=False)
        )
