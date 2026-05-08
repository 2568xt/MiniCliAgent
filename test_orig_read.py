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
    
    # Test with original read_documents
    docs = store.read_documents()
    print('Original read_documents() count:', len(docs))
    for doc in docs:
        print(f'  source={doc.source}, content={repr(doc.content[:80])}')
    
    searcher = BM25MemorySearcher(docs)
    hits = searcher.search('markdown memory', top_k=5)
    print('Hits with read_documents:', len(hits))
    for hit in hits:
        print(f'  score={hit.score:.3f}, source={hit.document.source}, content={repr(hit.content[:50])}')