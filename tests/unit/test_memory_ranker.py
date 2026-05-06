from minicliagent.core.memory.models import MemoryDocument, MemorySearchHit
from minicliagent.core.memory.ranker import fuse_memory_results


def _hit(source_id: str, score: float, content: str | None = None) -> MemorySearchHit:
    return MemorySearchHit(
        document=MemoryDocument(
            source_id=source_id,
            source="fragment",
            content=content or f"content {source_id}",
        ),
        score=score,
        retriever="dense",
    )


def test_hybrid_ranker_fuses_dense_and_bm25_scores_with_weights() -> None:
    dense = [_hit("same.md", 0.8), _hit("dense-only.md", 0.2)]
    bm25 = [
        MemorySearchHit(
            document=MemoryDocument(source_id="same.md", source="fragment", content="content same.md"),
            score=10.0,
            retriever="bm25",
        ),
        MemorySearchHit(
            document=MemoryDocument(source_id="bm25-only.md", source="fragment", content="content bm25.md"),
            score=5.0,
            retriever="bm25",
        ),
    ]

    results = fuse_memory_results(
        dense_hits=dense,
        bm25_hits=bm25,
        dense_weight=0.7,
        bm25_weight=0.3,
        final_top_k=6,
    )

    assert results[0].source_id == "same.md"
    assert {result.source_id for result in results[1:]} == {"dense-only.md", "bm25-only.md"}
    assert results[0].normalized_dense == 1.0
    assert results[0].normalized_bm25 == 1.0
    assert results[0].score == 1.0
    dense_only = next(result for result in results if result.source_id == "dense-only.md")
    bm25_only = next(result for result in results if result.source_id == "bm25-only.md")
    assert dense_only.normalized_bm25 == 0.0
    assert dense_only.score == 0.0
    assert bm25_only.normalized_dense == 0.0
    assert bm25_only.score == 0.0


def test_hybrid_ranker_equal_scores_normalize_hits_to_one() -> None:
    results = fuse_memory_results(
        dense_hits=[_hit("a.md", 3.0), _hit("b.md", 3.0)],
        bm25_hits=[],
        dense_weight=0.7,
        bm25_weight=0.3,
        final_top_k=6,
    )

    assert [result.normalized_dense for result in results] == [1.0, 1.0]
    assert [result.score for result in results] == [0.7, 0.7]


def test_hybrid_ranker_respects_final_top_k() -> None:
    results = fuse_memory_results(
        dense_hits=[_hit(f"{index}.md", float(index)) for index in range(10)],
        bm25_hits=[],
        dense_weight=0.7,
        bm25_weight=0.3,
        final_top_k=6,
    )

    assert len(results) == 6
    assert results[0].source_id == "9.md"
