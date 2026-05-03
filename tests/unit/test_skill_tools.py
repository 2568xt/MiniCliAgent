from pathlib import Path

from minicliagent.core.tools.builtins.skills import list_skills_tool, load_skill_tool
from minicliagent.core.skills.loader import SkillLoader


def test_list_skills_tool_returns_skill_names(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: demo\ndescription: Demo\n---\n\nBody\n")
    loader = SkillLoader([tmp_path])

    result = list_skills_tool(loader)

    assert result.is_error is False
    assert "demo" in result.content


def test_load_skill_tool_returns_body(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: demo\ndescription: Demo\n---\n\nBody\n")
    loader = SkillLoader([tmp_path])

    result = load_skill_tool(loader, "demo")

    assert result.is_error is False
    assert "Body" in result.content
