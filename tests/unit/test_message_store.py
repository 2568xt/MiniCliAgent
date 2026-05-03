import json
from pathlib import Path

from minicliagent.core.runtime.message_store import FileMessageStore


def test_file_message_store_persists_messages(tmp_path: Path) -> None:
    store = FileMessageStore(tmp_path)

    store.append("session-1", {"role": "user", "content": "hello"})
    messages = store.get("session-1")

    assert messages == [{"role": "user", "content": "hello"}]
    payload = json.loads((tmp_path / "session-1.json").read_text())
    assert payload == messages
