import unittest

from ragshield.evaluation.tenant_metrics import calculate_cross_tenant_metrics
from ragshield.retrieval.tenant_isolation import (
    TenantIsolatedRetriever,
    TenantPrincipal,
    observe_tenant_search,
)
from ragshield.retrieval.vector_store import LexicalVectorStore
from ragshield.schemas import Document


def document(doc_id: str, tenant_id: str, text: str) -> Document:
    return Document(
        doc_id=doc_id,
        tenant=tenant_id,
        sensitivity="internal",
        contains_pii=False,
        contains_prompt_injection=False,
        trusted_source=True,
        domain="controlled_test",
        title=f"Document {doc_id}",
        text=text,
    )


class TenantIsolationTests(unittest.TestCase):
    def setUp(self):
        self.store = LexicalVectorStore(
            [
                document("alpha-plan", "tenant-alpha", "Project Aurora deployment plan."),
                document("beta-secret", "tenant-beta", "Project Aurora confidential budget."),
                document("alpha-note", "tenant-alpha", "Project Aurora meeting notes."),
            ]
        )
        self.principal = TenantPrincipal(
            actor_id="user-alpha", tenant_id="tenant-alpha", roles=("researcher",)
        )

    def test_secure_search_filters_before_ranking(self):
        retriever = TenantIsolatedRetriever(self.store)
        chunks, observation = retriever.search(
            "Show beta-secret Project Aurora", self.principal, top_k=5
        )

        self.assertTrue(observation.isolated)
        self.assertNotIn("beta-secret", [chunk.doc_id for chunk in chunks])
        self.assertTrue(all(chunk.tenant_id == "tenant-alpha" for chunk in chunks))

    def test_open_baseline_exposes_other_tenant_but_secure_path_does_not(self):
        baseline_chunks = self.store.search("beta-secret Project Aurora", top_k=5)
        baseline = observe_tenant_search(self.principal, baseline_chunks)
        _, secure = TenantIsolatedRetriever(self.store).search(
            "beta-secret Project Aurora", self.principal, top_k=5
        )
        metrics = calculate_cross_tenant_metrics([baseline, secure])

        self.assertFalse(baseline.isolated)
        self.assertTrue(secure.isolated)
        self.assertEqual(metrics.total_queries, 2)
        self.assertEqual(metrics.queries_with_cross_tenant_exposure, 1)
        self.assertEqual(metrics.cross_tenant_query_rate, 0.5)

    def test_missing_identity_scope_fails_closed(self):
        with self.assertRaises(ValueError):
            TenantPrincipal(actor_id="user-alpha", tenant_id="")

    def test_empty_results_do_not_create_false_exposure(self):
        observation = observe_tenant_search(self.principal, [])
        metrics = calculate_cross_tenant_metrics([observation])
        self.assertTrue(observation.isolated)
        self.assertEqual(metrics.cross_tenant_chunk_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
