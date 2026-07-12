import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
