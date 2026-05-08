from __future__ import annotations

import re
from typing import Protocol

from minicliagent.core.llm.types import ModelRequest
from minicliagent.core.memory.bm25 import BM25MemorySearcher
from minicliagent.core.memory.models import (
    HybridMemoryResult,
    MemoryAppendResult,
    MemoryDocument,
    MemorySearchDiagnostics,
)
from minicliagent.core.memory.ranker import fuse_memory_results
from minicliagent.core.memory.store import MarkdownMemoryStore

TOOL_KEYWORD_PATTERNS = [
    re.compile(r'\bprefer\b'),
    re.compile(r'\blike\b'),
    re.compile(r'\buse\b'),
    re.compile(r'\bavoid\b'),
    re.compile(r'\bremember\b'),
    re.compile(r'\bimportant\b'),
]


class DenseMemoryIndex(Protocol):
    def search(self, query: str, top_k: int):
        ...

    def add_documents(self, documents: list[MemoryDocument]) -> None:
        ...


class MemorySummarizer(Protocol):
    def summarize(self, session_id: str, messages: list[dict], source: str) -> list[str]:
        ...


class MemoryService:
    def __init__(
        self,
        store: MarkdownMemoryStore,
        dense_index: DenseMemoryIndex,
        dense_weight: float,
        bm25_weight: float,
        dense_top_k: int,
        bm25_top_k: int,
        final_top_k: int,
        summarizer: MemorySummarizer | None = None,
        logger=None,
    ) -> None:
        self.store = store
        self.dense_index = dense_index
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.dense_top_k = dense_top_k
        self.bm25_top_k = bm25_top_k
        self.final_top_k = final_top_k
        self.summarizer = summarizer
        self.logger = logger
        self.last_search_diagnostics = MemorySearchDiagnostics(
            dense_available=True,
            dense_fallback=False,
            dense_hits=0,
            bm25_hits=0,
            final_hits=0,
            retriever=[],
        )

    def search(self, query: str) -> list[HybridMemoryResult]:
        documents = self.store.read_documents()
        bm25_hits = BM25MemorySearcher(documents).search(query, top_k=self.bm25_top_k)
        dense_available = True
        dense_fallback = False
        fallback_reason: str | None = None
        try:
            dense_hits = self.dense_index.search(query, top_k=self.dense_top_k)
        except Exception as exc:
            dense_available = False
            dense_fallback = True
            fallback_reason = str(exc)
            dense_hits = []
            if self.logger is not None:
                self.logger.log("warning", "memory_dense_search_failed", query=query, error=str(exc))
        results = fuse_memory_results(
            dense_hits=dense_hits,
            bm25_hits=bm25_hits,
            dense_weight=self.dense_weight,
            bm25_weight=self.bm25_weight,
            final_top_k=self.final_top_k,
        )
        retriever: list[str] = []
        if dense_available:
            retriever.append("dense")
        if bm25_hits:
            retriever.append("bm25")
        self.last_search_diagnostics = MemorySearchDiagnostics(
            dense_available=dense_available,
            dense_fallback=dense_fallback,
            dense_hits=len(dense_hits),
            bm25_hits=len(bm25_hits),
            final_hits=len(results),
            retriever=retriever,
            fallback_reason=fallback_reason,
        )
        if self.logger is not None:
            self.logger.log(
                "info",
                "memory_search_completed",
                query=query,
                dense_available=dense_available,
                dense_fallback=dense_fallback,
                dense_hits=len(dense_hits),
                bm25_hits=len(bm25_hits),
                final_hits=len(results),
            )
        return results

    def remember_session(
        self,
        session_id: str,
        messages: list[dict],
        source: str,
    ) -> MemoryAppendResult:
        if self.summarizer is None:
            if self.logger is not None:
                self.logger.log("info", "memory_summary_skipped", session_id=session_id, source=source, reason="no_summarizer")
            return MemoryAppendResult(written=False)
        entries = self.summarizer.summarize(session_id, messages, source)
        if self.logger is not None:
            self.logger.log(
                "info",
                "memory_summary_generated",
                session_id=session_id,
                source=source,
                entry_count=len(entries),
            )
        result = self.store.append_entries(session_id=session_id, source=source, entries=entries)
        if result.written and result.fragment_path is not None:
            document = MemoryDocument(
                source_id=result.fragment_path.name,
                source="fragment",
                content=result.fragment_path.read_text(encoding="utf-8"),
                metadata={"path": str(result.fragment_path), "source": source, "session_id": session_id},
            )
            try:
                self.dense_index.add_documents([document])
                if self.logger is not None:
                    self.logger.log(
                        "info",
                        "memory_dense_index_updated",
                        session_id=session_id,
                        source=source,
                        fragment_path=str(result.fragment_path),
                    )
            except Exception as exc:
                if self.logger is not None:
                    self.logger.log(
                        "warning",
                        "memory_dense_index_update_failed",
                        session_id=session_id,
                        source=source,
                        error=str(exc),
                    )
        elif self.logger is not None:
            self.logger.log("info", "memory_summary_not_written", session_id=session_id, source=source)
        return result


class ProviderMemorySummarizer:
    def __init__(self, provider, max_transcript_chars: int = 12000, fallback: object | None = None, logger=None) -> None:
        self.provider = provider
        self.max_transcript_chars = max_transcript_chars
        self.fallback = fallback or LocalMemorySummarizer()
        self.logger = logger

    def summarize(self, session_id: str, messages: list[dict], source: str) -> list[str]:
        transcript = _render_transcript(messages)[-self.max_transcript_chars :]
        try:
            response = self.provider.create_response(
                ModelRequest(
                    system=(
                        "Extract durable long-term memory from this MiniCLIAgent session. "
                        "Return concise bullet points only. Include stable user preferences, "
                        "project conventions, and decisions. If there is nothing worth remembering, "
                        "return NO_MEMORY."
                    ),
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                f"session_id: {session_id}\n"
                                f"source: {source}\n\n"
                                f"<session-transcript>\n{transcript}\n</session-transcript>"
                            ),
                        }
                    ],
                    tools=[],
                    max_tokens=512,
                )
            )
            parsed = _parse_memory_entries(response.text)
            if parsed:
                return parsed
        except Exception:
            pass
        if self.logger is not None:
            self.logger.log("warning", "memory_provider_summary_failed", session_id=session_id, source=source)
        return self.fallback.summarize(session_id, messages, source)


class LocalMemorySummarizer:
    def summarize(self, session_id: str, messages: list[dict], source: str) -> list[str]:
        transcript = _render_transcript(messages)
        candidates: list[str] = []
        for line in transcript.splitlines():
            line = line.strip()
            lower = line.lower()
            if any(p.search(lower) for p in TOOL_KEYWORD_PATTERNS):
                if ":" in line:
                    line = line.split(":", 1)[1].strip()
                candidates.append(line)
        return _dedupe_entries(candidates)


def _render_transcript(messages: list[dict]) -> str:
    parts: list[str] = []
    for message in messages:
        parts.append(f"{message.get('role', 'unknown')}: {message.get('content', '')}")
    return "\n".join(parts)


def _parse_memory_entries(text: str) -> list[str]:
    clean = text.strip()
    if not clean or clean.upper() == "NO_MEMORY":
        return []
    entries: list[str] = []
    for line in clean.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if line and line.upper() != "NO_MEMORY":
            entries.append(line)
    return _dedupe_entries(entries)


def _dedupe_entries(entries: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for entry in entries:
        normalized = entry.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(entry.strip())
    return deduped
