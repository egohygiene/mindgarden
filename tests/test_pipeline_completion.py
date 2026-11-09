"""One composed synthetic extraction/review/routing/retrieval/recovery proof."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location(
    "pipeline_completion_demo", ROOT / "scripts/pipeline_completion_demo.py"
)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)
from mindgarden.domain.validation import ContractError


class PipelineCompletionTests(unittest.TestCase):
    def test_combined_offline_pipeline_matches_proof_after_relocation_restore_and_clean_rebuild(
        self,
    ):
        with tempfile.TemporaryDirectory(
            prefix="mindgarden-pipeline-test-"
        ) as temporary:
            report = demo.run_demo(Path(temporary) / "workspace")
        expected = json.loads(
            (ROOT / "tests/fixtures/extraction/pipeline-proof.json").read_bytes()
        )
        self.assertEqual(report, expected)
        self.assertEqual(report["proposal_count"], 8)
        self.assertEqual(report["resume"]["completed_unit_replay"], 0)
        self.assertLessEqual(report["context_bytes"], report["context_max_bytes"])

    def test_occupied_workspace_is_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "human.txt"
            marker.write_text("Retain this synthetic human file.")
            with self.assertRaisesRegex(ValueError, "new or empty"):
                demo.run_demo(root)
            self.assertEqual(marker.read_text(), "Retain this synthetic human file.")

    def test_control_state_is_rejected_inside_git_before_creating_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            (root / ".git/HEAD").write_text("ref: refs/heads/synthetic\n")
            workspace = root / "new-proof"
            with self.assertRaisesRegex(ContractError, "REGISTRY_TRACKED"):
                demo.run_demo(workspace)
            self.assertFalse(workspace.exists())
