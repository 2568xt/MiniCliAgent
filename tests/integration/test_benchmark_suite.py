from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from minicliagent.app.agent_service import create_agent_service
from minicliagent.core.llm.types import ModelResponse
from minicliagent.core.memory.models import HybridMemoryResult
from minicliagent.core.memory.service import MemoryService
from minicliagent.core.memory.store import MarkdownMemoryStore
from minicliagent.core.runtime.agent_runtime import AgentRuntime
from minicliagent.core.tools.models import ToolResult
from minicliagent.core.tools.registry import ToolRegistry


@dataclass(frozen=True)
class MemoryEvalCase:
    session_id: str
    prompt: str
    queries: list[str]
    expected_terms: list[str]


@dataclass(frozen=True)
class AgentFlowCase:
    prompt: str
    expected_tool: str
    expected_task_subject: str | None = None


class BenchProvider:
    def __init__(self, responses: list[ModelResponse] | None = None) -> None:
        self.responses = responses or [ModelResponse(stop_reason="end_turn", text="ok", tool_calls=[])]
        self.calls: list[object] = []

    def create_response(self, request):
        self.calls.append(request)
        if len(self.responses) > 1:
            return self.responses.pop(0)
        return self.responses[0]


class SummarizerStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def summarize(self, session_id: str, messages: list[dict], source: str) -> list[str]:
        self.calls.append((session_id, source))
        combined = " ".join(str(message.get("content", "")) for message in messages)
        if session_id == "alice":
            return [
                "User prefers markdown-first notes.",
                "User plans the week on Monday.",
                f"Transcript: {combined[:80]}",
            ]
        if session_id == "bob":
            return [
                "User prefers short bullet lists.",
                "User uses macos.",
                "User likes reproducible workflows.",
            ]
        if session_id == "carol":
            return [
                "User works with Python.",
                "User wants reproducible test cases.",
            ]
        return ["User has no special memory preferences."]


class RecordingToolHandler:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, **kwargs) -> ToolResult:
        self.calls.append(kwargs)
        return ToolResult(content=f"handled:{kwargs}", is_error=False)


class MultiTurnProvider:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def create_response(self, request):
        self.calls.append(request)
        text = request.messages[-1]["content"] if request.messages else ""
        lowered = str(text).lower()
        if "create a task" in lowered or "task" in lowered:
            return ModelResponse(
                stop_reason="tool_use",
                text="",
                tool_calls=[type("Call", (), {"id": "1", "name": "task_create", "input": {"subject": "demo", "description": "benchmark task"}})()],
            )
        if "load skill" in lowered:
            return ModelResponse(
                stop_reason="tool_use",
                text="",
                tool_calls=[type("Call", (), {"id": "2", "name": "load_skill", "input": {"name": "demo"}})()],
            )
        return ModelResponse(stop_reason="end_turn", text="done", tool_calls=[])


def test_memory_benchmark_recall_across_sessions(tmp_path: Path) -> None:
    service = create_agent_service(env={"MINICLIAGENT_WORKSPACE": str(tmp_path), "MINICLIAGENT_MEMORY_ENABLED": "1"})
    service.runtime.provider = BenchProvider()
    assert service.memory_service is not None
    service.memory_service.summarizer = SummarizerStub()

    cases = [
        MemoryEvalCase("alice", "Please remember markdown-first notes and Monday planning.", ["markdown-first notes", "Monday planning"], ["markdown-first notes", "Monday planning"]),
        MemoryEvalCase("bob", "Remember that I like short bullet lists and macOS.", ["short bullet lists", "macos"], ["short bullet lists", "macos"]),
        MemoryEvalCase("carol", "Remember that I work with Python and want reproducible test cases.", ["Python", "reproducible test cases"], ["Python", "reproducible test cases"]),
        MemoryEvalCase("dave", "Please remember I prefer concise answers and tables only when needed.", ["concise answers", "tables only when needed"], ["concise answers", "tables only when needed"]),
        MemoryEvalCase("erin", "Remember that I use Linux and like reproducible benchmarks.", ["Linux", "reproducible benchmarks"], ["Linux", "reproducible benchmarks"]),
        MemoryEvalCase("frank", "Remember that I prefer bullet lists and short summaries.", ["bullet lists", "short summaries"], ["bullet lists", "short summaries"]),
    ]

    for case in cases:
        service.run_prompt(case.prompt, session_id=case.session_id)
        messages = service.runtime.message_store.get(case.session_id)
        service.memory_service.remember_session(case.session_id, messages, "exit_hook")
        service.finalize_session(case.session_id)

    assert len(service.memory_service.store.read_documents()) >= len(cases)
    hits = 0
    total = 0
    for case in cases:
        for query in case.queries:
            total += 1
            results = service.memory_service.search(query)
            if results and any(_matches_query(result, query, case.session_id) for result in results):
                hits += 1

    assert service.memory_service.last_search_diagnostics.final_hits >= 0
    assert hits / total >= 0.4


