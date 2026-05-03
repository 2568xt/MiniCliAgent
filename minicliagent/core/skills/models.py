from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillSummary:
    name: str
    description: str
    path: Path


@dataclass(frozen=True)
class SkillDocument:
    name: str
    description: str
    path: Path
    body: str
