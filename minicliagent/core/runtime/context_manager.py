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
        self.last_history_overflow_count = 0

    def prepare_messages(self, messages: list[dict], working_memory: dict | None = None) -> list[dict]:
        prepared = deepcopy(messages)
        tool_result_indices: list[int] = []
        self.last_history_overflow_count = 0

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
            self.last_history_overflow_count = overflow

            # Extract tool calls from the overflow section
            tool_summary_parts = []
            for msg in prepared[:-self.history_max_messages]:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            if part.get("type") == "tool_use":
                                tool_name = part.get("name", "unknown")
                                # Get a brief description of the tool call
                                args = part.get("input", {})
                                if isinstance(args, dict):
                                    # Try to extract meaningful info
                                    arg_parts = []
                                    for k, v in args.items():
                                        v_str = str(v)
                                        if len(v_str) > 50:
                                            v_str = v_str[:50] + "..."
                                        arg_parts.append(f"{k}: {v_str}")
                                    args_str = ", ".join(arg_parts) if arg_parts else "{}"
                                else:
                                    args_str = str(args)
                                tool_summary_parts.append(f"[tool: {tool_name}, args: {args_str}]")
                elif role == "assistant" and content:
                    # Text response from assistant
                    if len(content) > 100:
                        content = content[:100] + "..."
                    tool_summary_parts.append(f"[response: {content}]")

            # Build structured summary
            tool_count = len(tool_summary_parts)
            if tool_summary_parts:
                tools_str = ", ".join(tool_summary_parts)
                summary_content = (
                    f"<history-summary>Truncated {overflow} message(s). "
                    f"Tool calls made in this session ({tool_count}): {tools_str}</history-summary>"
                )
            else:
                summary_content = (
                    f"<history-summary>Truncated {overflow} message(s). "
                    f"No tool calls in truncated section.</history-summary>"
                )

            prepared = [
                {"role": "user", "content": summary_content}
            ] + prepared[-self.history_max_messages :]

        return prepared

    @staticmethod
    def render_working_memory(working_memory: dict | None) -> str:
        if not working_memory:
            return ""
        return f"Working memory: {json.dumps(working_memory, ensure_ascii=False)}"
