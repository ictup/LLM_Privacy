"""Dependency-free BM25 retrieval for reproducible SafeRAG experiments."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from ragshield.retrieval.vector_store import tokenize


@dataclass(frozen=True)
class BM25Hit:
    text: str
    score: float
    index: int


class BM25TextStore:
    """Small Okapi BM25 index over text records."""

    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75):
        if not texts:
            raise ValueError("BM25TextStore requires at least one text.")
        self.texts = list(texts)
        self.k1 = k1
        self.b = b
        self.term_counts = [Counter(tokenize(text)) for text in texts]
        self.lengths = [sum(counts.values()) for counts in self.term_counts]
        self.avg_length = sum(self.lengths) / len(self.lengths)
        document_frequency: Counter[str] = Counter()
        for counts in self.term_counts:
            document_frequency.update(counts.keys())
        count = len(texts)
        self.idf = {
            term: math.log(1.0 + (count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def search(self, query: str, top_k: int) -> list[BM25Hit]:
        query_terms = Counter(tokenize(query))
        scored = []
        for index, (counts, length) in enumerate(zip(self.term_counts, self.lengths, strict=True)):
            score = 0.0
            normalization = self.k1 * (1 - self.b + self.b * length / self.avg_length)
            for term, query_frequency in query_terms.items():
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                score += (
                    self.idf.get(term, 0.0)
                    * frequency
                    * (self.k1 + 1)
                    / (frequency + normalization)
                    * query_frequency
                )
            scored.append(BM25Hit(self.texts[index], round(score, 6), index))
        scored.sort(key=lambda hit: (-hit.score, hit.index))
        return scored[:top_k]
