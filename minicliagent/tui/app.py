from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Header, Input, Label

from minicliagent.app.agent_service import AgentService
from minicliagent.tui.bridge import TuiBridge
from minicliagent.tui.widgets.conversation import ConversationView
from minicliagent.tui.widgets.input_area import InputArea
from minicliagent.tui.widgets.toollog import ToolLog


THINKING_FRAMES = ["(´･ω･`) 思考中...", "(´･ω･`) 思考中....", "(´･ω･`) 思考中....."]
CHAR_SPEED = 0.018

SLASH_COMMANDS = {
    "/quit": "退出",
    "/exit": "退出",
    "/clear": "清屏",
}


class AgentTuiApp(App):
    """Textual TUI for MiniCLIAgent interactive sessions."""

    CSS_PATH = Path(__file__).parent / "theme.css"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_screen", "Clear", show=True),
    ]

    def __init__(
        self,
        service: AgentService,
        session_id: str,
        initial_prompt: str | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._session_id = session_id
        self._initial_prompt = initial_prompt
        self._bridge: TuiBridge | None = None
        self._streaming: bool = False
        self._text_queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._thinking_timer: asyncio.Timer | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield ConversationView(id="conversation")
            yield ToolLog(id="toollog")
        yield Label("", id="thinking")
        yield InputArea(id="input-area")

    def on_mount(self) -> None:
        self._bridge = TuiBridge(self, self._service, self._session_id)
        self.query_one("#input-area", InputArea).focus()

        if self._initial_prompt:
            self._submit_prompt(self._initial_prompt)

    def on_unmount(self) -> None:
        self._stop_thinking()
        if hasattr(self, "_run_task") and not self._run_task.done():
            self._run_task.cancel()
        if self._bridge is not None:
            self._bridge.finalize()

    def action_clear_screen(self) -> None:
        self.query_one("#conversation", ConversationView).clear()
        self.query_one("#toollog", ToolLog).clear()

    def on_input_changed(self, event: Input.Changed) -> None:
        if self._streaming:
            return
        value = event.value.strip()
        if value.startswith("/"):
            matches = [f"{cmd}  {desc}" for cmd, desc in SLASH_COMMANDS.items()
                       if cmd.startswith(value.split()[0])]
            hint = "  ".join(matches) if matches else "Commands: /quit, /exit, /clear"
            self.query_one("#thinking", Label).update(f"  {hint}")
            self.query_one("#thinking", Label).add_class("hint-visible")
        else:
            self.query_one("#thinking", Label).update("")
            self.query_one("#thinking", Label).remove_class("hint-visible")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        prompt = event.value.strip()
        event.input.clear()
        self.query_one("#thinking", Label).update("")
        if not prompt:
            return
        if prompt == "/clear":
            self.action_clear_screen()
            return
        if prompt in ("/quit", "/exit"):
            self.exit()
            return
        self._submit_prompt(prompt)

    def _submit_prompt(self, prompt: str) -> None:
        if self._streaming:
            return
        conv = self.query_one("#conversation", ConversationView)
        inp = self.query_one("#input-area", InputArea)

        inp.append_to_history(prompt)

        conv.add_user_message(prompt)
        conv.start_assistant_message()

        self._show_thinking()

        inp.disabled = True
        self._streaming = True

        self._run_task = asyncio.create_task(self._run_and_finish(prompt))

    async def _run_and_finish(self, prompt: str) -> None:
        try:
            assert self._bridge is not None
            char_writer = asyncio.create_task(self._char_writer())
            await self._bridge.run_prompt(prompt)
            self._text_queue.put_nowait(None)
            await char_writer
        except Exception as exc:
            conv = self.query_one("#conversation", ConversationView)
            conv.write(f"\n[red]Error: {exc}[/red]")
        finally:
            self._stop_thinking()
            self._streaming = False
            inp = self.query_one("#input-area", InputArea)
            inp.disabled = False
            inp.focus()

    async def _char_writer(self) -> None:
        conv = self.query_one("#conversation", ConversationView)
        while True:
            chunk = await self._text_queue.get()
            if chunk is None:
                return
            for char in chunk:
                conv.append_streaming_text(char)
                await asyncio.sleep(CHAR_SPEED)

    def on_streaming_text(self, text: str) -> None:
        self._stop_thinking()
        self._text_queue.put_nowait(text)

    def on_tool_call(self, name: str, inputs: dict) -> None:
        tool_log = self.query_one("#toollog", ToolLog)
        tool_log.add_tool_call(name, inputs)

    def _show_thinking(self) -> None:
        self._thinking_frame = 0
        label = self.query_one("#thinking", Label)
        label.update(THINKING_FRAMES[0])
        self._thinking_timer = self.set_interval(
            0.5, self._toggle_thinking
        )

    def _toggle_thinking(self) -> None:
        self._thinking_frame = (self._thinking_frame + 1) % len(THINKING_FRAMES)
        label = self.query_one("#thinking", Label)
        label.update(THINKING_FRAMES[self._thinking_frame])

    def _stop_thinking(self) -> None:
        if self._thinking_timer is not None:
            self._thinking_timer.stop()
            self._thinking_timer = None
        try:
            self.query_one("#thinking", Label).update("")
        except Exception:
            pass


def run_tui(
    service: AgentService,
    session_id: str,
    prompt: str | None = None,
) -> None:
    """Entry point called from CLI main()."""
    app = AgentTuiApp(service, session_id, initial_prompt=prompt)
    try:
        app.run()
    finally:
        service.stop()
