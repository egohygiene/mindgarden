"""Move previews preserve and inventory independently reviewed incoming references."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.routing_lifecycle import build_transition_plan
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from tests import test_routing_lifecycle as fixture
from tests.support_v1 import FIXTURES, add_knowledge, reference, write_json


class IncomingRoutingTests(unittest.TestCase):
    def setUp(self):
        fixture.RoutingLifecycleTests.setUp(self)
        self.owner = add_knowledge(
            self.workspace, "incoming-owner", sources=self.evidence
        )
        self.edge = json.loads((FIXTURES / "synapse.json").read_bytes())
        self.edge.update(
            garden="synthetic-garden",
            id="incoming-edge",
            type="references",
            directed=True,
            source=reference(
                "synthetic-garden", self.owner["id"], self.owner["content"]["sha256"]
            ),
            target=self.request["from"][0],
            scope=local_scope(),
            visibility="private",
            review=self.original["review"],
            evidence=self.evidence,
            status="active",
        )
        self.edge_path = self.workspace / ".garden/synapses/incoming-edge.json"
        self.write_edge()

    def write_edge(self):
        write_json(self.edge_path, self.edge)
        self.owner["synapses"] = [
            reference(
                "synthetic-garden",
                self.edge["id"],
                digest_bytes(canonical_json(self.edge)),
            )
        ]
        write_json(self.workspace / ".garden/knowledge/incoming-owner.json", self.owner)

    def plan(self):
        write_json(self.request_path, self.request)
        return build_transition_plan(self.bindings, self.request_path)

    def test_move_inventory_is_exact_deterministic_and_does_not_retarget_original(self):
        plan = self.plan()
        self.assertEqual(plan.document(), self.plan().document())
        (item,) = plan.decisions[0]["incoming_references"]
        self.assertEqual(
            item["reference"]["revision"],
            "sha256:" + digest_bytes(self.edge_path.read_bytes()),
        )
        self.assertEqual(item["historical_target"], self.request["from"][0])
        self.assertEqual(
            item["proposed_canonical_target"], plan.decisions[0]["canonical_home"]
        )
        self.assertEqual(item["state"], "separate-reviewed-reference-repair-required")
        before = self.edge_path.read_bytes()
        owner = (self.workspace / ".garden/knowledge/incoming-owner.json").read_bytes()
        self.assertTrue(plan.apply(plan.digest))
        self.assertEqual(self.edge_path.read_bytes(), before)
        self.assertEqual(
            (self.workspace / ".garden/knowledge/incoming-owner.json").read_bytes(),
            owner,
        )
        self.assertFalse(plan.apply(plan.digest))

    def test_unreviewed_and_inactive_edges_are_not_disclosed_in_move_explanations(self):
        for field, value in (
            (
                "review",
                {
                    "state": "unreviewed",
                    "reviewers": [],
                    "reviewed_at": None,
                    "rationale": None,
                },
            ),
            ("status", "deprecated"),
        ):
            original = deepcopy(self.edge)
            self.edge[field] = value
            self.write_edge()
            self.assertNotIn("incoming_references", self.plan().decisions[0])
            self.edge = original
            self.write_edge()

    def test_edge_change_invalidates_whole_transition_before_any_output(self):
        plan = self.plan()
        self.edge["confidence"] = (
            "low" if self.edge["confidence"] != "low" else "unknown"
        )
        self.write_edge()
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            plan.apply(plan.digest)
        self.assertFalse(
            (self.destination / ".garden/knowledge/moved-prompt.json").exists()
        )
        revised = self.plan()
        self.assertNotEqual(revised.digest, plan.digest)
        self.assertTrue(revised.apply(revised.digest))

    def test_unpinned_and_undirected_incoming_references_keep_their_original_form(self):
        self.edge.update(
            directed=False, target={**self.request["from"][0], "revision": None}
        )
        self.write_edge()
        (item,) = self.plan().decisions[0]["incoming_references"]
        self.assertFalse(item["directed"])
        self.assertIsNone(item["historical_target"]["revision"])

    def test_stricter_edges_and_unreviewed_sources_are_omitted_without_counts(self):
        self.edge["scope"] = local_scope("restricted")
        self.write_edge()
        self.assertNotIn("incoming_references", self.plan().decisions[0])
        self.edge["scope"] = local_scope()
        self.write_edge()
        self.owner["review"] = {
            "state": "unreviewed",
            "reviewers": [],
            "reviewed_at": None,
            "rationale": None,
        }
        self.write_edge()
        self.assertNotIn("incoming_references", self.plan().decisions[0])

    def test_incoming_inventory_is_bounded_before_any_canonical_write(self):
        for number in range(128):
            owner = add_knowledge(
                self.workspace, "owner-extra-" + str(number), sources=self.evidence
            )
            record = {**self.edge, "id": "incoming-extra-" + str(number)}
            record["source"] = reference(
                "synthetic-garden", owner["id"], owner["content"]["sha256"]
            )
            write_json(
                self.workspace / ".garden/synapses" / (record["id"] + ".json"), record
            )
        with self.assertRaisesRegex(ContractError, "ROUTE_INCOMING_BUDGET"):
            self.plan()
        self.assertFalse(
            (self.destination / ".garden/knowledge/moved-prompt.json").exists()
        )
