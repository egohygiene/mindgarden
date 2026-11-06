"""Authored redactions and exact merge/relationship attribution regression cases."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.validation import ContractError
from tests import test_curation as fixtures
from tests.support_v1 import write_json


class CurationTransformationTests(unittest.TestCase):
    def setUp(self):
        fixtures.CurationTests.setUp(self)

    def plan(self):
        write_json(self.proposal_path, self.proposal)
        return build_curation_plan(self.bindings, self.proposal_path)

    def test_merge_retains_authors_attribution_and_qualifications(self):
        path = self.workspace / ".garden/knowledge/merge-left.json"
        previous = json.loads(path.read_text())
        previous["x-curation"] = {"attribution": "user-statement", "epistemic_state": "open-question",
            "caveats": ["Preserve the original caveat."], "uncertainty": ["A question remains unanswered."], "contradictions": []}
        write_json(path, previous)
        original = path.read_bytes()
        candidate = next(c for c in self.proposal["candidates"] if c["action"] == "merge")
        candidate["output"]["attribution"] = "assistant-suggestion"
        self.proposal["candidates"] = [candidate]
        plan = self.plan(); apply_curation(plan, plan.digest, self.bindings)
        result = json.loads((self.workspace / ".garden/knowledge/merged-note.json").read_text())
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(result["x-curation"]["attribution"], "mixed")
        self.assertIn("Preserve the original caveat.", result["x-curation"]["caveats"])
        self.assertIn("A question remains unanswered.", result["x-curation"]["uncertainty"])
        self.assertEqual(result["x-curation"]["inherited_attribution"][0]["epistemic_state"], "open-question")
        self.assertTrue(all(author in result["authors"] for author in previous["authors"]))

    def test_duplicate_merge_input_does_not_count_as_two_sources(self):
        candidate = next(c for c in self.proposal["candidates"] if c["action"] == "merge")
        candidate["merge_inputs"][1] = deepcopy(candidate["merge_inputs"][0])
        self.proposal["candidates"] = [candidate]
        with self.assertRaisesRegex(ContractError, "CURATION_DUPLICATE"):
            self.plan()

    def test_existing_relationship_and_supersession_require_exact_revisions(self):
        candidate = self.proposal["candidates"][0]
        candidate["output"]["synapses"] = []
        self.proposal["candidates"] = [candidate]
        for revision in (None, "sha256:" + "0" * 64):
            candidate["output"]["supersedes"] = [{"garden": "synthetic-garden", "id": "merge-left", "revision": revision}]
            with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
                self.plan()
        content = (self.workspace / ".garden/knowledge/merge-left.md").read_bytes()
        candidate["output"]["supersedes"][0]["revision"] = "sha256:" + digest_bytes(content)
        self.plan()

    def test_claim_cannot_import_unselected_evidence(self):
        candidate = self.proposal["candidates"][0]
        candidate["output"]["claims"][0]["evidence"][0]["target"]["locator"] = "lines:1-1"
        with self.assertRaisesRegex(ContractError, "CURATION_EVIDENCE_SELECTION"):
            self.plan()

    def test_redaction_is_authored_evidence_bound_and_preserves_originals(self):
        candidate = self.proposal["candidates"][0]
        candidate["output"].update(body="A redacted synthetic summary.\n", claims=[], synapses=[],
            redactions=[{"source": deepcopy(candidate["sources"][0]), "rationale": "Omit a synthetic personal detail from this derivative."}])
        self.proposal["candidates"] = [candidate]
        before = len(self.vault.audit()["objects"])
        plan = self.plan(); apply_curation(plan, plan.digest, self.bindings)
        result = json.loads((self.workspace / ".garden/knowledge/reviewed-prompt.json").read_text())
        self.assertEqual(result["x-curation"]["redactions"], candidate["output"]["redactions"])
        self.assertEqual(len(self.vault.audit()["objects"]), before)
        self.assertEqual(result["scope"]["visibility"], "personal")
        provenance = json.loads((self.workspace / ".garden/provenance/provenance-reviewed-prompt.json").read_text())
        self.assertEqual(provenance["transformations"][0]["parameters"]["redactions"], candidate["output"]["redactions"])
