from __future__ import annotations

from minicliagent.core.memory.models import HybridMemoryResult, MemoryDocument, MemorySearchHit


def fuse_memory_results(
    dense_hits: list[MemorySearchHit],
    bm25_hits: list[MemorySearchHit],
    dense_weight: float,
    bm25_weight: float,
    final_top_k: int,
) -> list[HybridMemoryResult]:
    dense_scores = {hit.source_id: hit.score for hit in dense_hits}
    bm25_scores = {hit.source_id: hit.score for hit in bm25_hits}
    dense_normalized = _normalize_scores(dense_scores)
    bm25_normalized = _normalize_scores(bm25_scores)
    documents = _merge_documents(dense_hits, bm25_hits)

    results = [
        HybridMemoryResult(
            document=document,
            score=(
                dense_weight * dense_normalized.get(source_id, 0.0)
                + bm25_weight * bm25_normalized.get(source_id, 0.0)
            ),
            dense_score=dense_scores.get(source_id, 0.0),
            bm25_score=bm25_scores.get(source_id, 0.0),
            normalized_dense=dense_normalized.get(source_id, 0.0),
            normalized_bm25=bm25_normalized.get(source_id, 0.0),
        )
        for source_id, document in documents.items()
    ]
    return sorted(results, key=lambda result: (-result.score, result.source_id))[:final_top_k]


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    min_score = min(scores.values())
    max_score = max(scores.values())
    if max_score == min_score:
        return {source_id: 1.0 for source_id in scores}
    return {
        source_id: (score - min_score) / (max_score - min_score)
        for source_id, score in scores.items()
    }


def _merge_documents(
    dense_hits: list[MemorySearchHit],
    bm25_hits: list[MemorySearchHit],
) -> dict[str, MemoryDocument]:
    documents: dict[str, MemoryDocument] = {}
    for hit in dense_hits + bm25_hits:
        documents.setdefault(hit.source_id, hit.document)
    return documents
