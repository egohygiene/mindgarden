"""Authored curation dispositions, exact evidence and separate review authority."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import search_payload
from mindgarden.application.records import UNREVIEWED
from mindgarden.domain.contracts import ContractRegistry, digest_bytes
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.support_v1 import add_knowledge, write_json, write_session
from tests import test_source_adapters as source_tests


class CurationTests(unittest.TestCase):
    def setUp(self):
        source_tests.SourceAdapterTests.setUp(self)
        self.input.write_bytes((Path(__file__).parent / "fixtures/curation/source.txt").read_bytes())
        source = source_tests.SourceAdapterTests.plan(self)
        apply_ingestion(source, source.digest, self.bindings, "synthetic-vault")
        self.evidence = source.inputs["normalized_sources"][0]["evidence"]
        self.proposal = json.loads((Path(__file__).parent / "fixtures/curation/authored-plan.json").read_text())
        for name in ("merge-left", "merge-right"):
            record = add_knowledge(self.workspace, name, body="Synthetic merge input " + name + ".\n", sources=self.evidence)
            for candidate in self.proposal["candidates"]:
                for reference in candidate["merge_inputs"]:
                    if reference["id"] == name:
                        reference["revision"] = "sha256:" + record["content"]["sha256"]
        self.proposal_path = self.root / "authored-plan.json"
        write_json(self.proposal_path, self.proposal)

    def test_all_dispositions_preserve_originals_uncertainty_and_contradictions(self):
        original = (self.workspace / ".garden/knowledge/merge-left.md").read_bytes()
        count = len(self.vault.audit()["objects"])
        plan = build_curation_plan(self.bindings, self.proposal_path)
        self.assertEqual(ContractRegistry().errors(plan.document(), "change-plan"), [])
        self.assertTrue(apply_curation(plan, plan.digest, self.bindings))
        self.assertFalse(apply_curation(plan, plan.digest, self.bindings))
        note = json.loads((self.workspace / ".garden/knowledge/reviewed-prompt.json").read_text())
        self.assertEqual(note["authors"][0]["kind"], "agent")
        self.assertEqual(note["review"]["reviewers"], ["synthetic-reviewer"])
        self.assertEqual(note["x-curation"]["epistemic_state"], "proposed")
        self.assertTrue(note["x-curation"]["uncertainty"])
        self.assertEqual((self.workspace / ".garden/knowledge/merge-left.md").read_bytes(), original)
        self.assertEqual(len(self.vault.audit()["objects"]), count)
        receipt = json.loads((self.workspace / ".garden/provenance/curation-synthetic-curation.json").read_text())
        self.assertEqual({item["action"] for item in receipt["decisions"]},
                         {"keep", "summarize", "merge", "reference", "defer", "exclude"})
        self.assertNotIn("Cite exact evidence", json.dumps(receipt))
        session = self.root / "session.json"; write_session(session, self.configuration)
        results = search_payload(QueryContext.load(self.configuration, session), "evidence")
        entry = next(item for item in results["results"] if item["reference"]["id"] == "reviewed-prompt")
        self.assertEqual(entry["qualifications"]["attribution"], "assistant-suggestion")
        self.assertTrue(entry["qualifications"]["caveats"])

    def test_agent_proposals_are_not_promoted_by_apply(self):
        self.proposal["review_authority"] = None
        self.proposal["candidates"] = [self.proposal["candidates"][0]]
        output = self.proposal["candidates"][0]["output"]
        output.update(review=deepcopy(UNREVIEWED), status="proposed", claims=[], synapses=[],
                      body="proposed-only-marker\n")
        write_json(self.proposal_path, self.proposal)
        plan = build_curation_plan(self.bindings, self.proposal_path)
        apply_curation(plan, plan.digest, self.bindings)
        note = json.loads((self.workspace / ".garden/knowledge/reviewed-prompt.json").read_text())
        self.assertEqual(note["review"]["state"], "unreviewed")
        self.assertEqual(note["status"], "proposed")
        session = self.root / "session.json"; write_session(session, self.configuration)
        self.assertEqual(search_payload(QueryContext.load(self.configuration, session), "proposed-only-marker")["results"], [])

    def test_approval_requires_explicit_review_authority(self):
        self.proposal["review_authority"] = None
        write_json(self.proposal_path, self.proposal)
        with self.assertRaisesRegex(ContractError, "REVIEW_AUTHORITY"):
            build_curation_plan(self.bindings, self.proposal_path)

    def test_stale_proposal_or_source_revision_and_conflicts_are_rejected(self):
        plan = build_curation_plan(self.bindings, self.proposal_path)
        before = garden_fingerprint(self.workspace)
        self.proposal["candidates"][0]["rationale"] = "Changed synthetic rationale."
        write_json(self.proposal_path, self.proposal)
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            apply_curation(plan, plan.digest, self.bindings)
        self.assertEqual(garden_fingerprint(self.workspace), before)
        self.proposal["candidates"][0]["sources"][0]["content_sha256"] = "0" * 64
        write_json(self.proposal_path, self.proposal)
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            build_curation_plan(self.bindings, self.proposal_path)

    def test_excluded_content_cannot_be_copied_into_a_disposition(self):
        candidate = deepcopy(self.proposal["candidates"][-1])
        candidate["output"] = self.proposal["candidates"][0]["output"]
        self.proposal["candidates"] = [candidate]
        write_json(self.proposal_path, self.proposal)
        with self.assertRaisesRegex(ContractError, "CURATION_INVALID"):
            build_curation_plan(self.bindings, self.proposal_path)

    def test_preview_refuses_existing_human_content(self):
        path = self.workspace / ".garden/knowledge/reviewed-prompt.md"
        path.write_text("Synthetic existing human edit.\n")
        with self.assertRaisesRegex(ContractError, "PLAN_CONFLICT"):
            build_curation_plan(self.bindings, self.proposal_path)
        self.assertEqual(path.read_text(), "Synthetic existing human edit.\n")

    def test_cli_preview_and_apply_share_the_authored_plan(self):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["gardenize", "--local-config", str(self.configuration),
                                   "--plan", str(self.proposal_path)]), 0)
        digest = json.loads(output.getvalue())["plan_sha256"]
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["gardenize", "--local-config", str(self.configuration),
                                   "--apply", str(self.proposal_path), "--plan-digest", digest]), 0)
