"""Authored compaction preserves exact evidence, authority and selective invalidation."""

from contextlib import redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.compaction import preview_compaction
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.evidence import resolve_evidence
from mindgarden.application.query import QueryContext
from mindgarden.application.records import UNREVIEWED
from mindgarden.application.retrieval import render_context, search_payload
from mindgarden.application.storage import open_vault
from mindgarden.domain.compaction import evaluate_compaction, invalidated_nodes, node_sources
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.compaction_fixture import FIXTURES, create_fixture
from tests.support_v1 import write_json, write_session
from tests import test_v1_contracts as contract_tests


class CompactionTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root)
        self.context = self.fixture["context"]
        self.plan = self.fixture["plan"]
        self.curation = self.fixture["curation"]

    def preview(self, plan=None, curation=None):
        return preview_compaction(self.context, plan or self.plan, curation=self.curation if curation is None else curation)

    def evidence(self):
        citations = {canonical_json(citation): citation for node in self.plan["nodes"] for citation in node_sources(node)}
        return {key: resolve_evidence(self.context, **citation) for key, citation in citations.items()}

    def test_contracts_reference_parity_and_read_only_provenance_qualifications(self):
        before = garden_fingerprint(self.fixture["garden"])
        with patch("socket.socket", side_effect=AssertionError("Network attempted")), patch("subprocess.run", side_effect=AssertionError("Model/process attempted")):
            report = self.preview()
        self.assertEqual(before, garden_fingerprint(self.fixture["garden"]))
        self.assertEqual(self.plan["retention"], json.loads((FIXTURES / "retention-policy.json").read_text()))
        contract_tests.V1ContractTests.setUpClass(); reference = contract_tests.V1ContractTests()
        for name, document in (("retention-policy", self.plan["retention"]), ("compaction-plan", self.plan), ("compaction-manifest", report["manifest"])):
            self.assertEqual(ContractRegistry().errors(document, name), [])
            self.assertEqual(list(reference.validator(name).iter_errors(document)), [])
        self.assertEqual(report["metrics"]["exact_citations_verified"], 2)
        self.assertEqual(report["classification"], "machine-local-control")
        self.assertEqual(report["publication"], "never-exportable")
        self.assertTrue(all(item["trust"] == "untrusted-evidence" and item["origin"]["speaker"] == "assistant" for item in report["evidence"]))
        self.assertEqual({item["origin"]["original_selector"]["json_pointer"] for item in report["evidence"]}, {"/messages/1", "/messages/2"})
        self.assertTrue(all(item["source_review"]["state"] == "unreviewed" for item in report["evidence"]))
        self.assertNotIn("synthetic-malicious-command", json.dumps(report))

    def test_existing_reviewed_curation_applies_exact_handoff_and_preserves_originals(self):
        self.preview()
        original = self.fixture["archive"].read_bytes()
        old = (self.fixture["garden"] / ".garden/knowledge/reviewed-prompt.json").read_bytes()
        vault = open_vault(self.context.bindings, "synthetic-vault"); inventory = vault.export_bundle()
        plan = build_curation_plan(self.context.bindings, FIXTURES / "curation.json")
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"): apply_curation(plan, "0" * 64, self.context.bindings)
        self.assertTrue(apply_curation(plan, plan.digest, self.context.bindings))
        self.assertFalse(apply_curation(plan, plan.digest, self.context.bindings))
        self.assertEqual(original, self.fixture["archive"].read_bytes()); self.assertEqual(inventory, vault.export_bundle())
        self.assertEqual(old, (self.fixture["garden"] / ".garden/knowledge/reviewed-prompt.json").read_bytes())
        write_session(self.fixture["session_path"], self.fixture["configuration"])
        context = QueryContext.load(self.fixture["configuration"], self.fixture["session_path"])
        entry = next(item for item in search_payload(context, "evidence")["results"] if item["reference"]["id"] == "compacted-prompt")
        self.assertEqual(len(entry["sources"]), 2); self.assertTrue(entry["qualifications"]["uncertainty"])
        profile = {"schema": "mindgarden.context-profile/v1", "id": "compaction-proof", "garden": "synthetic-garden", "title": "Synthetic context",
                   "description": "Authored compacted knowledge", "query": "evidence", "include": [entry["reference"]], "exclude": [], "kinds": [],
                   "max_items": 1, "max_bytes": 8192, "max_candidates": 10}
        packed = render_context(context, profile, "json")
        self.assertLessEqual(len(packed), 8192)
        self.assertEqual(json.loads(packed)["included"][0]["reference"], entry["reference"])
        self.assertNotIn(b"synthetic-malicious-command", packed)

    def test_unreviewed_proposals_remain_unreviewed_and_cannot_grant_approval(self):
        proposal = deepcopy(self.curation); proposal["review_authority"] = None
        with self.assertRaisesRegex(ContractError, "REVIEW_AUTHORITY"):
            plan = deepcopy(self.plan); plan["curation_plan_sha256"] = digest_bytes(canonical_json(proposal)); self.preview(plan, proposal)
        proposal["candidates"][0]["output"].update(review=deepcopy(UNREVIEWED), status="proposed")
        plan = deepcopy(self.plan); plan["curation_plan_sha256"] = digest_bytes(canonical_json(proposal))
        self.assertEqual(self.preview(plan, proposal)["curation"][0]["review_state"], "unreviewed")
        path = self.root / "unreviewed-curation.json"; write_json(path, proposal)
        change = build_curation_plan(self.context.bindings, path); apply_curation(change, change.digest, self.context.bindings)
        record = json.loads((self.fixture["garden"] / ".garden/knowledge/compacted-prompt.json").read_text())
        self.assertEqual(record["review"]["state"], "unreviewed")

    def test_unknown_policy_destructive_modes_public_downgrade_and_budgets_fail(self):
        cases = []
        plan = deepcopy(self.plan); plan["retention"]["policy"]["revision"] = "sha256:" + "0" * 64; cases.append((plan, "POLICY_UNSUPPORTED"))
        plan = deepcopy(self.plan); plan["retention"]["archival"]["deletion"] = "delete-after-summary"; cases.append((plan, "COMPACTION_INVALID"))
        plan = deepcopy(self.plan); plan["budget_profile"] = "publishing"; cases.append((plan, "COMPACTION_PUBLICATION"))
        plan = deepcopy(self.plan); plan["retention"]["detail_budgets"]["personal"]["max_statements"] = 1; cases.append((plan, "COMPACTION_BUDGET"))
        for plan, code in cases:
            with self.subTest(code=code), self.assertRaisesRegex(ContractError, code): self.preview(plan)

    def test_cycles_dangling_links_and_missing_qualifications_fail_before_output(self):
        evidence = self.evidence()
        for change, code in (("cycle", "COMPACTION_CYCLE"), ("dangling", "COMPACTION_RELATIONSHIP"), ("uncertainty", "COMPACTION_UNCERTAINTY"),
                             ("contradiction", "COMPACTION_CONTRADICTION"), ("validity", "COMPACTION_VALIDITY"),
                             ("attribution", "COMPACTION_ATTRIBUTION"), ("epistemic", "COMPACTION_EPISTEMIC"),
                             ("state-loss", "COMPACTION_VALIDITY")):
            plan = deepcopy(self.plan); node = next(item for item in plan["nodes"] if item["id"] == "summary-prompt")
            if change == "cycle": node["inputs"] = ["summary-prompt"]
            if change == "dangling": node["inputs"] = ["missing-node"]
            if change == "uncertainty": node["statements"][0]["uncertainty"] = ["Other uncertain detail."]
            if change == "contradiction":
                node = next(item for item in plan["nodes"] if item["id"] == "summary-alternative")
                node["statements"][0]["contradictions"] = []; node["statements"][0]["validity"]["state"] = "unknown"
            if change == "validity": node["statements"][0]["validity"]["state"] = "current"; node["statements"][0]["validity"]["valid_until"] = "2020-01-01"
            if change == "attribution": node["statements"][0]["attribution"] = "user-report"
            if change == "epistemic": node["statements"][0]["epistemic_state"] = "decided"
            if change == "state-loss":
                node = next(item for item in plan["nodes"] if item["id"] == "summary-alternative")
                node["statements"][0]["validity"]["state"] = "unknown"
            with self.subTest(change=change), self.assertRaisesRegex(ContractError, code): evaluate_compaction(plan, evidence)

    def test_changed_evidence_invalidates_only_affected_branch_and_descendants(self):
        evidence = self.evidence(); before = evaluate_compaction(self.plan, evidence)["manifest"]
        self.assertEqual(invalidated_nodes(before, before), [])
        plan = deepcopy(self.plan)
        original = next(node for node in plan["nodes"] if node["id"] == "segment-prompt")["statements"][0]["evidence"][0]
        replacement = deepcopy(original); replacement["source"]["revision"] = "sha256:" + digest_bytes(b"Synthetic revised source wrapper")
        replacement["content_sha256"] = digest_bytes(b"New exact evidence wording.")
        payload = deepcopy(evidence.pop(canonical_json(original))); payload.update(text="New exact evidence wording.", **replacement)
        evidence[canonical_json(replacement)] = payload
        for node in plan["nodes"]:
            for statement in node["statements"]:
                statement["evidence"] = [deepcopy(replacement) if citation == original else citation for citation in statement["evidence"]]
                if node["layer"] == "normalized-segment" and statement["evidence"] == [replacement]: statement["text"] = payload["text"]
        after = evaluate_compaction(plan, evidence)["manifest"]
        invalidated = invalidated_nodes(before, after)
        self.assertIn("bounded-context", invalidated); self.assertIn("publication-proposal", invalidated)
        self.assertNotIn("segment-alternative", invalidated); self.assertNotIn("summary-alternative", invalidated)
        self.assertNotIn("deferred-alternative", invalidated)
        plan = deepcopy(self.plan); plan["retention"]["model_context"]["ttl_seconds"] = 300
        policy_change = evaluate_compaction(plan, self.evidence())["manifest"]
        self.assertEqual(invalidated_nodes(before, policy_change), ["bounded-context", "publication-proposal"])

    def test_stale_curation_hash_removed_qualifications_and_corrupt_sources_are_denied(self):
        proposal = deepcopy(self.curation); proposal["candidates"][0]["output"]["body"] = "Changed output\n"
        with self.assertRaisesRegex(ContractError, "COMPACTION_CURATION"): self.preview(curation=proposal)
        proposal = deepcopy(self.curation); proposal["candidates"][0]["output"]["uncertainty"] = []
        plan = deepcopy(self.plan); plan["curation_plan_sha256"] = digest_bytes(canonical_json(proposal))
        with self.assertRaisesRegex(ContractError, "COMPACTION_CURATION"): self.preview(plan, proposal)
        citation = self.plan["nodes"][0]["statements"][0]["evidence"][0]
        digest = citation["source"]["revision"].removeprefix("sha256:")
        blob = self.root / "vault/objects/sha256" / digest[:2] / digest
        blob.chmod(0o600)
        blob.write_bytes(b"Synthetic modified normalized bytes")
        with self.assertRaisesRegex(ContractError, "QUERY_INTEGRITY"): self.preview()

    def test_cli_preview_is_read_only_and_matches_application_service(self):
        plan = self.root / "compaction.json"; write_json(plan, self.plan)
        before = garden_fingerprint(self.fixture["garden"])
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["compaction", "preview", "--input", str(plan), "--curation-plan", str(FIXTURES / "curation.json"),
                                   "--local-config", str(self.fixture["configuration"]), "--scope", str(self.fixture["session_path"])]), 0)
        self.assertEqual(json.loads(output.getvalue()), self.preview())
        self.assertEqual(before, garden_fingerprint(self.fixture["garden"]))

    def test_denied_exact_citation_cannot_open_unselected_sources(self):
        plan = deepcopy(self.plan)
        plan["nodes"][0]["statements"][0]["evidence"][0]["source"]["garden"] = "denied-garden-canary"
        with self.assertRaisesRegex(ContractError, "EVIDENCE_UNAVAILABLE") as error:
            self.preview(plan)
        self.assertNotIn("canary", str(error.exception))

    def test_clean_synthetic_proof_matches_golden_and_preserves_occupied_workspace(self):
        specification = importlib.util.spec_from_file_location("synthetic_compaction_demo", Path(__file__).parents[1] / "scripts/compaction_demo.py")
        demo = importlib.util.module_from_spec(specification); specification.loader.exec_module(demo)
        report = demo.run_demo(self.root / "proof")
        self.assertEqual(report, json.loads((FIXTURES / "expected-proof.json").read_text()))
        with self.assertRaisesRegex(ValueError, "new or empty"): demo.run_demo(self.root / "proof")


if __name__ == "__main__":
    unittest.main()
