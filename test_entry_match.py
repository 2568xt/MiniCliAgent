import tempfile
from pathlib import Path
from minicliagent.core.memory.store import MarkdownMemoryStore
from minicliagent.core.memory.bm25 import BM25MemorySearcher
import re

def tokenize(text: str) -> list[str]:
    return re.findall(r"[\w./-]+|[\u4e00-\u9fff]", text.lower())

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_path = Path(tmp_dir)
    store = MarkdownMemoryStore(
        summary_path=tmp_path / '.minicliagent' / 'memory.md',
        fragments_dir=tmp_path / '.minicliagent' / 'memory',
    )
    store.append_entries(
        session_id='s1',
        source='exit_hook',
        entries=['User prefers Markdown-first memory.'],
        created_at='2026-05-04T01:02:03',
    )
    
    line_docs = store.read_line_documents()
    
    # Check the specific line
    for doc in line_docs:
        if doc.line_number == 9 and doc.source == 'fragment':
            print('Entry line:', repr(doc.content))
            print('Tokens:', tokenize(doc.content))
            
            query = 'markdown memory'
            query_tokens = tokenize(query)
            print('Query tokens:', query_tokens)
            
            # Manually calculate score
            line_tokens = tokenize(doc.content)
            common = set(query_tokens) & set(line_tokens)
            print('Common tokens:', common)
            has_markdown = 'markdown' in line_tokens
            has_memory = 'memory' in line_tokens
            has_markdown_first = 'markdown-first' in line_tokens
            print('markdown in tokens:', has_markdown)
            print('memory in tokens:', has_memory)
            print('markdown-first in tokens:', has_markdown_first)