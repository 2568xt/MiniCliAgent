from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static


class ConversationView(VerticalScroll):
    """Scrollable conversation log with user/assistant styling.

    Uses Static (not RichLog) so that append_streaming_text can
    extend the last line in-place — this avoids RichLog's per-write
    paragraph behaviour which breaks character-by-character streaming.
    """

    def compose(self) -> None:
        self._static = Static("")
        yield self._static

    def on_mount(self) -> None:
        self._lines: list[str] = ["[dim italic]Session started. Type a message below.[/]"]
        self._refresh()

    def add_user_message(self, text: str) -> None:
        self._lines.append("")
        self._lines.append(f"[bold green]You[/] {text}")
        self._refresh()

    def start_assistant_message(self) -> None:
        self._lines.append("")
        self._lines.append("[bold cyan]Agent[/] ")
        self._refresh()

    def append_streaming_text(self, text: str) -> None:
        self._lines[-1] += text
        self._refresh()

    def write(self, text: str) -> None:
        """Append a line — kept for error-message compatibility."""
        self._lines.append(text)
        self._refresh()

    def clear(self) -> None:
        self._lines = []
        self._refresh()

    def _refresh(self) -> None:
        self._static.update("\n".join(self._lines))
        self.call_after_refresh(self.scroll_end, animate=False)
