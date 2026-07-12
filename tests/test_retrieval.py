import unittest

from ragshield.ingestion.build_corpus import generate_corpus
from ragshield.retrieval.vector_store import LexicalVectorStore


class RetrievalTests(unittest.TestCase):
    def test_explicit_document_reference_ranks_target_first(self):
        store = LexicalVectorStore(generate_corpus())
        results = store.search("Summarize project_004 and cite the decision.", top_k=5)
        self.assertEqual(results[0].doc_id, "project_004")


if __name__ == "__main__":
    unittest.main()
