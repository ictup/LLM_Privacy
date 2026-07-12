import json
import tempfile
import unittest
from pathlib import Path

from ragshield.benchmarks.saferag import TASKS, build_task_documents, load_saferag
from ragshield.retrieval.vector_store import LexicalVectorStore, tokenize


class SafeRAGTests(unittest.TestCase):
    def test_chinese_tokenizer_emits_bigrams(self):
        tokens = tokenize("健康教育平台")
        self.assertIn("健康", tokens)
        self.assertIn("教育", tokens)
        self.assertIn("平台", tokens)

    def test_adapter_loads_all_task_partitions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = {}
            for task in TASKS:
                raw[task] = [
                    {
                        "id": 0,
                        "questions": "测试问题",
                        "enhanced_contexts": ["可信上下文"],
                        f"enhanced_{task}_contexts": ["攻击上下文"],
                        "attack_kws": ["攻击"],
                        "numbered_options": ["1. 测试"],
                        "ground_truth_correct_options": ["1"],
                        "ground_truth_incorrect_options": [],
                    }
                ]
                kb_path = root / "knowledge_base" / task / "db.txt"
                kb_path.parent.mkdir(parents=True, exist_ok=True)
                kb_path.write_text("可信上下文\n", encoding="utf-8")
            dataset_path = root / "nctd_datasets" / "nctd.json"
            dataset_path.parent.mkdir(parents=True, exist_ok=True)
            dataset_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text("{}", encoding="utf-8")

            dataset = load_saferag(root, manifest_path=manifest, verify=False)
            documents = build_task_documents(dataset, "SA")
            self.assertEqual(dataset.case_count, 4)
            self.assertEqual(sum(doc.trusted_source for doc in documents), 1)
            self.assertEqual(sum(not doc.trusted_source for doc in documents), 1)

    def test_chinese_retrieval_ranks_relevant_context(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = {
                task: [
                    {
                        "id": 0,
                        "questions": "卫生事业取得了哪些重要进展？",
                        "enhanced_contexts": ["卫生事业在医疗资源方面取得重要进展。"],
                        f"enhanced_{task}_contexts": ["博物馆讲解服务规范。"],
                        "attack_kws": [],
                        "numbered_options": [],
                        "ground_truth_correct_options": [],
                        "ground_truth_incorrect_options": [],
                    }
                ]
                for task in TASKS
            }
            for task in TASKS:
                kb_path = root / "knowledge_base" / task / "db.txt"
                kb_path.parent.mkdir(parents=True, exist_ok=True)
                kb_path.write_text(
                    "卫生事业在医疗资源方面取得重要进展。\n博物馆讲解服务规范。\n",
                    encoding="utf-8",
                )
            dataset_path = root / "nctd_datasets" / "nctd.json"
            dataset_path.parent.mkdir(parents=True, exist_ok=True)
            dataset_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text("{}", encoding="utf-8")
            dataset = load_saferag(root, manifest_path=manifest, verify=False)
            store = LexicalVectorStore(build_task_documents(dataset, "SA"))
            result = store.search("卫生事业取得了哪些重要进展？", top_k=1)
            self.assertIn("卫生事业", result[0].text)

if __name__ == "__main__":
    unittest.main()
