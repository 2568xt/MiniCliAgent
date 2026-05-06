from __future__ import annotations

from pathlib import Path

from minicliagent.app.agent_service import create_agent_service


class DummyProvider:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def create_response(self, request):
        self.calls.append(request)
        return type("R", (), {"stop_reason": "end_turn", "text": "ack", "tool_calls": []})()


class DatasetSummarizer:
    def summarize(self, session_id: str, messages: list[dict], source: str) -> list[str]:
        combined = " ".join(str(message.get("content", "")) for message in messages)
        if session_id == "alice":
            return [
                "User goes by Alice and prefers markdown-first notes.",
                "User likes concise answers and plans the week on Monday.",
            ]
        if session_id == "bob":
            return [
                "User Bob prefers short bullet lists and uses macOS.",
                "User avoids emojis in technical discussions.",
            ]
        if session_id == "carol":
            return [
                "User Carol works with Python and likes reproducible test cases.",
                f"Session content mentions: {combined[:80]}",
            ]
        return ["User has no special memory preferences."]


def test_memory_evaluation_across_multiple_sessions(tmp_path: Path) -> None:
    env = {
        "MINICLIAGENT_WORKSPACE": str(tmp_path),
        "MINICLIAGENT_MEMORY_ENABLED": "1",
    }
    service = create_agent_service(env=env)
    service.runtime.provider = DummyProvider()
    assert service.memory_service is not None
    service.memory_service.summarizer = DatasetSummarizer()

    sessions = {
        "alice": "Please remember that I prefer markdown-first notes and Monday planning.",
        "bob": "Remember that I like short bullet lists and I use macOS.",
        "carol": "Remember that I work with Python and want reproducible test cases.",
    }

    for session_id, prompt in sessions.items():
        service.run_prompt(prompt, session_id=session_id)
        service.finalize_session(session_id)

    queries = {
        "alice": ["markdown-first notes", "concise answers"],
        "bob": ["short bullet lists", "technical discussions"],
        "carol": ["Python", "reproducible test cases"],
    }

    for session_id, terms in queries.items():
        for term in terms:
            results = service.memory_service.search(term)
            assert results, f"expected hits for {session_id} query {term!r}"
            assert any(
                term.lower() in result.content.lower()
                or term.lower() in ((result.metadata or {}).get("session_id", "")).lower()
                for result in results
            )

    memory_summary = tmp_path / ".minicliagent" / "memory.md"
    fragments_dir = tmp_path / ".minicliagent" / "memory"
    assert memory_summary.exists()
    assert len(list(fragments_dir.glob("*.md"))) == len(sessions)
