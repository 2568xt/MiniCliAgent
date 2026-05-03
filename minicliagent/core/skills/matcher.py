from __future__ import annotations

from minicliagent.core.skills.loader import SkillLoader
from minicliagent.core.skills.models import SkillSummary


class SkillMatcher:
    def __init__(self, loader: SkillLoader) -> None:
        self.loader = loader

    def match(self, query: str) -> list[SkillSummary]:
        query_lower = query.lower()
        matches = []
        for skill in self.loader.list_skills():
            haystack = f"{skill.name} {skill.description}".lower()
            if any(token in haystack for token in query_lower.split()):
                matches.append(skill)
        return matches
