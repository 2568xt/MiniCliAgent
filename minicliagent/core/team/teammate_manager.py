from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Teammate:
    name: str
    role: str
    status: str = "idle"


class TeammateManager:
    def __init__(self) -> None:
        self._members: dict[str, Teammate] = {}

    def add_member(self, name: str, role: str) -> Teammate:
        teammate = Teammate(name=name, role=role)
        self._members[name] = teammate
        return teammate

    def set_status(self, name: str, status: str) -> Teammate:
        teammate = self._members[name]
        teammate.status = status
        return teammate

    def list_members(self) -> list[Teammate]:
        return list(self._members.values())
