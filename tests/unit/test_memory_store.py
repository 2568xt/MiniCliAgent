from pathlib import Path

from minicliagent.core.memory.store import MarkdownMemoryStore


def test_markdown_memory_store_appends_summary_and_fragment(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(
        summary_path=tmp_path / ".minicliagent" / "memory.md",
        fragments_dir=tmp_path / ".minicliagent" / "memory",
    )

    result = store.append_entries(
        session_id="chat/session",
        source="exit_hook",
        entries=["User prefers Markdown-first memory.", "Use hybrid memory search."],
        created_at="2026-05-04T01:02:03",
    )

    assert result.written is True
    assert result.fragment_path is not None
    assert result.fragment_path.name == "20260504T010203-chat-session.md"
    summary = (tmp_path / ".minicliagent" / "memory.md").read_text()
    assert "## 2026-05-04T01:02:03 session: chat/session" in summary
    assert "- User prefers Markdown-first memory." in summary
    assert "- Use hybrid memory search." in summary
    fragment = result.fragment_path.read_text()
    assert "source: exit_hook" in fragment
    assert "- User prefers Markdown-first memory." in fragment


def test_markdown_memory_store_skips_empty_entries(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(
        summary_path=tmp_path / ".minicliagent" / "memory.md",
        fragments_dir=tmp_path / ".minicliagent" / "memory",
    )

    result = store.append_entries(
        session_id="s1",
        source="exit_hook",
        entries=["", "   "],
        created_at="2026-05-04T01:02:03",
    )

    assert result.written is False
    assert not (tmp_path / ".minicliagent" / "memory.md").exists()
    assert not (tmp_path / ".minicliagent" / "memory").exists()


def test_markdown_memory_store_reads_searchable_documents(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(
        summary_path=tmp_path / ".minicliagent" / "memory.md",
        fragments_dir=tmp_path / ".minicliagent" / "memory",
    )
    store.append_entries(
        session_id="s1",
        source="compact_hook",
        entries=["User likes concise final answers."],
        created_at="2026-05-04T01:02:03",
    )

    documents = store.read_documents()

    assert [document.source for document in documents] == ["summary", "fragment"]
    assert documents[0].source_id == "memory.md"
    assert "concise final answers" in documents[0].content
    assert documents[1].source_id == "20260504T010203-s1.md"
    assert "compact_hook" in documents[1].metadata["source"]
