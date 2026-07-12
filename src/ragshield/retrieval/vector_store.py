"""A lightweight lexical retriever used as the baseline vector-store stand-in."""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from ragshield.schemas import Document, RetrievedChunk
from ragshield.utils.jsonl import read_jsonl


TOKEN_RE = re.compile(r"[a-zA-Z0-9_+-]+")
CJK_SEQUENCE_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    tokens = [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
    for sequence in CJK_SEQUENCE_RE.findall(text):
        tokens.extend(sequence)
        tokens.extend(sequence[index : index + 2] for index in range(len(sequence) - 1))
    return tokens


def load_documents(path: str | Path) -> list[Document]:
    return [Document(**row) for row in read_jsonl(path)]


class LexicalVectorStore:
    """Deterministic lexical retrieval with simple TF-IDF-like scoring."""

    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.doc_terms = [
            Counter(tokenize(doc.doc_id + " " + doc.title + " " + doc.text)) for doc in documents
        ]
        document_frequency: Counter[str] = Counter()
        for terms in self.doc_terms:
            document_frequency.update(terms.keys())
        self.idf = {
            term: math.log((1 + len(documents)) / (1 + frequency)) + 1.0
            for term, frequency in document_frequency.items()
        }

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "LexicalVectorStore":
        return cls(load_documents(path))

    def search(
        self,
        query: str,
        top_k: int = 5,
        tenant: str | None = None,
        tenant_filtering: bool = False,
    ) -> list[RetrievedChunk]:
        query_terms = Counter(tokenize(query))
        scored: list[tuple[float, Document]] = []
        for doc, doc_terms in zip(self.documents, self.doc_terms, strict=True):
            if tenant_filtering and tenant is not None and doc.tenant != tenant:
                continue
            score = 0.0
            for term, query_count in query_terms.items():
                if term in doc_terms:
                    score += query_count * doc_terms[term] * self.idf.get(term, 1.0)
            if doc.doc_id.lower() in query_terms:
                score += 20.0
            if query.lower() in doc.text.lower():
                score += 5.0
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda item: (-item[0], item[1].doc_id))
        return [
            RetrievedChunk(
                doc_id=doc.doc_id,
                title=doc.title,
                tenant=doc.tenant,
                sensitivity=doc.sensitivity,
                trusted_source=doc.trusted_source,
                contains_pii=doc.contains_pii,
                contains_prompt_injection=doc.contains_prompt_injection,
                domain=doc.domain,
                text=doc.text,
                score=round(score, 4),
            )
            for score, doc in scored[:top_k]
        ]
