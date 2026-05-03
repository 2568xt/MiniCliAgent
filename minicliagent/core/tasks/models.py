from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TaskRecord:
    id: int
    subject: str
    description: str
    status: str = "pending"
    owner: str = ""
    priority: str = "normal"
    blocked_by: list[int] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    worktree: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
