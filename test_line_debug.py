import tempfile
from pathlib import Path
from minicliagent.core.memory.store import MarkdownMemoryStore
from minicliagent.core.memory.bm25 import BM25MemorySearcher

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_path = Path(tmp_dir)
    store = MarkdownMemoryStore(
        summary_path=tmp_path / '.minicliagent' / 'memory.md',
        fragments_dir=tmp_path / '.minicliagent' / 'memory',
    )
    store.append_entries(session_id='s1', source='exit_hook', entries=['User prefers Markdown-first memory.'], created_at='2026-05-04T01:02:03')
    
    line_docs = store.read_line_documents()
    print('Line docs count:', len(line_docs))
    for doc in line_docs:
        print(f'  line={doc.line_number}, content={repr(doc.content[:50])}')
    
    searcher = BM25MemorySearcher(line_docs)
    hits = searcher.search('markdown memory', top_k=5)
    print('Hits:', len(hits))
    for hit in hits:
        print(f'  score={hit.score:.3f}, line={hit.document.line_number}, content={repr(hit.content[:40])}')