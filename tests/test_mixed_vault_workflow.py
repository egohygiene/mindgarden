"""Dependency-free recorded PDF port in the complete mixed-source recovery golden."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]


class MixedVaultWorkflowTests(unittest.TestCase):
    def test_reviewed_archive_pdf_media_survive_fault_restore_relocation_and_rebuild(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([sys.executable, str(ROOT / "scripts/mixed_vault_demo.py"), "--workspace", temporary,
                                     "--recorded-synthetic-pdf", "--require-source"], cwd=ROOT, text=True,
                                    capture_output=True, check=True, timeout=180)
        expected = json.loads((ROOT / "tests/fixtures/assets/expected-proof.json").read_bytes())
        self.assertEqual(json.loads(result.stdout), expected)
        self.assertEqual(result.stderr, "")
