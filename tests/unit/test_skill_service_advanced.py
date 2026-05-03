from pathlib import Path

from minicliagent.app.skill_service import SkillService
from minicliagent.core.skills.loader import SkillLoader
from minicliagent.core.skills.matcher import SkillMatcher


def test_skill_service_trims_loaded_body(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: demo\ndescription: Demo skill\n---\n\n1234567890abcdef\n")

    service = SkillService(loader=SkillLoader([tmp_path]), max_skill_chars=5)

    assert service.load_skill("demo").body == "12345"


def test_skill_service_matches_skills(tmp_path: Path) -> None:
    skill_dir = tmp_path / "review"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: review\ndescription: code review helper\n---\n\nBody\n")

    service = SkillService(loader=SkillLoader([tmp_path]), matcher=SkillMatcher(SkillLoader([tmp_path])))

    assert service.match_skills("review code")[0].name == "review"
