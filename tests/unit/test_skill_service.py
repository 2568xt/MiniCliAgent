from pathlib import Path

from minicliagent.app.skill_service import SkillService
from minicliagent.core.skills.loader import SkillLoader


def test_skill_service_delegates_to_loader(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo skill\n---\n\nBody\n"
    )

    service = SkillService(loader=SkillLoader([tmp_path]))
    names = [skill.name for skill in service.list_skills()]

    assert names == ["demo"]
    assert service.load_skill("demo").body == "Body"
