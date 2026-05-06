from __future__ import annotations

from pathlib import Path
from typing import Any

from minicliagent.core.memory.models import MemoryDocument, MemorySearchHit


class UnavailableDenseMemoryIndex:
    def __init__(self, reason: str = "dense memory index unavailable") -> None:
        self.reason = reason

    def search(self, query: str, top_k: int) -> list[MemorySearchHit]:
        return []

    def add_documents(self, documents: list[MemoryDocument]) -> None:
        return None


class Mem0DenseMemoryIndex:
    def __init__(self, index_dir: Path, user_id: str = "minicliagent") -> None:
        self.index_dir = index_dir
        self.user_id = user_id
        self._memory = _create_mem0_memory(index_dir)

    def search(self, query: str, top_k: int) -> list[MemorySearchHit]:
        raw_results = self._memory.search(query=query, user_id=self.user_id, limit=top_k)
        if isinstance(raw_results, dict):
            raw_items = raw_results.get("results", [])
        else:
            raw_items = raw_results

        hits: list[MemorySearchHit] = []
        for index, item in enumerate(raw_items[:top_k]):
            if not isinstance(item, dict):
                continue
            metadata = item.get("metadata") or {}
            source_id = str(metadata.get("source_id") or item.get("id") or f"mem0-{index}")
            content = str(item.get("memory") or item.get("text") or item.get("content") or "")
            if not content:
                continue
            score = _score_from_item(item)
            hits.append(
                MemorySearchHit(
                    document=MemoryDocument(
                        source_id=source_id,
                        source="dense",
                        content=content,
                        metadata={str(key): str(value) for key, value in metadata.items()},
                    ),
                    score=score,
                    retriever="dense",
                )
            )
        return hits

    def add_documents(self, documents: list[MemoryDocument]) -> None:
        for document in documents:
            self._memory.add(
                document.content,
                user_id=self.user_id,
                metadata={
                    "source_id": document.source_id,
                    "source": document.source,
                    **document.metadata,
                },
            )


def _create_mem0_memory(index_dir: Path) -> Any:
    try:
        from mem0 import Memory
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError(f"mem0 is unavailable: {exc}") from exc

    index_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": str(index_dir / "qdrant"),
            },
        },
        "history_db_path": str(index_dir / "history.db"),
    }
    try:
        if hasattr(Memory, "from_config"):
            return Memory.from_config(config)
        return Memory(config=config)
    except Exception:
        return Memory()


def _score_from_item(item: dict) -> float:
    for key in ("score", "similarity", "relevance"):
        value = item.get(key)
        if isinstance(value, int | float):
            return float(value)
    return 1.0
