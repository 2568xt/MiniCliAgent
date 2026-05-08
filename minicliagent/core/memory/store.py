from __future__ import annotations

import re
from datetime import datetime, UTC
from pathlib import Path

from minicliagent.core.memory.models import MemoryAppendResult, MemoryDocument, MemoryEntry


class MarkdownMemoryStore:
    def __init__(self, summary_path: Path, fragments_dir: Path) -> None:
        self.summary_path = summary_path
        self.fragments_dir = fragments_dir

    def append_entries(
        self,
        session_id: str,
        source: str,
        entries: list[str],
        created_at: str | None = None,
    ) -> MemoryAppendResult:
        clean_entries = [entry.strip() for entry in entries if entry.strip()]
        if not clean_entries:
            return MemoryAppendResult(written=False)

        created_at = created_at or datetime.now(UTC).replace(microsecond=0).isoformat()
        memory_entries = [
            MemoryEntry(
                content=entry,
                session_id=session_id,
                source=source,
                created_at=created_at,
            )
            for entry in clean_entries
        ]
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        self.fragments_dir.mkdir(parents=True, exist_ok=True)

        summary_block = _render_summary_block(session_id, created_at, clean_entries)
        with self.summary_path.open("a", encoding="utf-8") as handle:
            if self.summary_path.stat().st_size > 0:
                handle.write("\n")
            handle.write(summary_block)

        fragment_path = self.fragments_dir / _fragment_name(session_id, created_at)
        fragment_path.write_text(
            _render_fragment(session_id, source, created_at, clean_entries),
            encoding="utf-8",
        )
        return MemoryAppendResult(
            written=True,
            summary_path=self.summary_path,
            fragment_path=fragment_path,
            entries=memory_entries,
        )

    def read_documents(self) -> list[MemoryDocument]:
        documents: list[MemoryDocument] = []
        if self.summary_path.exists():
            content = self.summary_path.read_text(encoding="utf-8").strip()
            if content:
                documents.append(
                    MemoryDocument(
                        source_id=self.summary_path.name,
                        source="summary",
                        content=content,
                        metadata={"path": str(self.summary_path)},
                    )
                )

        if self.fragments_dir.exists():
            for path in sorted(self.fragments_dir.glob("*.md")):
                content = path.read_text(encoding="utf-8").strip()
                if not content:
                    continue
                documents.append(
                    MemoryDocument(
                        source_id=path.name,
                        source="fragment",
                        content=content,
                        metadata={
                            "path": str(path),
                            "source": _metadata_value(content, "source"),
                            "session_id": _metadata_value(content, "session_id"),
                            "created_at": _metadata_value(content, "created_at"),
                        },
                    )
                )
        return documents

    def read_line_documents(self) -> list[MemoryDocument]:
        documents: list[MemoryDocument] = []

        if self.summary_path.exists():
            lines = self.summary_path.read_text(encoding="utf-8").splitlines()
            for line_num, line in enumerate(lines, start=1):
                line = line.strip()
                if not line:
                    continue
                documents.append(MemoryDocument(
                    source_id=self.summary_path.name,
                    source="summary",
                    content=line,
                    metadata={"path": str(self.summary_path)},
                    line_number=line_num,
                ))

        if self.fragments_dir.exists():
            for path in sorted(self.fragments_dir.glob("*.md")):
                text = path.read_text(encoding="utf-8")
                # Parse frontmatter once per file (not per line)
                file_meta = {
                    "path": str(path),
                    "source": _metadata_value(text, "source"),
                    "session_id": _metadata_value(text, "session_id"),
                    "created_at": _metadata_value(text, "created_at"),
                }
                lines = text.splitlines()
                for line_num, line in enumerate(lines, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    documents.append(MemoryDocument(
                        source_id=path.name,
                        source="fragment",
                        content=line,
                        metadata=dict(file_meta),
                        line_number=line_num,
                    ))
        return documents


def _render_summary_block(session_id: str, created_at: str, entries: list[str]) -> str:
    lines = [f"## {created_at} session: {session_id}", ""]
    lines.extend(f"- {entry}" for entry in entries)
    lines.append("")
    return "\n".join(lines)


def _render_fragment(session_id: str, source: str, created_at: str, entries: list[str]) -> str:
    lines = [
        "---",
        f"session_id: {session_id}",
        f"source: {source}",
        f"created_at: {created_at}",
        "---",
        "",
        "# Memory",
        "",
    ]
    lines.extend(f"- {entry}" for entry in entries)
    lines.append("")
    return "\n".join(lines)


def _fragment_name(session_id: str, created_at: str) -> str:
    timestamp = created_at.replace("-", "").replace(":", "")
    session_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", session_id).strip("-") or "session"
    return f"{timestamp}-{session_slug}.md"


def _metadata_value(content: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", content, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""
