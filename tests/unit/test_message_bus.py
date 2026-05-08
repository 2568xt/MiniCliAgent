from pathlib import Path

from minicliagent.core.team.bus import MessageBus
from minicliagent.core.team.protocols import TeamMessage


def test_message_bus_send_and_read(tmp_path: Path) -> None:
    """Two-phase read: message survives in staging until explicitly acked."""
    bus = MessageBus(tmp_path)
    message = TeamMessage(
        message_type="message",
        sender="lead",
        recipient="worker",
        content="hello",
    )

    bus.send(message)
    inbox = bus.read_inbox("worker")

    assert len(inbox) == 1
    assert inbox[0].content == "hello"

    # Second read without ack still returns staging (crash protection)
    assert len(bus.read_inbox("worker")) == 1

    # After ack, inbox is cleared
    bus.ack_inbox("worker")
    assert bus.read_inbox("worker") == []


def test_message_bus_ack_without_staging(tmp_path: Path) -> None:
    """ack_inbox on empty staging is a no-op."""
    bus = MessageBus(tmp_path)
    bus.ack_inbox("worker")  # should not raise
    assert bus.read_inbox("worker") == []
