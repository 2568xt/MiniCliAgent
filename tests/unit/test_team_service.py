from pathlib import Path

from minicliagent.app.team_service import TeamService
from minicliagent.core.team.bus import MessageBus


def test_team_service_send_and_read_inbox(tmp_path: Path) -> None:
    service = TeamService(bus=MessageBus(tmp_path))

    service.send_message("lead", "worker", "hello")
    inbox = service.read_inbox("worker")

    assert len(inbox) == 1
    assert inbox[0].content == "hello"
