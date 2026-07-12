"""Fail-closed tenant authorization for retrieval operations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from ragshield.retrieval.vector_store import LexicalVectorStore
from ragshield.schemas import RetrievedChunk


@dataclass(frozen=True)
class TenantPrincipal:
    actor_id: str
    tenant_id: str
    roles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("actor_id is required.")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required.")


@dataclass(frozen=True)
class TenantSearchObservation:
    actor_id: str
    requested_tenant_id: str
    returned_doc_ids: tuple[str, ...]
    returned_tenant_ids: tuple[str, ...]

    @property
    def cross_tenant_doc_ids(self) -> tuple[str, ...]:
        return tuple(
            doc_id
            for doc_id, tenant_id in zip(
                self.returned_doc_ids, self.returned_tenant_ids, strict=True
            )
            if tenant_id != self.requested_tenant_id
        )

    @property
    def isolated(self) -> bool:
        return not self.cross_tenant_doc_ids

    def to_dict(self) -> dict[str, object]:
        row = asdict(self)
        row["cross_tenant_doc_ids"] = self.cross_tenant_doc_ids
        row["isolated"] = self.isolated
        return row


def observe_tenant_search(
    principal: TenantPrincipal,
    chunks: Iterable[RetrievedChunk],
) -> TenantSearchObservation:
    rows = tuple(chunks)
    return TenantSearchObservation(
        actor_id=principal.actor_id,
        requested_tenant_id=principal.tenant_id,
        returned_doc_ids=tuple(chunk.doc_id for chunk in rows),
        returned_tenant_ids=tuple(chunk.tenant_id for chunk in rows),
    )


class TenantIsolatedRetriever:
    """Retriever whose public search path always enforces exact tenant scope."""

    def __init__(self, store: LexicalVectorStore):
        self.store = store

    def search(
        self,
        query: str,
        principal: TenantPrincipal,
        top_k: int = 5,
    ) -> tuple[list[RetrievedChunk], TenantSearchObservation]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        chunks = self.store.search(
            query=query,
            top_k=top_k,
            tenant=principal.tenant_id,
            tenant_filtering=True,
        )
        observation = observe_tenant_search(principal, chunks)
        if not observation.isolated:
            raise RuntimeError("Tenant boundary violation detected after retrieval.")
        return chunks, observation
