from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class MemoryEntry:
    content: str
    session_id: str
    source: str
    created_at: str
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MemoryDocument:
    source_id: str
    source: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MemorySearchHit:
    document: MemoryDocument
    score: float
    retriever: str

    @property
    def source_id(self) -> str:
        return self.document.source_id

    @property
    def content(self) -> str:
        return self.document.content


@dataclass(frozen=True)
class HybridMemoryResult:
    document: MemoryDocument
    score: float
    dense_score: float = 0.0
    bm25_score: float = 0.0
    normalized_dense: float = 0.0
    normalized_bm25: float = 0.0

    @property
    def source_id(self) -> str:
        return self.document.source_id

    @property
    def content(self) -> str:
        return self.document.content


@dataclass(frozen=True)
class MemoryAppendResult:
    written: bool
    summary_path: Path | None = None
    fragment_path: Path | None = None
    entries: list[MemoryEntry] = field(default_factory=list)


@dataclass(frozen=True)
class MemorySearchDiagnostics:
    dense_available: bool
    dense_fallback: bool
    dense_hits: int
    bm25_hits: int
    final_hits: int
    retriever: list[str] = field(default_factory=list)
    fallback_reason: str | None = None
