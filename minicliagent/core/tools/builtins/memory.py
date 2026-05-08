from __future__ import annotations

import json

from minicliagent.core.memory.service import MemoryService
from minicliagent.core.tools.models import ToolResult


def memory_get_tool(memory_service: MemoryService, source_id: str) -> ToolResult:
    """Get a specific memory document by its source_id.

    Args:
        memory_service: The memory service instance.
        source_id: The unique identifier of the memory document (e.g., 'summary.md' or fragment filename).

    Returns:
        ToolResult with the memory document content or error message.
    """
    documents = memory_service.store.read_documents()
    for doc in documents:
        if doc.source_id == source_id:
            payload = {
                "source_id": doc.source_id,
                "source": doc.source,
                "content": doc.content,
                "metadata": doc.metadata,
            }
            return ToolResult(content=json.dumps(payload, ensure_ascii=False, indent=2))
    return ToolResult(content=json.dumps({"error": f"Memory document not found: {source_id}"}), is_error=True)


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
                "line_number": result.document.line_number,
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
