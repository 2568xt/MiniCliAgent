from __future__ import annotations

import json
import time
from pathlib import Path


class EventBus:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("")

    def emit(self, event: str, payload: dict) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps({"ts": time.time(), "event": event, "payload": payload}, ensure_ascii=False) + "\n"
            )
