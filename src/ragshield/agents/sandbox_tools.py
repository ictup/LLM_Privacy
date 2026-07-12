"""Local-only sandbox tools for agent security evaluation."""

from __future__ import annotations

from ragshield.retrieval.vector_store import LexicalVectorStore


def search_docs(query: str, tenant: str | None = None, top_k: int = 3) -> dict:
    store = LexicalVectorStore.from_jsonl("data/synthetic_docs/corpus.jsonl")
    chunks = store.search(query=query, top_k=top_k, tenant=tenant, tenant_filtering=tenant is not None)
    return {
        "status": "ok",
        "results": [
            {
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "score": chunk.score,
                "tenant": chunk.tenant,
            }
            for chunk in chunks
        ],
    }


def update_ticket(ticket_id: str, status: str) -> dict:
    return {
        "status": "sandboxed",
        "ticket_id": ticket_id,
        "new_status": status,
        "side_effect": "not_persisted",
    }


def send_email(to: str, body: str) -> dict:
    return {
        "status": "sandboxed",
        "to": to,
        "body_preview": body[:80],
        "side_effect": "email_not_sent",
    }


def read_secret_store(key: str) -> dict:
    raise PermissionError(f"read_secret_store is forbidden in the RAGShield sandbox: {key}")
