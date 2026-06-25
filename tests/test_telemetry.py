import tempfile
import unittest
from pathlib import Path

from sts2_ai_stream.telemetry import JsonlEventStore


class TelemetryTest(unittest.TestCase):
    def test_append_and_tail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = JsonlEventStore(root, root / "audit" / "control.jsonl")
            event = store.append("training.metrics", {"step": 1}, source="test")
            store.write_service_log("training", "hello")
            self.assertEqual(event["type"], "training.metrics")
            self.assertEqual(len(store.recent_events("training.metrics")), 1)
            self.assertTrue(store.tail_log("training")[0].endswith("hello"))


if __name__ == "__main__":
    unittest.main()

