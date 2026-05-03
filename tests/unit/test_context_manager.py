from minicliagent.core.runtime.context_manager import ContextManager


def test_context_manager_microcompacts_old_tool_results() -> None:
    manager = ContextManager(tool_result_keep_count=1, tool_result_max_chars=20)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool-1",
                    "content": "abcdefghijklmnopqrstuvwxyz",
                    "is_error": False,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool-2",
                    "content": "1234567890",
                    "is_error": False,
                }
            ],
        },
    ]

    compacted = manager.prepare_messages(messages)

    older = compacted[0]["content"][0]["content"]
    newer = compacted[1]["content"][0]["content"]
    assert older.startswith("[compact]")
    assert newer == "1234567890"


def test_context_manager_trims_long_text_messages() -> None:
    manager = ContextManager(
        tool_result_keep_count=1,
        tool_result_max_chars=20,
        text_message_max_chars=10,
    )
    messages = [
        {"role": "user", "content": "abcdefghijklmnopqrstuvwxyz"},
    ]

    compacted = manager.prepare_messages(messages)

    assert compacted[0]["content"] == "abcdefghij..."


def test_context_manager_preserves_last_summary_message_when_compacting_history() -> None:
    manager = ContextManager(
        tool_result_keep_count=1,
        tool_result_max_chars=10,
        text_message_max_chars=10,
        history_max_messages=3,
    )
    messages = [
        {"role": "user", "content": "first-message"},
        {"role": "assistant", "content": "second-message"},
        {"role": "user", "content": "third-message"},
        {"role": "assistant", "content": "fourth-message"},
        {"role": "user", "content": "fifth-message"},
    ]

    compacted = manager.prepare_messages(messages)

    assert len(compacted) == 4
    assert compacted[0]["role"] == "user"
    assert "History compacted" in compacted[0]["content"]


def test_context_manager_renders_working_memory_summary() -> None:
    summary = ContextManager.render_working_memory(
        {
            "loaded_skills": ["demo"],
            "active_task": 1,
            "pending_request_ids": ["req-1"],
        }
    )

    assert "loaded_skills" in summary
