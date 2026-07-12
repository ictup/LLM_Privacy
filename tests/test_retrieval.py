import unittest

from ragshield.retrieval.vector_store import LexicalVectorStore
from ragshield.schemas import Document


class RetrievalTests(unittest.TestCase):
    def test_explicit_document_reference_ranks_target_first(self):
        documents = [
            Document(
                doc_id="project_004",
                tenant="public",
                sensitivity="public",
                contains_pii=False,
                contains_prompt_injection=False,
                trusted_source=True,
                domain="project",
                title="Project decision",
                text="Project 004 records the approved deployment decision.",
            ),
            Document(
                doc_id="project_005",
                tenant="public",
                sensitivity="public",
                contains_pii=False,
                contains_prompt_injection=False,
                trusted_source=True,
                domain="project",
                title="Unrelated project",
                text="Project 005 contains an unrelated planning note.",
            ),
        ]
        store = LexicalVectorStore(documents)
        results = store.search("Summarize project_004 and cite the decision.", top_k=5)
        self.assertEqual(results[0].doc_id, "project_004")


if __name__ == "__main__":
    unittest.main()
