import json
from pathlib import Path

from minicliagent.core.memory.service import MemoryService
from minicliagent.core.memory.store import MarkdownMemoryStore
from minicliagent.core.tools.builtins.memory import memory_search_tool


class EmptyDenseIndex:
    def search(self, query: str, top_k: int):
        return []

    def add_documents(self, documents):
        return None


def test_memory_search_tool_returns_structured_results(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(
        summary_path=tmp_path / ".minicliagent" / "memory.md",
        fragments_dir=tmp_path / ".minicliagent" / "memory",
    )
    store.append_entries(
        session_id="s1",
        source="exit_hook",
        entries=["User prefers hybrid memory retrieval."],
        created_at="2026-05-04T01:02:03",
    )
    service = MemoryService(
        store=store,
        dense_index=EmptyDenseIndex(),
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
    )

    result = memory_search_tool(service, "hybrid memory")

    assert result.is_error is False
    payload = json.loads(result.content)
    assert payload["query"] == "hybrid memory"
    assert payload["diagnostics"]["final_hits"] >= 0
    assert payload["results"]
    assert any("hybrid memory retrieval" in item["content"] for item in payload["results"])
    assert "normalized_bm25" in payload["results"][0]


def test_memory_search_tool_handles_empty_results(tmp_path: Path) -> None:
    service = MemoryService(
        store=MarkdownMemoryStore(
            summary_path=tmp_path / ".minicliagent" / "memory.md",
            fragments_dir=tmp_path / ".minicliagent" / "memory",
        ),
        dense_index=EmptyDenseIndex(),
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
    )

    result = memory_search_tool(service, "missing")

    payload = json.loads(result.content)
    assert payload["query"] == "missing"
    assert payload["results"] == []
    assert payload["diagnostics"]["final_hits"] == 0
