import re

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w./-]+|[\u4e00-\u9fff]", text.lower())

# Original full content
full_content = """---
session_id: s1
source: exit_hook
created_at: 2026-05-04T01:02:03
---

# Memory

- User prefers Markdown-first memory."""

tokens = _tokenize(full_content)
print(f"Full content tokens: {tokens}")
print(f"'markdown' in tokens: {'markdown' in tokens}")
print(f"'memory' in tokens: {'memory' in tokens}")
print(f"'markdown-first' in tokens: {'markdown-first' in tokens}")