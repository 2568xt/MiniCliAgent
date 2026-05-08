import tempfile
from pathlib import Path
from minicliagent.core.memory.store import MarkdownMemoryStore
from minicliagent.core.memory.bm25 import BM25MemorySearcher
import re

def tokenize(text):
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
    
    # Check which lines match the query
    query = 'markdown memory'
    query_tokens = tokenize(query)
    print(f'Query tokens: {query_tokens}')
    
    print('\nMatching analysis:')
    for doc in line_docs:
        line_tokens = tokenize(doc.content)
        matches_query = all(qt in line_tokens for qt in query_tokens)
        print(f'Line {doc.line_number} ({doc.source}): {repr(doc.content[:40])}')
        print(f'  Tokens: {line_tokens}')
        print(f'  Matches query: {matches_query}')
        print()