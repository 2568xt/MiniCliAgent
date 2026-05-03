from __future__ import annotations

from minicliagent.app.team_service import TeamService
from minicliagent.core.tools.models import ToolResult


def team_send_tool(service: TeamService, sender: str, recipient: str, content: str) -> ToolResult:
    service.send_message(sender, recipient, content)
    return ToolResult(content="sent")


def team_inbox_tool(service: TeamService, recipient: str) -> ToolResult:
    messages = service.read_inbox(recipient)
    if not messages:
        return ToolResult(content="")
    return ToolResult(content="\n".join(f"{message.sender}: {message.content}" for message in messages))
