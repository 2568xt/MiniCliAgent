import tempfile
from pathlib import Path
from minicliagent.core.memory.store import MarkdownMemoryStore
from minicliagent.core.memory.bm25 import BM25MemorySearcher
import re

# Simulating the test setup
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
    
    # Check original read_documents content
    docs = store.read_documents()
    for doc in docs:
        print(f'Doc: {doc.source}')
        print(f'Content:\n{doc.content}')
        print()
        
        # Tokenize and show
        def tokenize(text):
            return re.findall(r"[\w./-]+|[\u4e00-\u9fff]", text.lower())
        
        tokens = tokenize(doc.content)
        print(f'Tokens: {tokens}')
        
        # Check for 'markdown' and 'memory' tokens
        print(f"'markdown' in tokens: {'markdown' in tokens}")
        print(f"'memory' in tokens: {'memory' in tokens}")
        print()