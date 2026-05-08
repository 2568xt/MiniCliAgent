import tempfile
from pathlib import Path
from minicliagent.core.memory.store import MarkdownMemoryStore
from minicliagent.core.memory.bm25 import BM25MemorySearcher
from minicliagent.core.memory.models import MemoryDocument, MemorySearchHit
from minicliagent.core.memory.ranker import fuse_memory_results

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
    
    # Dense index fake
    dense_doc = MemoryDocument(
        source_id='dense.md',
        source='fragment',
        content='Dense hit about semantic memory.',
    )
    dense_hits = [MemorySearchHit(dense_doc, 0.9, 'dense')]
    
    # BM25 with ORIGINAL read_documents
    docs = store.read_documents()
    print('Original docs:')
    for doc in docs:
        print(f'  source={doc.source}, content={repr(doc.content[:80])}')
    
    searcher = BM25MemorySearcher(docs)
    bm25_hits = searcher.search('markdown memory', top_k=4)
    print(f'\nBM25 hits: {len(bm25_hits)}')
    for hit in bm25_hits:
        print(f'  score={hit.score:.3f}, source={hit.document.source}, content={repr(hit.content[:60])}')
    
    # Now fuse
    results = fuse_memory_results(
        dense_hits=dense_hits,
        bm25_hits=bm25_hits,
        dense_weight=0.7,
        bm25_weight=0.3,
        final_top_k=6,
    )
    
    print(f'\nFused results: {len(results)}')
    for result in results:
        print(f'  source_id={result.source_id}, content={repr(result.content[:60])}')
        print(f'    dense_score={result.dense_score:.3f}, bm25_score={result.bm25_score:.3f}, final={result.score:.3f}')
    
    # Check if any contains "Markdown-first memory"
    print(f'\nAny result contains "Markdown-first memory": {any("Markdown-first memory" in r.content for r in results)}')