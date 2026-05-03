from __future__ import annotations

from minicliagent.core.skills.loader import SkillLoader
from minicliagent.core.tools.models import ToolResult


def list_skills_tool(loader: SkillLoader) -> ToolResult:
    skills = loader.list_skills()
    if not skills:
        return ToolResult(content="")
    return ToolResult(content="\n".join(skill.name for skill in skills))


def load_skill_tool(loader: SkillLoader, name: str) -> ToolResult:
    try:
        document = loader.load(name)
    except KeyError:
        return ToolResult(content=f"Unknown skill: {name}", is_error=True)
    return ToolResult(content=document.body)
