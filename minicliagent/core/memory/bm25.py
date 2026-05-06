from __future__ import annotations

import math
import re
from collections import Counter

from minicliagent.core.memory.models import MemoryDocument, MemorySearchHit


class BM25MemorySearcher:
    def __init__(self, documents: list[MemoryDocument], k1: float = 1.5, b: float = 0.75) -> None:
        self.documents = documents
        self.k1 = k1
        self.b = b
        self._tokens = [_tokenize(document.content) for document in documents]
        self._term_counts = [Counter(tokens) for tokens in self._tokens]
        self._doc_freqs = _document_frequencies(self._tokens)
        self._avg_doc_len = (
            sum(len(tokens) for tokens in self._tokens) / len(self._tokens) if self._tokens else 0.0
        )

    def search(self, query: str, top_k: int) -> list[MemorySearchHit]:
        query_terms = _tokenize(query)
        if not query_terms or not self.documents or top_k <= 0:
            return []

        scored: list[MemorySearchHit] = []
        for index, document in enumerate(self.documents):
            score = self._score(query_terms, index)
            if score > 0:
                scored.append(MemorySearchHit(document=document, score=score, retriever="bm25"))
        return sorted(scored, key=lambda hit: (-hit.score, hit.source_id))[:top_k]

    def _score(self, query_terms: list[str], document_index: int) -> float:
        score = 0.0
        term_counts = self._term_counts[document_index]
        doc_len = len(self._tokens[document_index])
        for term in query_terms:
            frequency = term_counts.get(term, 0)
            if frequency == 0:
                continue
            idf = self._idf(term)
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * (doc_len / self._avg_doc_len if self._avg_doc_len else 0)
            )
            score += idf * (frequency * (self.k1 + 1)) / denominator
        return score

    def _idf(self, term: str) -> float:
        doc_count = len(self.documents)
        doc_frequency = self._doc_freqs.get(term, 0)
        return math.log(1 + (doc_count - doc_frequency + 0.5) / (doc_frequency + 0.5))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w./-]+|[\u4e00-\u9fff]", text.lower())


def _document_frequencies(documents: list[list[str]]) -> dict[str, int]:
    frequencies: dict[str, int] = {}
    for tokens in documents:
        for token in set(tokens):
            frequencies[token] = frequencies.get(token, 0) + 1
    return frequencies
