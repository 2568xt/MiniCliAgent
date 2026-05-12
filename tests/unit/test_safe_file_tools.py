from pathlib import Path

from minicliagent.core.tools.builtins.files import edit_text_file, read_text_file, write_text_file


def test_read_text_file_rejects_workspace_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("bad")

    result = read_text_file(
        workspace_root=tmp_path,
        path="../outside.txt",
    )

    assert result.is_error is True
    assert "resolves to" in result.content or "escapes workspace" in result.content


def test_write_text_file_writes_inside_workspace(tmp_path: Path) -> None:
    result = write_text_file(
        workspace_root=tmp_path,
        path="notes.txt",
        content="hello",
    )

    assert result.is_error is False
    assert (tmp_path / "notes.txt").read_text() == "hello"


def test_edit_text_file_replaces_first_match(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello world hello")

    result = edit_text_file(
        workspace_root=tmp_path,
        path="notes.txt",
        old_text="hello",
        new_text="hi",
    )

    assert result.is_error is False
    assert file_path.read_text() == "hi world hello"