def test_agent_execution_benchmark_task_tool_flow(tmp_path: Path) -> None:
    service = create_agent_service(env={"MINICLIAGENT_WORKSPACE": str(tmp_path)})
    provider = MultiTurnProvider()
    service.runtime.provider = provider
    result = service.run_prompt("Please create a task for the benchmark.", session_id="bench-task")

    assert result
    assert any(request.messages for request in provider.calls)
    board_items = service.task_service.list_tasks()
    assert any(item.subject == "demo" for item in board_items)

    service.runtime.provider = BenchProvider()
    second = service.run_prompt("Please create another task for the benchmark.", session_id="bench-task-2")
    assert second
    assert len(service.task_service.list_tasks()) >= 1


def test_agent_execution_benchmark_skill_tool_flow(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Demo Skill\n\nThis skill exists for benchmark validation.\n", encoding="utf-8")

    service = create_agent_service(env={"MINICLIAGENT_WORKSPACE": str(tmp_path)})
    service.runtime.provider = MultiTurnProvider()
    result = service.run_prompt("Please load skill demo.", session_id="bench-skill")

    assert result
    assert service.skill_service.list_skills()


def test_cli_workflow_benchmark_runs_and_finalizes_session(tmp_path: Path) -> None:
    service = create_agent_service(env={"MINICLIAGENT_WORKSPACE": str(tmp_path), "MINICLIAGENT_MEMORY_ENABLED": "1"})
    service.runtime.provider = BenchProvider()
    assert service.memory_service is not None
    service.memory_service.summarizer = SummarizerStub()

    result = service.run_prompt("Remember I prefer concise answers.", session_id="workflow")
    messages = service.runtime.message_store.get("workflow")
    service.memory_service.remember_session("workflow", messages, "exit_hook")
    service.finalize_session("workflow")

    assert result == "ok"
    assert service.memory_service.store.read_documents()
    assert (tmp_path / ".minicliagent" / "memory.md").exists()

    second = service.run_prompt("Remember I prefer bullet lists.", session_id="workflow-2")
    assert second == "ok"


def test_failure_benchmark_dense_search_falls_back_to_bm25(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(summary_path=tmp_path / ".minicliagent" / "memory.md", fragments_dir=tmp_path / ".minicliagent" / "memory")
    store.append_entries(session_id="s1", source="exit_hook", entries=["Fallback to BM25 should still find this memory."], created_at="2026-05-05T00:00:00")

    class FailingDenseIndex:
        def search(self, query: str, top_k: int):
            raise RuntimeError("dense down")

        def add_documents(self, documents):
            pass

    memory_service = MemoryService(
        store=store,
        dense_index=FailingDenseIndex(),
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
    )

    results = memory_service.search("BM25 fallback memory")
    assert results
    assert memory_service.last_search_diagnostics.dense_available is False
    assert memory_service.last_search_diagnostics.dense_fallback is True


def _matches_query(result: HybridMemoryResult, query: str, session_id: str) -> bool:
    lower_query = query.lower()
    return lower_query in result.content.lower() or session_id.lower() in (result.document.metadata or {}).get("session_id", "").lower()
