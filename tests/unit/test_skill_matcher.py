from pathlib import Path

from minicliagent.core.skills.loader import SkillLoader
from minicliagent.core.skills.matcher import SkillMatcher


def test_skill_matcher_matches_by_query_text(tmp_path: Path) -> None:
    skill_dir = tmp_path / "review"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: review\ndescription: code review helper\n---\n\nBody\n")
    matcher = SkillMatcher(SkillLoader([tmp_path]))

    matches = matcher.match("please review this code")

    assert matches[0].name == "review"
