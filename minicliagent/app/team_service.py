from __future__ import annotations

from dataclasses import dataclass

from minicliagent.core.team.bus import MessageBus
from minicliagent.core.team.protocols import (
    TeamMessage,
    create_plan_approval_request,
    create_shutdown_request,
    create_task_claim,
)


@dataclass
class TeamService:
    bus: MessageBus

    def send_message(self, sender: str, recipient: str, content: str, request_id: str = "") -> None:
        self.bus.send(
            TeamMessage(
                message_type="message",
                sender=sender,
                recipient=recipient,
                content=content,
                request_id=request_id,
            )
        )

    def read_inbox(self, recipient: str) -> list[TeamMessage]:
        return self.bus.read_inbox(recipient)

    def send_shutdown_request(self, sender: str, recipient: str, content: str) -> TeamMessage:
        message = create_shutdown_request(sender, recipient, content)
        self.bus.send(message)
        return message

    def send_plan_approval_request(self, sender: str, recipient: str, content: str) -> TeamMessage:
        message = create_plan_approval_request(sender, recipient, content)
        self.bus.send(message)
        return message

    def send_task_claim(self, sender: str, recipient: str, content: str) -> TeamMessage:
        message = create_task_claim(sender, recipient, content)
        self.bus.send(message)
        return message
