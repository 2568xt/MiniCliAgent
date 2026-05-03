from __future__ import annotations

import json
from pathlib import Path


class InMemoryMessageStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[dict]] = {}

    def get(self, session_id: str) -> list[dict]:
        return self._sessions.setdefault(session_id, [])

    def append(self, session_id: str, message: dict) -> list[dict]:
        messages = self.get(session_id)
        messages.append(message)
        return messages


class FileMessageStore:
    def __init__(self, sessions_dir: Path) -> None:
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def get(self, session_id: str) -> list[dict]:
        path = self._path(session_id)
        if not path.exists():
            return []
        return json.loads(path.read_text())

    def append(self, session_id: str, message: dict) -> list[dict]:
        messages = self.get(session_id)
        messages.append(message)
        self._path(session_id).write_text(json.dumps(messages, indent=2))
        return messages
