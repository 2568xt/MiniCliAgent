"""Temporary test to verify memory_get_tool implementation."""
import json
from pathlib import Path
import tempfile
from minicliagent.core.memory.service import MemoryService
from minicliagent.core.memory.store import MarkdownMemoryStore
from minicliagent.core.tools.builtins.memory import memory_get_tool, memory_search_tool

class EmptyDenseIndex:
    def search(self, query: str, top_k: int):
        return []
    def add_documents(self, documents):
        return None

def test_memory_get_tool_returns_document(tmp_path: Path) -> None:
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
    
    docs = store.read_documents()
    assert len(docs) > 0, "Expected at least one document"
    
    result = memory_get_tool(service, docs[0].source_id)
    assert result.is_error is False, f"Expected success, got: {result.content}"
    payload = json.loads(result.content)
    assert "source_id" in payload
    assert "content" in payload
    assert "metadata" in payload
    print(f"memory_get_tool with valid id: OK (source_id={payload['source_id']})")

def test_memory_get_tool_handles_missing_document(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(
        summary_path=tmp_path / ".minicliagent" / "memory.md",
        fragments_dir=tmp_path / ".minicliagent" / "memory",
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
    
    result = memory_get_tool(service, "nonexistent.md")
    assert result.is_error is True, f"Expected error, got: {result.content}"
    payload = json.loads(result.content)
    assert "error" in payload, f"Expected error field in payload: {payload}"
    print(f"memory_get_tool with invalid id: OK (error returned correctly)")

if __name__ == "__main__":
    import sys
    with tempfile.TemporaryDirectory() as tmpdir:
        test_memory_get_tool_returns_document(Path(tmpdir))
        test_memory_get_tool_handles_missing_document(Path(tmpdir))
    print("All memory_get_tool tests passed!")