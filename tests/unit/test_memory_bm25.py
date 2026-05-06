from minicliagent.core.memory.bm25 import BM25MemorySearcher
from minicliagent.core.memory.models import MemoryDocument


def test_bm25_searcher_returns_exact_token_hits_first() -> None:
    searcher = BM25MemorySearcher(
        [
            MemoryDocument(
                source_id="a.md",
                source="fragment",
                content="User prefers markdown memory and local storage.",
            ),
            MemoryDocument(
                source_id="b.md",
                source="fragment",
                content="Worktree tasks use git branches.",
            ),
        ]
    )

    results = searcher.search("markdown memory", top_k=2)

    assert [result.source_id for result in results] == ["a.md"]
    assert results[0].score > 0
    assert results[0].content.startswith("User prefers")


def test_bm25_searcher_handles_empty_corpus() -> None:
    searcher = BM25MemorySearcher([])

    assert searcher.search("anything", top_k=4) == []


def test_bm25_searcher_respects_top_k() -> None:
    searcher = BM25MemorySearcher(
        [
            MemoryDocument(source_id="a.md", source="fragment", content="memory alpha"),
            MemoryDocument(source_id="b.md", source="fragment", content="memory beta"),
            MemoryDocument(source_id="c.md", source="fragment", content="memory gamma"),
        ]
    )

    results = searcher.search("memory", top_k=2)

    assert len(results) == 2
    assert {result.source_id for result in results}.issubset({"a.md", "b.md", "c.md"})
