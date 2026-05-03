from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class WorktreeRecord:
    name: str
    path: Path
    branch: str
    task_id: int | None
    status: str = "active"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        return payload
