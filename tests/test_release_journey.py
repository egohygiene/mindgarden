"""Composed synthetic archive/private routing and reviewed-public branch evidence."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scripts.release_journey_demo import run_demo


class ReleaseJourneyTests(unittest.TestCase):
    def test_archive_to_private_fallback_and_separate_public_source_match_golden(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_demo(Path(directory).resolve() / "journey")
        self.assertEqual(report, json.loads((ROOT / "tests/fixtures/release-journey/expected-proof.json").read_bytes()))
        self.assertEqual(report["routing"]["private"], "private-fallback")
        self.assertEqual(report["federation"]["visibility"], "public")
        self.assertLessEqual(report["public_context_bytes"], report["public_context_budget"])

    def test_existing_human_workspace_is_not_used_for_a_synthetic_journey(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); marker = root / "human.txt"; marker.write_text("Retain synthetic human file")
            with self.assertRaisesRegex(ValueError, "new or empty"): run_demo(root)
            self.assertEqual(marker.read_text(), "Retain synthetic human file")
