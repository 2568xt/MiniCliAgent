from __future__ import annotations

from dataclasses import dataclass

from minicliagent.core.skills.loader import SkillLoader
from minicliagent.core.skills.matcher import SkillMatcher
from minicliagent.core.skills.models import SkillDocument, SkillSummary


@dataclass
class SkillService:
    loader: SkillLoader
    matcher: SkillMatcher | None = None
    max_skill_chars: int = 4000

    def list_skills(self) -> list[SkillSummary]:
        return self.loader.list_skills()

    def load_skill(self, name: str) -> SkillDocument:
        document = self.loader.load(name)
        body = document.body[: self.max_skill_chars]
        return SkillDocument(
            name=document.name,
            description=document.description,
            path=document.path,
            body=body,
        )

    def match_skills(self, query: str) -> list[SkillSummary]:
        matcher = self.matcher or SkillMatcher(self.loader)
        return matcher.match(query)
