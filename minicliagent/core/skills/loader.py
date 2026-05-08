from __future__ import annotations

from pathlib import Path

from minicliagent.core.skills.models import SkillDocument, SkillSummary


class SkillLoader:
    def __init__(self, roots: list[Path]) -> None:
        self.roots = roots
        self._index = self._scan()

    def _scan(self) -> dict[str, SkillSummary]:
        index: dict[str, SkillSummary] = {}
        for root in self.roots:
            if not root.exists():
                continue
            for skill_file in sorted(root.rglob("SKILL.md")):
                name, description, _ = self._parse_skill_file(skill_file)
                index[name] = SkillSummary(name=name, description=description, path=skill_file)
        return index

    def _parse_skill_file(self, path: Path) -> tuple[str, str, str]:
        text = path.read_text()
        if text.startswith("---\n"):
            _, frontmatter, body = text.split("---\n", 2)
            try:
                import yaml
                meta = yaml.safe_load(frontmatter) or {}
            except Exception:
                meta = {}
                for line in frontmatter.strip().splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        meta[key.strip()] = value.strip()
            name = meta.get("name", "") or path.parent.name
            description = meta.get("description", "") or ""
            return name, description, body.strip()
        return path.parent.name, "", text.strip()

    def list_skills(self) -> list[SkillSummary]:
        return sorted(self._index.values(), key=lambda item: item.name)

    def load(self, name: str) -> SkillDocument:
        summary = self._index[name]
        skill_name, description, body = self._parse_skill_file(summary.path)
        return SkillDocument(name=skill_name, description=description, path=summary.path, body=body)
