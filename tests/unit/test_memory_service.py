from pathlib import Path

from minicliagent.core.llm.types import ModelRequest, ModelResponse
from minicliagent.core.memory.models import MemoryDocument, MemorySearchHit
from minicliagent.core.memory.service import (
    LocalMemorySummarizer,
    MemoryService,
    ProviderMemorySummarizer,
)
from minicliagent.core.memory.store import MarkdownMemoryStore


class FakeDenseIndex:
    def __init__(self, hits: list[MemorySearchHit] | None = None, fail: bool = False) -> None:
        self.hits = hits or []
        self.fail = fail
        self.added_documents: list[MemoryDocument] = []

    def search(self, query: str, top_k: int) -> list[MemorySearchHit]:
        if self.fail:
            raise RuntimeError("dense unavailable")
        return self.hits[:top_k]

    def add_documents(self, documents: list[MemoryDocument]) -> None:
        self.added_documents.extend(documents)


class FakeSummarizer:
    def __init__(self, entries: list[str]) -> None:
        self.entries = entries
        self.calls: list[tuple[str, str]] = []

    def summarize(self, session_id: str, messages: list[dict], source: str) -> list[str]:
        self.calls.append((session_id, source))
        return self.entries


class FakeLogger:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    def log(self, level: str, message: str, **extra) -> None:
        self.calls.append((level, message, extra))


