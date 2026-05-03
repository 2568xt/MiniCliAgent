from pathlib import Path

from minicliagent.app.team_service import TeamService
from minicliagent.core.team.bus import MessageBus
from minicliagent.core.tools.builtins.team import team_inbox_tool, team_send_tool


def test_team_send_tool_writes_message(tmp_path: Path) -> None:
    service = TeamService(bus=MessageBus(tmp_path))

    result = team_send_tool(service, "lead", "worker", "hello")

    assert result.is_error is False
    assert "sent" in result.content.lower()


def test_team_inbox_tool_reads_messages(tmp_path: Path) -> None:
    service = TeamService(bus=MessageBus(tmp_path))
    service.send_message("lead", "worker", "hello")

    result = team_inbox_tool(service, "worker")

    assert result.is_error is False
    assert "lead: hello" in result.content
