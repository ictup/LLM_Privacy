"""Cross-tenant exposure metrics for retrieval studies."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from ragshield.retrieval.tenant_isolation import TenantSearchObservation


@dataclass(frozen=True)
class CrossTenantMetrics:
    total_queries: int
    queries_with_cross_tenant_exposure: int
    cross_tenant_query_rate: float
    returned_chunks: int
    cross_tenant_chunks: int
    cross_tenant_chunk_rate: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def calculate_cross_tenant_metrics(
    observations: Iterable[TenantSearchObservation],
) -> CrossTenantMetrics:
    rows = list(observations)
    exposed_queries = sum(not row.isolated for row in rows)
    returned_chunks = sum(len(row.returned_doc_ids) for row in rows)
    cross_tenant_chunks = sum(len(row.cross_tenant_doc_ids) for row in rows)
    return CrossTenantMetrics(
        total_queries=len(rows),
        queries_with_cross_tenant_exposure=exposed_queries,
        cross_tenant_query_rate=round(exposed_queries / len(rows), 6) if rows else 0.0,
        returned_chunks=returned_chunks,
        cross_tenant_chunks=cross_tenant_chunks,
        cross_tenant_chunk_rate=(
            round(cross_tenant_chunks / returned_chunks, 6) if returned_chunks else 0.0
        ),
    )
