from __future__ import annotations

import json
import shutil
from pathlib import Path

from minicliagent.core.team.protocols import TeamMessage


class MessageBus:
    def __init__(self, inbox_dir: Path) -> None:
        self.inbox_dir = inbox_dir
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, recipient: str) -> Path:
        return self.inbox_dir / f"{recipient}.jsonl"

    def _staging_path(self, recipient: str) -> Path:
        return self.inbox_dir / f"{recipient}.jsonl.staging"

    def send(self, message: TeamMessage) -> None:
        with self._path(message.recipient).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(message.to_dict(), ensure_ascii=False) + "\n")

    def read_inbox(self, recipient: str) -> list[TeamMessage]:
        """Two-phase read: messages survive in staging until ack_inbox is called.

        Phase 1 (read): reads and returns all available messages.
          - If no staging exists: atomically moves main inbox to staging, returns messages.
          - If staging exists: reads staging (un-acked from crash) AND new messages from main.
        Phase 2 (ack): agent calls ack_inbox() after processing to delete staging.
        """
        staging = self._staging_path(recipient)
        staging_existed = staging.exists()

        messages: list[TeamMessage] = []

        # Read stale staging from a previous crash/un-acked read
        if staging_existed:
            messages.extend(
                TeamMessage.from_dict(json.loads(line))
                for line in staging.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )

        # Move main inbox atomically to staging if staging didn't pre-exist
        path = self._path(recipient)
        if path.exists():
            new_messages = [
                TeamMessage.from_dict(json.loads(line))
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            messages.extend(new_messages)
            if not staging_existed:
                # First read this session: atomically move main to staging
                shutil.move(str(path), str(staging))
            else:
                # Staging existed (crash protection): clear main
                path.write_text("", encoding="utf-8")

        return messages

    def ack_inbox(self, recipient: str) -> None:
        """Delete the staging file after successful message processing."""
        staging = self._staging_path(recipient)
        if staging.exists():
            staging.unlink()
