from __future__ import annotations

import inspect
import json
from dataclasses import dataclass

from minicliagent.core.llm.tool_adapter import tool_specs_to_anthropic
from minicliagent.core.llm.types import ModelRequest, TextDeltaCallback, ToolCallCallback
from minicliagent.core.runtime.background_manager import BackgroundManager
from minicliagent.core.runtime.context_manager import ContextManager
from minicliagent.core.runtime.event_bus import EventBus
from minicliagent.core.runtime.message_store import InMemoryMessageStore
from minicliagent.core.tools.registry import ToolRegistry
from minicliagent.infra.logging.setup import JsonLogger, TranscriptRecorder


@dataclass
class RuntimeTurnResult:
    output_text: str
    messages: list[dict]


class AgentRuntime:
    def __init__(
        self,
        provider,
        tool_registry: ToolRegistry,
        system_prompt: str,
        message_store=None,
        context_manager: ContextManager | None = None,
        background_manager: BackgroundManager | None = None,
        event_bus: EventBus | None = None,
        logger: JsonLogger | None = None,
        transcript_recorder: TranscriptRecorder | None = None,
        memory_service=None,
    ) -> None:
        self.provider = provider
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.message_store = message_store or InMemoryMessageStore()
        self.context_manager = context_manager or ContextManager()
        self.background_manager = background_manager
        self.event_bus = event_bus
        self.logger = logger
        self.transcript_recorder = transcript_recorder
        self.memory_service = memory_service
        self.loaded_skills: dict[str, list[str]] = {}
        self.session_state: dict[str, dict] = {}
        self._memory_compact_overflows: dict[str, int] = {}

    def run_turn(
        self,
        session_id: str,
        user_input: str | None = None,
        on_text_delta: TextDeltaCallback | None = None,
        on_tool_call: ToolCallCallback | None = None,
    ) -> RuntimeTurnResult:
        messages = self.message_store.get(session_id)
        if user_input:
            self.message_store.append(session_id, {"role": "user", "content": user_input})
            messages = self.message_store.get(session_id)

        while True:
            if self.background_manager is not None:
                notifications = self.background_manager.drain_notifications()
                if notifications:
                    notification_text = "\n".join(
                        f"[bg:{item['task_id']}] {item['status']}: {item['result']}"
                        for item in notifications
                    )
                    self.message_store.append(
                        session_id,
                        {
                            "role": "user",
                            "content": f"<background-results>\n{notification_text}\n</background-results>",
                        },
                    )
                    messages = self.message_store.get(session_id)

            working_memory = self.session_state.get(session_id, {})
            if session_id in self.loaded_skills:
                working_memory = dict(working_memory)
                working_memory["loaded_skills"] = self.loaded_skills[session_id]
            prepared_messages = self.context_manager.prepare_messages(messages, working_memory=working_memory)
            self._maybe_record_compacted_memory(session_id, messages)
            response = _invoke_provider(
                self.provider,
                ModelRequest(
                    system=_build_system_prompt(
                        self.system_prompt,
                        working_memory,
                        memory_enabled=self.memory_service is not None,
                    ),
                    messages=prepared_messages,
                    tools=tool_specs_to_anthropic(self.tool_registry.list_specs()),
                    max_tokens=4096,
                ),
                on_text_delta=on_text_delta,
            )
            assistant_message = _assistant_message_from_response(response)
            self.message_store.append(session_id, assistant_message)
            messages = self.message_store.get(session_id)
            if self.transcript_recorder is not None:
                self.transcript_recorder.record(session_id, messages)
            if response.stop_reason != "tool_use":
                return RuntimeTurnResult(output_text=response.text, messages=list(messages))

            for call in response.tool_calls:
                if on_tool_call is not None:
                    on_tool_call(call.name, call.input)
                if self.event_bus is not None:
                    self.event_bus.emit("tool_call", {"name": call.name, "session_id": session_id})
                if self.logger is not None:
                    self.logger.log("info", "tool_call", tool=call.name, session_id=session_id)
                result = self.tool_registry.execute(call.name, call.input)
                if call.name == "load_skill" and not result.is_error:
                    self.loaded_skills.setdefault(session_id, []).append(call.input["name"])
                self.message_store.append(
                    session_id,
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": call.id,
                                "content": result.content,
                                "is_error": result.is_error,
                            }
                        ],
                    },
                )
                messages = self.message_store.get(session_id)
                if self.transcript_recorder is not None:
                    self.transcript_recorder.record(session_id, messages)

    def _maybe_record_compacted_memory(self, session_id: str, messages: list[dict]) -> None:
        if self.memory_service is None:
            return
        overflow_count = getattr(self.context_manager, "last_history_overflow_count", 0)
        if overflow_count <= 0:
            return
        if self._memory_compact_overflows.get(session_id) == overflow_count:
            return
        self._memory_compact_overflows[session_id] = overflow_count
        try:
            self.memory_service.remember_session(session_id, list(messages), "compact_hook")
        except Exception:
            if self.logger is not None:
                self.logger.log("warning", "memory_compact_hook_failed", session_id=session_id)


def _assistant_message_from_response(response) -> dict:
    if response.stop_reason != "tool_use":
        return {"role": "assistant", "content": response.text}

    content: list[dict] = []
    if response.text:
        content.append({"type": "text", "text": response.text})
    for call in response.tool_calls:
        content.append(
            {
                "type": "tool_use",
                "id": call.id,
                "name": call.name,
                "input": call.input,
            }
        )
    return {"role": "assistant", "content": content}


def _build_system_prompt(base_prompt: str, working_memory: dict | None, memory_enabled: bool = False) -> str:
    parts = [base_prompt]
    if memory_enabled:
        parts.append("When cross-session facts, user preferences, or project decisions may help, call memory_search.")
    if working_memory:
        parts.append(f"Working memory: {json.dumps(working_memory, ensure_ascii=False)}")
    return "\n\n".join(parts)


def _invoke_provider(provider, request: ModelRequest, on_text_delta: TextDeltaCallback | None) -> object:
    create_response = provider.create_response
    if on_text_delta is None:
        return create_response(request)

    try:
        signature = inspect.signature(create_response)
    except (TypeError, ValueError):
        signature = None

    if signature is not None and "on_text_delta" not in signature.parameters:
        response = create_response(request)
        if response.text:
            on_text_delta(response.text)
        return response

    return create_response(request, on_text_delta=on_text_delta)
