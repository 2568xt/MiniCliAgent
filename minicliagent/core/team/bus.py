from __future__ import annotations

import json
from pathlib import Path

from minicliagent.core.team.protocols import TeamMessage


class MessageBus:
    def __init__(self, inbox_dir: Path) -> None:
        self.inbox_dir = inbox_dir
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, recipient: str) -> Path:
        return self.inbox_dir / f"{recipient}.jsonl"

    def send(self, message: TeamMessage) -> None:
        with self._path(message.recipient).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(message.to_dict(), ensure_ascii=False) + "\n")

    def read_inbox(self, recipient: str) -> list[TeamMessage]:
        path = self._path(recipient)
        if not path.exists():
            return []
        messages = [
            TeamMessage.from_dict(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        path.write_text("", encoding="utf-8")
        return messages
