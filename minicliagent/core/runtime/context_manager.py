from __future__ import annotations

import json
from copy import deepcopy


class ContextManager:
    def __init__(
        self,
        tool_result_keep_count: int = 3,
        tool_result_max_chars: int = 2000,
        text_message_max_chars: int = 4000,
        history_max_messages: int | None = None,
    ) -> None:
        self.tool_result_keep_count = tool_result_keep_count
        self.tool_result_max_chars = tool_result_max_chars
        self.text_message_max_chars = text_message_max_chars
        self.history_max_messages = history_max_messages

    def prepare_messages(self, messages: list[dict], working_memory: dict | None = None) -> list[dict]:
        prepared = deepcopy(messages)
        tool_result_indices: list[int] = []

        for index, message in enumerate(prepared):
            content = message.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "tool_result":
                        tool_result_indices.append(index)
                        break
            elif isinstance(content, str) and len(content) > self.text_message_max_chars:
                message["content"] = f"{content[:self.text_message_max_chars]}..."

        keep_from = max(0, len(tool_result_indices) - self.tool_result_keep_count)
        compact_indices = set(tool_result_indices[:keep_from])

        for index in compact_indices:
            for part in prepared[index]["content"]:
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    text = str(part.get("content", ""))
                    if len(text) > self.tool_result_max_chars:
                        part["content"] = f"[compact] {text[:self.tool_result_max_chars]}..."

        if self.history_max_messages is not None and len(prepared) > self.history_max_messages:
            overflow = len(prepared) - self.history_max_messages
            prepared = [
                {
                    "role": "user",
                    "content": f"<history-summary>History compacted: {overflow} earlier message(s) summarized.</history-summary>",
                }
            ] + prepared[-self.history_max_messages :]

        return prepared

    @staticmethod
    def render_working_memory(working_memory: dict | None) -> str:
        if not working_memory:
            return ""
        return f"Working memory: {json.dumps(working_memory, ensure_ascii=False)}"
