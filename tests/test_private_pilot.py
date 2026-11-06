"""Synthetic private-pilot plans: authority, stale inputs, retention and safe reports."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scripts import private_pilot
from mindgarden.domain.contracts import canonical_json, digest_bytes
from tests.archive_fixture import package_bytes, package_members


class PrivatePilotTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.archive = self.root / "private-filename-canary.zip"
        self.archive.write_bytes(package_bytes(package_members()))
        self.workspace = self.root / "pilot"

    def plan(self, **extra):
        return private_pilot.plan(self.archive, self.workspace, classification="personal", manifest_version="3.2.3",
            owner="synthetic-owner", captured_at="2026-11-04T00:00:00Z", expires_at="2099-01-01T00:00:00Z", **extra)

    def test_unknown_or_restricted_scope_is_denied_before_source_access(self):
        with patch("scripts.private_pilot.captured_bytes", side_effect=AssertionError("Unclassified source was read")):
            with self.assertRaisesRegex(private_pilot.PilotError, "PILOT_RUNTIME_UNAVAILABLE"):
                private_pilot.plan(self.archive, self.workspace, classification="restricted", manifest_version="3.2.3",
                    owner="synthetic-owner", captured_at="2026-11-04T00:00:00Z")
        self.assertFalse(self.workspace.exists())

    def test_source_changes_invalidate_reviewed_plan_without_writes(self):
        document = self.plan(); reviewed = digest_bytes(canonical_json(document))
        self.archive.write_bytes(self.archive.read_bytes() + b"changed")
        with self.assertRaisesRegex(private_pilot.PilotError, "PILOT_PLAN_STALE"):
            private_pilot.apply(document, reviewed)
        self.assertFalse(self.workspace.exists())

    def test_existing_unowned_workspace_is_preserved(self):
        self.workspace.mkdir(mode=0o700); marker = self.workspace / "human.txt"; marker.write_text("Synthetic human data")
        with self.assertRaisesRegex(private_pilot.PilotError, "PILOT_OWNERSHIP"): self.plan()
        self.assertEqual(marker.read_text(), "Synthetic human data")

    def test_normalization_repeat_preserves_original_and_emits_only_safe_report(self):
        before = self.archive.read_bytes(); document = self.plan(); reviewed = digest_bytes(canonical_json(document))
        report = private_pilot.apply(document, reviewed)
        self.assertEqual(private_pilot.apply(document, reviewed), report)
        self.assertEqual(self.archive.read_bytes(), before)
        self.assertEqual(report["status"], "partial-awaiting-reviewed-knowledge")
        for private in (str(self.root), self.archive.name, digest_bytes(before), "synthetic-malicious-command"):
            self.assertNotIn(private, canonical_json(report).decode())
        self.assertEqual(report["report_review"], "private-until-owner-approves-sharing")

    def test_changed_proposal_is_not_authorized_by_an_older_completion_receipt(self):
        proposal = self.root / "proposal.json"; proposal.write_text('{}\n')
        original = self.plan(proposal=proposal)
        reviewed = digest_bytes(canonical_json(original))
        modified = deepcopy(original); modified["before"] = "after-digest"
        modified["proposal_sha256"] = "0" * 64
        with patch("scripts.private_pilot.plan", return_value=modified), \
                patch("scripts.private_pilot.state", return_value=({"receipts": {reviewed: {"after": "after-digest"}}}, "after-digest")):
            with self.assertRaisesRegex(private_pilot.PilotError, "PILOT_PLAN_STALE"):
                private_pilot.apply(original, reviewed)
