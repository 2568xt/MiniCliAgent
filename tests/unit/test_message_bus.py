from pathlib import Path

from minicliagent.core.team.bus import MessageBus
from minicliagent.core.team.protocols import TeamMessage


def test_message_bus_send_and_read(tmp_path: Path) -> None:
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
    assert bus.read_inbox("worker") == []
