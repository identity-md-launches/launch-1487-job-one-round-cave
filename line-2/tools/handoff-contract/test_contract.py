import io
import json
import unittest
import zipfile
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("contract", Path(__file__).with_name("contract.py"))
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


class ContractTests(unittest.TestCase):
    def test_demo_real_archive(self):
        result = contract.demo()
        self.assertTrue(result["contract_passed"])
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["unexpected"], [])

    def test_non_exact_reports_extra_file(self):
        result = contract.contract_receipt("line-2/handoff.zip", ["README.md"])
        self.assertTrue(result["contract_passed"])
        self.assertEqual(result["unexpected"], ["handoff.py"])

    def test_exact_rejects_extra_file(self):
        result = contract.contract_receipt("line-2/handoff.zip", ["README.md"], exact=True)
        self.assertFalse(result["contract_passed"])
        self.assertEqual(result["unexpected"], ["handoff.py"])

    def test_missing_and_unsafe_requirements(self):
        result = contract.contract_receipt("line-2/handoff.zip", ["missing.txt"])
        self.assertFalse(result["contract_passed"])
        self.assertEqual(result["missing"], ["missing.txt"])
        for value in ("../x", "HANDOFF.json", "a\\b"):
            with self.assertRaises(ValueError):
                contract.safe_contract_path(value)


if __name__ == "__main__":
    unittest.main()
