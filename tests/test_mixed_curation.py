"""Authored mixed evidence, later correction, quotation and private destinations."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import LocalBindings
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import render_context, search_payload
from mindgarden.application.routing_lifecycle import build_transition_plan
from mindgarden.domain.contracts import read_object
from mindgarden.domain.validation import ContractError
from tests.journey_fixture import curation_members, mixed_proposal
from tests import test_archive_diagrams as archive_fixture
from tests.support_v1 import TIME, create_garden, reference, write_json, write_session


class MixedCurationTests(unittest.TestCase):
    def setUp(self):
        archive_fixture.ArchiveDiagramTests.setUp(self)
        imported = archive_fixture.ArchiveDiagramTests.plan(self, curation_members())
        apply_ingestion(imported, imported.digest, self.bindings, "synthetic-vault")
        self.proposal = mixed_proposal(imported)
        self.path = self.root / "mixed-review.json"

    def plan(self):
        write_json(self.path, self.proposal)
        return build_curation_plan(self.bindings, self.path)

    def test_mixed_evidence_and_private_exclusion_keep_attribution_and_originals(self):
        blobs = self.vault.audit()
        plan = self.plan()
        self.assertEqual(plan.document(), self.plan().document())
        self.assertTrue(apply_curation(plan, plan.digest, self.bindings))
        self.assertFalse(apply_curation(plan, plan.digest, self.bindings))
        self.assertEqual(self.vault.audit(), blobs)
        root = self.workspace / ".garden"
        prompt = read_object(root / "knowledge/reviewed-prompt.json")
        self.assertEqual(prompt["x-curation"]["attribution"], "mixed")
        self.assertEqual(len(prompt["sources"]), 3)
        self.assertEqual(
            prompt["x-curation"]["contradictions"][0]["id"], "diagram-proposal"
        )
        self.assertTrue(prompt["x-curation"]["redactions"])
        quoted = read_object(root / "knowledge/quoted-statement.json")
        self.assertEqual(quoted["x-curation"]["attribution"], "quoted")
        receipt = read_object(
            root / "provenance/curation-synthetic-mixed-media-review.json"
        )
        self.assertEqual(receipt["decisions"][-1]["action"], "exclude")
        self.assertIsNone(receipt["decisions"][-1]["output"])
        self.assertFalse((root / "knowledge/scratch.json").exists())
        session = self.root / "session.json"
        write_session(session, self.configuration)
        query = QueryContext.load(self.configuration, session)
        result = search_payload(query, "evidence")
        self.assertEqual(result["results"][0]["sources"], prompt["sources"])
        profile = read_object(root / "context-packs/default.json")
        profile.update(query="evidence", max_bytes=8192)
        context = render_context(query, profile, "json")
        self.assertIn(b"reviewed-prompt", context)
        self.assertNotIn(b"ACCOUNT-EXAMPLE", context)
        self.assertNotIn(b"open-question", context)

    def test_agent_cannot_approve_or_apply_after_changed_authored_evidence(self):
        self.proposal["review_authority"] = {
            "kind": "agent", "id": "synthetic-producer", "version": "fixture-1"
        }
        with self.assertRaisesRegex(ContractError, "REVIEW_AUTHORITY"):
            self.plan()
        self.proposal["review_authority"] = {
            "kind": "human", "id": "synthetic-reviewer"
        }
        plan = self.plan()
        changed = deepcopy(self.proposal)
        changed["candidates"][0]["rationale"] = "Changed review request."
        write_json(self.path, changed)
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            apply_curation(plan, plan.digest, self.bindings)
        self.assertFalse((self.workspace / ".garden/knowledge/reviewed-prompt.json").exists())

    def test_reviewed_destinations_share_evidence_without_copying_raw_archive(self):
        plan = self.plan()
        apply_curation(plan, plan.digest, self.bindings)
        config = read_object(self.configuration)
        destination = self.root / "project-garden"
        create_garden(destination, "project-garden")
        config["gardens"].append(
            {
                **deepcopy(config["gardens"][0]),
                "id": "project-garden",
                "root": str(destination),
            }
        )
        write_json(self.configuration, config)
        bindings = LocalBindings.load(self.configuration)
        original = read_object(self.workspace / ".garden/knowledge/diagram-proposal.json")
        before = self.vault.audit()
        request = {
            "schema": "mindgarden.routing-transition/v1",
            "id": "diagram-destination",
            "operation": "move",
            "created_at": TIME,
            "from": [
                reference("synthetic-garden", original["id"], original["content"]["sha256"])
            ],
            "to": reference("project-garden", "architecture-diagram"),
            "review": original["review"],
            "authority": self.proposal["review_authority"],
            "rationale": "Reviewed diagram home; prompt stays in the personal garden.",
        }
        path = self.root / "destination.json"
        write_json(path, request)
        move = build_transition_plan(bindings, path)
        move.apply(move.digest)
        placed = read_object(destination / ".garden/knowledge/architecture-diagram.json")
        self.assertEqual(placed["sources"], original["sources"])
        self.assertEqual(self.vault.audit(), before)
        self.assertFalse(list((destination / ".garden/sources").glob("*.json")))
        self.assertTrue((self.workspace / ".garden/knowledge/reviewed-prompt.json").exists())
