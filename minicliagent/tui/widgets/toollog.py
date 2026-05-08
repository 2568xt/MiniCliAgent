from __future__ import annotations

from rich.text import Text
from textual.widgets import RichLog


class ToolLog(RichLog):
    """Compact sidebar showing tool invocations in real time."""

    def on_mount(self) -> None:
        self.auto_scroll = True
        self.border_title = "Tool Calls"
        self.write(Text("Waiting for tool calls...", style="dim italic"))

    def add_tool_call(self, name: str, inputs: dict) -> None:
        summary = _summarize_inputs(name, inputs)
        line = Text()
        line.append("> ", style="yellow")
        line.append(name, style="bold yellow")
        line.append(f"  {summary}", style="dim white")
        self.write(line)


def _summarize_inputs(name: str, inputs: dict) -> str:
    if name == "bash":
        cmd = inputs.get("command", "")
        return cmd[:60] + ("..." if len(cmd) > 60 else "")
    if name in ("read_file", "write_file", "edit_file"):
        return inputs.get("path", "")[:60]
    if name == "memory_search":
        return inputs.get("query", "")[:60]
    for v in inputs.values():
        s = str(v)[:60]
        if s:
            return s
    return ""
