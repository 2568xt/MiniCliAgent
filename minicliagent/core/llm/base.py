from __future__ import annotations

from typing import Protocol

from minicliagent.core.llm.types import ModelRequest, ModelResponse, TextDeltaCallback


class LLMProvider(Protocol):
    def create_response(
        self,
        request: ModelRequest,
        on_text_delta: TextDeltaCallback | None = None,
    ) -> ModelResponse:
        ...
