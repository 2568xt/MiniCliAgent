from __future__ import annotations

from dataclasses import dataclass
import uuid


VALID_MESSAGE_TYPES = {
    "message",
    "broadcast",
    "shutdown_request",
    "shutdown_response",
    "plan_approval_request",
    "plan_approval_response",
    "task_claim",
    "task_claim_result",
}


def validate_message_type(message_type: str) -> str:
    if message_type not in VALID_MESSAGE_TYPES:
        raise ValueError(f"Unsupported message type: {message_type}")
    return message_type


@dataclass(frozen=True)
class TeamMessage:
    message_type: str
    sender: str
    recipient: str
    content: str
    request_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "type": validate_message_type(self.message_type),
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "request_id": self.request_id,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, str]) -> "TeamMessage":
        return cls(
            message_type=validate_message_type(payload["type"]),
            sender=payload["sender"],
            recipient=payload["recipient"],
            content=payload["content"],
            request_id=payload.get("request_id", ""),
        )


def generate_request_id() -> str:
    return f"req-{uuid.uuid4().hex[:8]}"


def create_shutdown_request(sender: str, recipient: str, content: str) -> TeamMessage:
    return TeamMessage("shutdown_request", sender, recipient, content, request_id=generate_request_id())


def create_plan_approval_request(sender: str, recipient: str, content: str) -> TeamMessage:
    return TeamMessage("plan_approval_request", sender, recipient, content, request_id=generate_request_id())


def create_task_claim(sender: str, recipient: str, content: str) -> TeamMessage:
    return TeamMessage("task_claim", sender, recipient, content, request_id=generate_request_id())


def create_shutdown_response(sender: str, recipient: str, content: str, request_id: str) -> TeamMessage:
    return TeamMessage("shutdown_response", sender, recipient, content, request_id=request_id)


def create_plan_approval_response(sender: str, recipient: str, content: str, request_id: str) -> TeamMessage:
    return TeamMessage("plan_approval_response", sender, recipient, content, request_id=request_id)


def create_task_claim_result(sender: str, recipient: str, content: str, request_id: str) -> TeamMessage:
    return TeamMessage("task_claim_result", sender, recipient, content, request_id=request_id)
