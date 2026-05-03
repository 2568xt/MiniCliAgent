import pytest

from minicliagent.core.team.protocols import TeamMessage, validate_message_type


def test_validate_message_type_accepts_known_values() -> None:
    assert validate_message_type("message") == "message"
    assert validate_message_type("shutdown_request") == "shutdown_request"


def test_validate_message_type_rejects_unknown_values() -> None:
    with pytest.raises(ValueError, match="Unsupported message type"):
        validate_message_type("unknown")


def test_team_message_to_dict_roundtrip() -> None:
    message = TeamMessage(
        message_type="message",
        sender="lead",
        recipient="worker",
        content="hello",
        request_id="req-1",
    )

    payload = message.to_dict()

    assert payload["type"] == "message"
    assert payload["request_id"] == "req-1"
