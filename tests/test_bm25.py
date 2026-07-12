import unittest

from ragshield.retrieval.bm25 import BM25TextStore


class BM25Tests(unittest.TestCase):
    def test_ranks_relevant_chinese_text_first(self):
        store = BM25TextStore(
            [
                "博物馆社会讲解服务需要规范管理。",
                "医疗资源下沉改善县级医院服务。",
                "火箭发射任务取得成功。",
            ]
        )
        hits = store.search("县级医院医疗资源取得哪些进展？", top_k=2)
        self.assertEqual(hits[0].index, 1)
        self.assertGreater(hits[0].score, 0)

    def test_tie_breaking_is_deterministic(self):
        store = BM25TextStore(["医疗服务", "医疗服务"])
        self.assertEqual([hit.index for hit in store.search("医疗", 2)], [0, 1])

    def test_empty_store_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one text"):
            BM25TextStore([])


if __name__ == "__main__":
    unittest.main()
