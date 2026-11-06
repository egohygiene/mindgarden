"""Append-only private move/merge authority, reference and rollback proofs."""

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.query import QueryContext
from mindgarden.application.routing import snapshots_for
from mindgarden.application.routing_lifecycle import build_transition_plan
from mindgarden.application.retrieval import search_payload
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.routing_transitions import canonical_reference, retired_references
from mindgarden.domain.validation import ContractError
from tests import test_source_adapters as fixtures
from tests.support_v1 import TIME, add_knowledge, create_garden, reference, write_json, write_session


class RoutingLifecycleTests(unittest.TestCase):
    def setUp(self):
        fixtures.SourceAdapterTests.setUp(self)
        imported = fixtures.SourceAdapterTests.plan(self)
        apply_ingestion(imported, imported.digest, self.bindings, "synthetic-vault")
        self.evidence = imported.inputs["normalized_sources"][0]["evidence"]
        self.original = add_knowledge(self.workspace, sources=self.evidence)
        self.original.update(aliases=["Synthetic alias"], tags=["synthetic-tag"])
        write_json(self.workspace / ".garden/knowledge/synthetic-prompt.json", self.original)
        configuration = json.loads(self.configuration.read_text())
        self.destination = self.root / "other-garden"; create_garden(self.destination, "other-garden")
        configuration["gardens"].append({**deepcopy(configuration["gardens"][0]), "id":"other-garden", "root":str(self.destination)})
        write_json(self.configuration, configuration); self.bindings = LocalBindings.load(self.configuration)
        self.request_path = self.root / "transition.json"
        self.request = {"schema":"mindgarden.routing-transition/v1", "id":"synthetic-move", "operation":"move", "created_at":TIME,
            "from":[reference("synthetic-garden", self.original["id"], self.original["content"]["sha256"])],
            "to":reference("other-garden", "moved-prompt"), "review":self.original["review"],
            "authority":{"kind":"human", "id":"synthetic-reviewer"}, "rationale":"Reviewed synthetic private move."}

    def plan(self):
        write_json(self.request_path, self.request)
        return build_transition_plan(self.bindings, self.request_path)

    def test_move_preserves_originals_aliases_and_one_searchable_home(self):
        before = {p:p.read_bytes() for p in (self.workspace / ".garden").rglob("*") if p.is_file()}
        plan = self.plan()
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            self.assertTrue(plan.apply(plan.digest)); self.assertFalse(plan.apply(plan.digest))
            again = self.plan(); self.assertFalse(again.apply(again.digest))
        for path, content in before.items(): self.assertEqual(path.read_bytes(), content)
        snapshots = snapshots_for(self.bindings)
        records = [record for snapshot in snapshots.values() for record in snapshot.records.values()]
        target = canonical_reference(self.request["from"][0], records)
        self.assertEqual(target["garden"], "other-garden")
        self.assertEqual(target["id"], "moved-prompt")
        session = self.root / "session.json"; write_session(session, self.configuration)
        result = search_payload(QueryContext.load(self.configuration, session), "evidence")
        self.assertEqual([r["reference"]["id"] for r in result["results"]], ["moved-prompt"])
        self.assertEqual(result["results"][0]["sources"], self.evidence)
        moved = json.loads((self.destination / ".garden/knowledge/moved-prompt.json").read_text())
        self.assertEqual(moved["aliases"], self.original["aliases"])
        self.assertEqual(moved["tags"], self.original["tags"])
        # A session selecting only the old garden must not resurrect the old home.
        write_session(session, self.configuration, readable_ids=["synthetic-garden"])
        self.assertEqual(search_payload(QueryContext.load(self.configuration, session), "evidence")["results"], [])

    def test_stale_request_and_second_cutover_failure_leave_original_state(self):
        plan = self.plan(); self.request["rationale"] = "Changed review."; write_json(self.request_path, self.request)
        before = {garden:garden_fingerprint(binding["root"]) for garden,binding in self.bindings.gardens.items()}
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"): plan.apply(plan.digest)
        plan = self.plan(); replace = os.replace; selected = 0
        def fail(source, destination):
            nonlocal selected
            if Path(source).name.startswith(".mindgarden-route-stage-") and Path(destination).name == ".garden":
                selected += 1
                if selected == 2: raise OSError("Synthetic second cutover failure")
            return replace(source, destination)
        with patch("os.replace", side_effect=fail):
            with self.assertRaises(OSError): plan.apply(plan.digest)
        self.assertEqual(before, {garden:garden_fingerprint(binding["root"]) for garden,binding in self.bindings.gardens.items()})
        self.assertTrue(plan.apply(plan.digest))

    def test_review_scope_and_complex_transfer_fail_closed(self):
        self.request["authority"] = {"kind":"human", "id":"unrelated-reviewer"}
        with self.assertRaisesRegex(ContractError, "REVIEW_AUTHORITY"): self.plan()
        self.request["authority"]["id"] = "synthetic-reviewer"
        self.request["from"][0]["revision"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"): self.plan()
        self.request["from"][0]["revision"] = "sha256:" + self.original["content"]["sha256"]
        self.request["to"] = deepcopy(self.request["from"][0])
        with self.assertRaisesRegex(ContractError, "ROUTE_TRANSITION_CYCLE"): self.plan()

    def test_merge_requires_reviewed_exact_lineage_before_retirement(self):
        second = add_knowledge(self.workspace, "second-prompt", sources=self.evidence)
        third = add_knowledge(self.workspace, "merged-prompt", sources=self.evidence)
        self.request.update(operation="merge", to=reference("synthetic-garden", third["id"], third["content"]["sha256"]))
        self.request["from"].append(reference("synthetic-garden", second["id"], second["content"]["sha256"]))
        with self.assertRaisesRegex(ContractError, "ROUTE_MERGE_LINEAGE"): self.plan()
        # Produce the accepted target through the authored curation service.
        proposal = json.loads((Path(__file__).parent / "fixtures/curation/authored-plan.json").read_text())
        candidate = next(c for c in proposal["candidates"] if c["action"] == "merge")
        candidate.update(sources=self.evidence, merge_inputs=self.request["from"])
        candidate["output"].update(id="reviewed-merge", claims=[], synapses=[])
        proposal["candidates"] = [candidate]
        path = self.root / "merge-proposal.json"; write_json(path, proposal)
        curated = build_curation_plan(self.bindings, path); apply_curation(curated, curated.digest, self.bindings)
        target = json.loads((self.workspace / ".garden/knowledge/reviewed-merge.json").read_text())
        self.request["to"] = reference("synthetic-garden", target["id"], target["content"]["sha256"])
        plan = self.plan(); self.assertTrue(plan.apply(plan.digest))
        records = [r for s in snapshots_for(self.bindings).values() for r in s.records.values()]
        self.assertEqual(len(retired_references(records)), 2)
        self.assertTrue(all(canonical_reference(ref, records) == self.request["to"] for ref in self.request["from"]))
