import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ragshield.tracing.logger import AuditLogger


class AuditLoggerTests(unittest.TestCase):
    def test_writes_jsonl_event(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "trace.jsonl"
            logger = AuditLogger(path)
            logger.log("test_event", {"test_id": "T001"})
            row = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(row["event_type"], "test_event")
            self.assertEqual(row["test_id"], "T001")
            self.assertIn("timestamp_utc", row)

    def test_multiple_instances_write_complete_concurrent_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "trace.jsonl"
            loggers = [AuditLogger(path), AuditLogger(path)]
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [
                    executor.submit(
                        loggers[index % 2].log,
                        "concurrent_event",
                        {"index": index},
                    )
                    for index in range(100)
                ]
                for future in futures:
                    future.result()

            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 100)
            self.assertEqual({row["index"] for row in rows}, set(range(100)))


if __name__ == "__main__":
    unittest.main()
