from __future__ import annotations

import json

from minicliagent.core.memory.service import MemoryService
from minicliagent.core.tools.models import ToolResult


def memory_search_tool(memory_service: MemoryService, query: str) -> ToolResult:
    results = memory_service.search(query)
    diagnostics = memory_service.last_search_diagnostics
    payload = {
        "query": query,
        "diagnostics": {
            "dense_available": diagnostics.dense_available,
            "dense_fallback": diagnostics.dense_fallback,
            "dense_hits": diagnostics.dense_hits,
            "bm25_hits": diagnostics.bm25_hits,
            "final_hits": diagnostics.final_hits,
            "retriever": diagnostics.retriever,
            "fallback_reason": diagnostics.fallback_reason,
        },
        "results": [
            {
                "source_id": result.source_id,
                "source": result.document.source,
                "content": result.content,
                "score": result.score,
                "dense_score": result.dense_score,
                "bm25_score": result.bm25_score,
                "normalized_dense": result.normalized_dense,
                "normalized_bm25": result.normalized_bm25,
                "metadata": result.document.metadata,
            }
            for result in results
        ],
    }
    return ToolResult(content=json.dumps(payload, ensure_ascii=False, indent=2))
