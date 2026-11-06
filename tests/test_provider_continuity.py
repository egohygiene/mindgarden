"""Provider recovery, historical dependencies and fail-closed policy regressions."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scripts.provider_switch_demo import retrieve, run_demo
from mindgarden.domain.contracts import canonical_json
from tests.provider_continuity_fixture import FIXTURE, GARDEN, create_fixture
from tests.support_v1 import write_json, write_session


class ProviderContinuityTests(unittest.TestCase):
    def temporary(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        return Path(temporary.name).resolve()

    def test_removed_provider_and_caches_rebuild_exact_structured_context(self):
        root = self.temporary() / "scenario"
        report = run_demo(root)
        self.assertEqual(report, json.loads((FIXTURE / "expected-proof.json").read_bytes()))
        self.assertFalse((root / "disposable-providers/alpha").exists())
        self.assertLessEqual(report["context_bytes"], report["context_max_bytes"])

    def test_historical_claim_supports_current_correction_without_current_ranking(self):
        fixture = create_fixture(self.temporary())
        state = retrieve(fixture)
        selected = {item["reference"]["id"]: item for item in state["context"]["included"]}
        self.assertIn("weekly-review-claim", selected)
        self.assertNotIn("daily-review-claim", selected)
        self.assertIn(fixture["old_claim"]["revision"], selected["review-correction"]["content"])
        self.assertTrue(state["evidence"]["lineage"])

    def test_unreviewed_historical_dependency_still_removes_current_derivatives(self):
        fixture = create_fixture(self.temporary())
        path = fixture["garden"] / ".garden/claims/daily-review-claim.json"
        claim = json.loads(path.read_bytes())
        claim["review"] = {"state": "unreviewed", "reviewers": [], "reviewed_at": None, "rationale": None}
        write_json(path, claim)
        write_session(fixture["session"], fixture["bindings"], readable_ids=[GARDEN], writable=GARDEN)
        # The scoped CLI succeeds but excludes both derivative references. No
        # exception body, missing-reference count or hidden claim is disclosed.
        from scripts.provider_switch_demo import cli_json
        result = cli_json(["context", "--repository-root", str(fixture["garden"]),
            "--local-config", str(fixture["bindings"]), "--scope", str(fixture["session"]), "--pack", "default", "--format", "json"])
        self.assertNotIn("weekly-review-claim", canonical_json(result).decode())
        self.assertNotIn("review-correction", canonical_json(result).decode())
        self.assertNotIn("daily-review-claim", canonical_json(result).decode())

    def test_denied_garden_changes_do_not_change_recovered_state(self):
        fixture = create_fixture(self.temporary())
        before = canonical_json(retrieve(fixture))
        path = fixture["denied"] / ".garden/garden.json"
        path.write_text("Malformed out-of-scope garden; must never be opened.\n")
        self.assertEqual(canonical_json(retrieve(fixture)), before)

    def test_restricted_history_cannot_authorize_a_personal_correction(self):
        from mindgarden.domain.scope import local_scope
        from scripts.provider_switch_demo import cli_json

        fixture = create_fixture(self.temporary())
        path = fixture["garden"] / ".garden/claims/daily-review-claim.json"
        claim = json.loads(path.read_bytes()); claim["scope"] = local_scope("restricted")
        write_json(path, claim)
        write_session(fixture["session"], fixture["bindings"], readable_ids=[GARDEN], writable=GARDEN)
        result = cli_json(["context", "--repository-root", str(fixture["garden"]),
            "--local-config", str(fixture["bindings"]), "--scope", str(fixture["session"]), "--pack", "default", "--format", "json"])
        for denied in ("weekly-review-claim", "review-correction", "daily-review-claim"):
            self.assertNotIn(denied, canonical_json(result).decode())

    def test_revocation_prevents_recovery_from_current_interfaces(self):
        fixture = create_fixture(self.temporary())
        retrieve(fixture, write_index=True)
        document = json.loads(fixture["bindings"].read_bytes())
        document["revoked_sessions"] = [json.loads(fixture["session"].read_bytes())["id"]]
        write_json(fixture["bindings"], document)
        with self.assertRaisesRegex(AssertionError, "Synthetic scoped command failed: index"):
            retrieve(fixture)
