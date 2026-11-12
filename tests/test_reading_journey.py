"""Committed synthetic acceptance golden, with all external entry points blocked."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).parents[1]


def demo():
    spec = importlib.util.spec_from_file_location(
        "synthetic_reading_journey", ROOT / "scripts/reading_journey_demo.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReadingJourneyTests(unittest.TestCase):
    def test_synthetic_archive_to_reviewed_context_and_clean_recovery_matches_golden(
        self,
    ):
        with TemporaryDirectory() as directory:
            report = demo().run_demo(Path(directory) / "journey")
        expected = json.loads(
            (
                ROOT / "tests/fixtures/conversation-archives/reading-journey-proof.json"
            ).read_bytes()
        )
        self.assertEqual(report, expected)

    def test_occupied_workspace_is_preserved_before_initialization(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "synthetic-human-file.txt"
            original = b"Retain this supplied synthetic content.\n"
            marker.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "new or empty"):
                demo().run_demo(root)
            self.assertEqual(marker.read_bytes(), original)
            self.assertEqual(list(root.iterdir()), [marker])
