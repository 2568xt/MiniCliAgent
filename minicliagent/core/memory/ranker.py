from __future__ import annotations

import re
from minicliagent.core.memory.models import HybridMemoryResult, MemoryDocument, MemorySearchHit


def mmr_diversify(
    results: list[HybridMemoryResult],
    lambda_param: float = 0.5,
    top_k: int | None = None,
) -> list[HybridMemoryResult]:
    """MMR diversification: λ·relevance - (1-λ)·max_similarity."""
    if not results:
        return []

    if len(results) <= 1:
        return results[:]

    if top_k is None:
        top_k = len(results)

    selected: list[HybridMemoryResult] = []
    remaining = list(results)

    while remaining and len(selected) < top_k:
        best_score = float("-inf")
        best_idx = 0

        for idx, candidate in enumerate(remaining):
            relevance = candidate.score
            max_sim = 0.0

            for sel in selected:
                sim = _text_similarity(candidate.document.content, sel.document.content)
                max_sim = max(max_sim, sim)

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        selected.append(remaining.pop(best_idx))

    return selected


def _text_similarity(text1: str, text2: str) -> float:
    """Jaccard similarity (word tokens) between two texts."""
    if not text1 or not text2:
        return 0.0

    tokens1 = set(re.findall(r"\w+", text1.lower()))
    tokens2 = set(re.findall(r"\w+", text2.lower()))

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union) if union else 0.0


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
