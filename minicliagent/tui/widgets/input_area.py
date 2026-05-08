from __future__ import annotations

from textual.events import Key
from textual.widgets import Input


class InputArea(Input):
    """Prompt input with command history (Up/Down to navigate)."""

    def on_mount(self) -> None:
        self.placeholder = "Type a message... (Enter to send, Ctrl+Q to quit)"
        self.history: list[str] = []
        self._history_index: int = -1

    def append_to_history(self, text: str) -> None:
        if self.history and self.history[-1] == text:
            return
        self.history.append(text)

    def _on_key(self, event: Key) -> None:
        if event.key == "up" and self.history:
            event.stop()
            if self._history_index == -1:
                self._history_index = len(self.history) - 1
            elif self._history_index > 0:
                self._history_index -= 1
            self.value = self.history[self._history_index]
            self.cursor_position = len(self.value)
        elif event.key == "down" and self.history:
            event.stop()
            if self._history_index == -1:
                return
            elif self._history_index < len(self.history) - 1:
                self._history_index += 1
                self.value = self.history[self._history_index]
                self.cursor_position = len(self.value)
            else:
                self._history_index = -1
                self.value = ""
        else:
            self._history_index = -1
            super()._on_key(event)
