import copy
import importlib.util
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("activity", HERE / "activity.py")
activity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activity)


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.capture = json.loads(
            (HERE.parent / "transfer-crosscheck" / "publicnode.json").read_text()
        )

    def test_demo_shape(self):
        result = activity.activity(self.capture)
        self.assertEqual(result["transfer_count"], 3)
        self.assertEqual(result["populated_block_count"], 1)
        self.assertEqual(result["longest_empty_run"], 11)
        self.assertEqual([run["state"] for run in result["runs"]], ["empty", "populated"])

    def test_empty_window_is_one_empty_run(self):
        empty = copy.deepcopy(self.capture)
        empty["raw_logs"] = []
        empty["transfers"] = []
        empty["transfer_count"] = 0
        empty["duplicate_count"] = 0
        result = activity.activity(empty)
        self.assertEqual(len(result["runs"]), 1)
        self.assertEqual(result["runs"][0]["state"], "empty")
        self.assertEqual(result["longest_empty_run"], result["block_count"])

    def test_tampered_evidence_is_rejected(self):
        bad = copy.deepcopy(self.capture)
        bad["raw_logs"][0]["removed"] = True
        with self.assertRaises(activity.crosscheck.window.RpcError):
            activity.activity(bad)


if __name__ == "__main__":
    unittest.main()
