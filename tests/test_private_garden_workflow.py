"""Finite, path-independent offline workflow proved through the ordinary CLI."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("private_garden_demo", ROOT / "scripts/private_garden_demo.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class PrivateGardenWorkflowTests(unittest.TestCase):
    def test_offline_archive_review_search_context_and_relocation_match_committed_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = demo.run_demo(Path(temporary) / "new-private-workspace")
        expected = json.loads((ROOT / "tests/fixtures/conversation-archives/expected-proof.json").read_text())
        self.assertEqual(report, expected)
        self.assertEqual(report["knowledge"]["review"], "approved")
        self.assertEqual(report["source_review"], "unreviewed")
        self.assertLessEqual(report["context_bytes"], report["context_max_bytes"])

    def test_demo_refuses_existing_human_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); marker = root / "human.txt"; marker.write_text("Synthetic human-owned data.")
            with self.assertRaisesRegex(ValueError, "new or empty workspace"):
                demo.run_demo(root)
            self.assertEqual(marker.read_text(), "Synthetic human-owned data.")
