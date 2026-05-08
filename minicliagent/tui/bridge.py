from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from minicliagent.app.agent_service import AgentService
    from minicliagent.tui.app import AgentTuiApp


class TuiBridge:
    """Bridges synchronous AgentService calls with the async Textual UI.

    All LLM work runs in a thread-pool thread via asyncio.to_thread().
    UI updates are posted back via app.call_from_thread().
    """

    def __init__(self, app: AgentTuiApp, service: AgentService, session_id: str) -> None:
        self._app = app
        self._service = service
        self._session_id = session_id

    async def run_prompt(self, prompt: str) -> None:
        def _on_text(text: str) -> None:
            if text:
                self._app.call_from_thread(self._app.on_streaming_text, text)

        def _on_tool(name: str, inputs: dict) -> None:
            self._app.call_from_thread(self._app.on_tool_call, name, inputs)

        await asyncio.to_thread(
            self._service.run_prompt,
            prompt,
            session_id=self._session_id,
            on_text_delta=_on_text,
            on_tool_call=_on_tool,
        )

    def finalize(self) -> None:
        self._service.finalize_session(self._session_id)
