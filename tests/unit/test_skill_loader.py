from pathlib import Path

from minicliagent.core.skills.loader import SkillLoader


def test_skill_loader_lists_and_loads_skill(tmp_path: Path) -> None:
    skill_dir = tmp_path / "review-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: review-skill\n"
        "description: Review code carefully\n"
        "---\n"
        "\n"
        "# Review Skill\n"
        "Check logic and tests.\n"
    )

    loader = SkillLoader([tmp_path])
    summaries = loader.list_skills()

    assert len(summaries) == 1
    assert summaries[0].name == "review-skill"
    loaded = loader.load("review-skill")
    assert loaded.body.startswith("# Review Skill")
    assert loaded.description == "Review code carefully"
