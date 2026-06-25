import tempfile
import unittest
from pathlib import Path

from sts2_ai_stream.config import Settings
from sts2_ai_stream.control import ControlCore


class ControlCoreTest(unittest.TestCase):
    def make_core(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        settings = Settings.from_env(project_root=root)
        return temp, ControlCore(settings)

    def test_service_lifecycle(self):
        temp, core = self.make_core()
        self.addCleanup(temp.cleanup)
        started = core.service_action("training", "start", operator="test")
        self.assertEqual(started["state"], "running")
        stopped = core.service_action("training", "stop", operator="test")
        self.assertEqual(stopped["state"], "stopped")
        logs = core.logs("training")
        self.assertTrue(any("started by test" in line for line in logs["lines"]))

    def test_model_reset_creates_new_namespace_without_delete(self):
        temp, core = self.make_core()
        self.addCleanup(temp.cleanup)
        first = core.reset_model("first", operator="test")
        second = core.reset_model("second", operator="test")
        self.assertNotEqual(first["new_namespace"], second["new_namespace"])
        self.assertEqual(first["new_namespace"], second["old_namespace"])


if __name__ == "__main__":
    unittest.main()