def test_memory_service_search_combines_dense_and_bm25(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.append_entries(
        session_id="s1",
        source="exit_hook",
        entries=["User prefers Markdown-first memory."],
        created_at="2026-05-04T01:02:03",
    )
    dense_doc = MemoryDocument(
        source_id="dense.md",
        source="fragment",
        content="Dense hit about semantic memory.",
    )
    service = MemoryService(
        store=store,
        dense_index=FakeDenseIndex([MemorySearchHit(dense_doc, 0.9, "dense")]),
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
    )

    results = service.search("markdown memory")

    assert results
    assert "dense.md" in {result.source_id for result in results}
    assert any("Markdown-first memory" in result.content for result in results)
    assert results[0].score >= results[-1].score


def test_memory_service_degrades_to_bm25_when_dense_fails(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.append_entries(
        session_id="s1",
        source="exit_hook",
        entries=["Use BM25 when dense search is unavailable."],
        created_at="2026-05-04T01:02:03",
    )
    service = MemoryService(
        store=store,
        dense_index=FakeDenseIndex(fail=True),
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
        logger=FakeLogger(),
    )

    results = service.search("BM25 dense unavailable")

    assert [result.source_id for result in results]
    assert all(result.dense_score == 0 for result in results)


def test_memory_service_remember_session_uses_summarizer_and_indexes_documents(tmp_path: Path) -> None:
    dense = FakeDenseIndex()
    summarizer = FakeSummarizer(["User wants automatic memory append."])
    logger = FakeLogger()
    service = MemoryService(
        store=_store(tmp_path),
        dense_index=dense,
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
        summarizer=summarizer,
        logger=logger,
    )

    result = service.remember_session("s1", [{"role": "user", "content": "hello"}], "exit_hook")

    assert result.written is True
    assert summarizer.calls == [("s1", "exit_hook")]
    assert dense.added_documents
    assert "automatic memory append" in dense.added_documents[0].content


def test_memory_service_skips_empty_summaries(tmp_path: Path) -> None:
    logger = FakeLogger()
    service = MemoryService(
        store=_store(tmp_path),
        dense_index=FakeDenseIndex(),
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
        summarizer=FakeSummarizer([]),
        logger=logger,
    )

    result = service.remember_session("s1", [{"role": "user", "content": "hello"}], "exit_hook")

    assert result.written is False
    assert any(call[1] == "memory_summary_not_written" for call in logger.calls)


def test_memory_service_records_search_diagnostics(tmp_path: Path) -> None:
    logger = FakeLogger()
    service = MemoryService(
        store=_store(tmp_path),
        dense_index=FakeDenseIndex(fail=True),
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
        logger=logger,
    )

    service.search("missing")

    assert service.last_search_diagnostics.dense_available is False
    assert service.last_search_diagnostics.dense_fallback is True
    assert service.last_search_diagnostics.final_hits == 0
    assert any(call[1] == "memory_dense_search_failed" for call in logger.calls)
    assert any(call[1] == "memory_search_completed" for call in logger.calls)


class FailingProvider:
    def create_response(self, request: ModelRequest) -> ModelResponse:
        raise RuntimeError("provider unavailable")


class ProviderReturningNoMemory:
    def create_response(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(stop_reason="end_turn", text="NO_MEMORY", tool_calls=[])


class ProviderReturningMemory:
    def create_response(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(stop_reason="end_turn", text="- User prefers short commit messages.\n- Project uses uv for dependency management.", tool_calls=[])


def test_provider_summarizer_falls_back_to_local_on_error() -> None:
    summarizer = ProviderMemorySummarizer(provider=FailingProvider(), logger=FakeLogger())
    messages = [{"role": "user", "content": "I prefer short commit messages."}]
    entries = summarizer.summarize("s1", messages, "exit_hook")
    assert len(entries) >= 1


def test_provider_summarizer_falls_back_on_no_memory_response() -> None:
    summarizer = ProviderMemorySummarizer(provider=ProviderReturningNoMemory())
    messages = [{"role": "user", "content": "I prefer short commit messages and important decisions."}]
    entries = summarizer.summarize("s1", messages, "exit_hook")
    # Falls back to LocalMemorySummarizer when provider returns NO_MEMORY
    assert len(entries) >= 1


def test_provider_summarizer_returns_provider_entries_when_available() -> None:
    summarizer = ProviderMemorySummarizer(provider=ProviderReturningMemory())
    messages = [{"role": "user", "content": "hello"}]
    entries = summarizer.summarize("s1", messages, "exit_hook")
    assert "User prefers short commit messages." in entries


def test_local_summarizer_extracts_preference_lines() -> None:
    summarizer = LocalMemorySummarizer()
    messages = [
        {"role": "user", "content": "I prefer markdown for all notes."},
        {"role": "assistant", "content": "Noted."},
        {"role": "user", "content": "We should use pytest for all tests."},
    ]
    entries = summarizer.summarize("s1", messages, "exit_hook")
    assert any("markdown" in e.lower() for e in entries)


def test_memory_search_diagnostics_includes_retriever_info(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.append_entries(session_id="s1", source="exit_hook", entries=["Test entry."], created_at="2026-05-04T01:02:03")
    service = MemoryService(
        store=store,
        dense_index=FakeDenseIndex([MemorySearchHit(MemoryDocument(source_id="d", source="f", content="c"), 0.9, "dense")]),
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
    )
    service.search("test")
    diag = service.last_search_diagnostics
    assert "dense" in diag.retriever
    assert diag.fallback_reason is None


def test_memory_search_diagnostics_records_fallback_reason(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.append_entries(session_id="s1", source="exit_hook", entries=["Test."], created_at="2026-05-04T01:02:03")
    service = MemoryService(
        store=store,
        dense_index=FakeDenseIndex(fail=True),
        dense_weight=0.7,
        bm25_weight=0.3,
        dense_top_k=4,
        bm25_top_k=4,
        final_top_k=6,
    )
    service.search("test")
    diag = service.last_search_diagnostics
    assert diag.dense_fallback is True
    assert diag.fallback_reason is not None
    assert "dense unavailable" in diag.fallback_reason


def _store(tmp_path: Path) -> MarkdownMemoryStore:
    return MarkdownMemoryStore(
        summary_path=tmp_path / ".minicliagent" / "memory.md",
        fragments_dir=tmp_path / ".minicliagent" / "memory",
    )
