"""Exact private relationship review, append-only history and retry behavior."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.query import QueryContext
from mindgarden.application.reference_repairs import build_reference_repair_plan
from mindgarden.application.retrieval import build_index
from mindgarden.application.routing import snapshots_for
from mindgarden.application.routing_lifecycle import build_transition_plan
from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_routing_incoming as fixture
from tests.support_v1 import TIME, add_knowledge, reference, write_json, write_session


class ReferenceRepairTests(unittest.TestCase):
    write_edge = fixture.IncomingRoutingTests.write_edge

    def setUp(self):
        fixture.IncomingRoutingTests.setUp(self)
        write_json(self.request_path, self.request)
        move = build_transition_plan(self.bindings, self.request_path)
        incoming = move.decisions[0]["incoming_references"][0]
        move.apply(move.digest)
        self.repair_path = self.root / "repair.json"
        self.repair = {
            "schema": "mindgarden.reference-repair/v1",
            "id": "synthetic-repair",
            "created_at": TIME,
            "review": self.original["review"],
            "authority": {"kind": "human", "id": "synthetic-reviewer"},
            "repairs": [
                {
                    "edge": incoming["reference"],
                    "source": incoming["source"],
                    "historical_target": incoming["historical_target"],
                    "canonical_target": incoming["proposed_canonical_target"],
                    "replacement_id": "repaired-edge",
                    "rationale": "Human reviewed this exact reference after the move.",
                }
            ],
        }

    def plan(self):
        write_json(self.repair_path, self.repair)
        return build_reference_repair_plan(self.bindings, self.repair_path)

    def index(self):
        session = self.root / "session.json"
        write_session(session, self.configuration)
        return build_index(QueryContext.load(self.configuration, session))

    def test_repair_is_reviewed_deterministic_and_keeps_originals(self):
        original = self.edge_path.read_bytes()
        owner_path = self.workspace / ".garden/knowledge/incoming-owner.json"
        owner = owner_path.read_bytes()
        blobs = self.vault.audit()
        self.assertEqual(self.index()["edges"], [])
        plan = self.plan()
        self.assertEqual(plan.document(), self.plan().document())
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            self.assertTrue(plan.apply(plan.digest))
            self.assertFalse(plan.apply(plan.digest))
        self.assertEqual(self.edge_path.read_bytes(), original)
        self.assertEqual(owner_path.read_bytes(), owner)
        self.assertEqual(self.vault.audit(), blobs)
        repaired = read_object(self.workspace / ".garden/synapses/repaired-edge.json")
        self.assertEqual(repaired["evidence"], self.edge["evidence"])
        self.assertEqual(repaired["authors"], self.edge["authors"])
        (edge,) = self.index()["edges"]
        self.assertEqual(edge["target"], "other-garden/moved-prompt")
        self.assertEqual(edge["source"], "synthetic-garden/incoming-owner")

    def test_explicit_authority_and_target_are_required(self):
        self.repair["authority"]["id"] = "unrelated-reviewer"
        with self.assertRaisesRegex(ContractError, "REVIEW_AUTHORITY"):
            self.plan()
        self.repair["authority"]["id"] = "synthetic-reviewer"
        self.repair["repairs"][0]["canonical_target"] = self.repair["repairs"][0][
            "source"
        ]
        with self.assertRaisesRegex(ContractError, "ROUTE_REPAIR_TARGET"):
            self.plan()

    def test_changed_request_or_target_invalidates_apply(self):
        plan = self.plan()
        write_json(self.repair_path, {**self.repair, "id": "changed-request"})
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            plan.apply(plan.digest)
        plan = self.plan()
        target = self.destination / ".garden/knowledge/moved-prompt.json"
        record = read_object(target)
        record["title"] = "Changed target metadata"
        write_json(target, record)
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            plan.apply(plan.digest)
        self.assertFalse(
            (self.workspace / ".garden/synapses/repaired-edge.json").exists()
        )

    def test_duplicate_selection_and_conflicting_repair_are_rejected(self):
        self.repair["repairs"] *= 2
        with self.assertRaisesRegex(ContractError, "ROUTE_REPAIR_DUPLICATE"):
            self.plan()
        self.repair["repairs"] = self.repair["repairs"][:1]
        plan = self.plan()
        plan.apply(plan.digest)
        self.repair["id"] = "another-repair"
        with self.assertRaisesRegex(ContractError, "ROUTE_REPAIR_CONFLICT"):
            self.plan()

    def test_failed_selection_rolls_back_and_same_plan_retries(self):
        plan = self.plan()
        before = garden_fingerprint(self.workspace)
        replace = os.replace

        def fail_stage(source, destination):
            if Path(source).name.startswith(".mindgarden-route-stage-"):
                raise OSError("Synthetic private cutover failure")
            return replace(source, destination)

        with patch(
            "mindgarden.application.transactions.os.replace", side_effect=fail_stage
        ):
            with self.assertRaises(OSError):
                plan.apply(plan.digest)
        self.assertEqual(garden_fingerprint(self.workspace), before)
        self.assertTrue(plan.apply(plan.digest))

    def test_changed_review_event_fails_validation_and_live_session(self):
        plan = self.plan()
        plan.apply(plan.digest)
        session = self.root / "session.json"
        write_session(session, self.configuration)
        query = QueryContext.load(self.configuration, session)
        path = next(
            (self.workspace / ".garden/provenance").glob("reference-repair-*.json")
        )
        record = read_object(path)
        record["x-reference-repair"]["rationale"] = "Unreviewed change"
        write_json(path, record)
        with self.assertRaisesRegex(ContractError, "ROUTE_REPAIR_INVALID"):
            snapshots_for(self.bindings)
        with self.assertRaisesRegex(
            ContractError, "ROUTE_REPAIR_INVALID|SESSION_REVISION|QUERY_INTEGRITY"
        ):
            build_index(query)

    def test_cli_preview_and_apply_use_the_exact_digest(self):
        plan = self.plan()
        args = [
            "route",
            "--local-config",
            str(self.configuration),
            "--reference-repair",
            str(self.repair_path),
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(args + ["--plan"]), 0)
        self.assertEqual(read_object(self.repair_path), self.repair)
        self.assertIn(plan.digest, output.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(args + ["--apply", "--plan-digest", plan.digest]), 0)

    def test_repaired_history_survives_a_later_successor_move(self):
        plan = self.plan()
        plan.apply(plan.digest)
        request = deepcopy(self.request)
        request.update(
            id="second-move",
            **{
                "from": [self.repair["repairs"][0]["canonical_target"]],
                "to": reference("other-garden", "moved-again"),
            },
        )
        write_json(self.request_path, request)
        later = build_transition_plan(self.bindings, self.request_path)
        later.apply(later.digest)
        snapshots_for(self.bindings)
        self.assertEqual(self.index()["edges"], [])

    def test_matching_personal_policy_is_required(self):
        config = read_object(self.configuration)
        config["gardens"][1]["scope"]["publication"] = "never-exportable"
        write_json(self.configuration, config)
        from mindgarden.application.bindings import LocalBindings

        self.bindings = LocalBindings.load(self.configuration)
        with self.assertRaisesRegex(ContractError, "ROUTE_REPAIR_SCOPE"):
            self.plan()

    def test_supports_or_contradicts_are_not_reinterpreted(self):
        self.edge["type"] = "contradicts"
        self.write_edge()
        self.repair["repairs"][0]["edge"]["revision"] = "sha256:" + digest_bytes(
            canonical_json(self.edge)
        )
        plan = self.plan()
        plan.apply(plan.digest)
        replacement = read_object(
            self.workspace / ".garden/synapses/repaired-edge.json"
        )
        self.assertEqual(replacement["type"], "contradicts")
        self.assertEqual(replacement["directed"], self.edge["directed"])

    def test_unpinned_historical_target_requires_a_new_exact_review(self):
        self.edge["target"]["revision"] = None
        self.write_edge()
        self.repair["repairs"][0]["edge"]["revision"] = "sha256:" + digest_bytes(
            canonical_json(self.edge)
        )
        with self.assertRaisesRegex(ContractError, "ROUTE_REPAIR_TARGET"):
            self.plan()

    def test_two_owner_cutover_failure_restores_both_gardens(self):
        other = add_knowledge(
            self.destination, "other-incoming-owner", sources=self.evidence
        )
        edge = deepcopy(self.edge)
        edge.update(
            garden="other-garden",
            id="other-incoming-edge",
            source=reference("other-garden", other["id"], other["content"]["sha256"]),
        )
        edge_ref = reference(
            "other-garden", edge["id"], digest_bytes(canonical_json(edge))
        )
        write_json(self.destination / ".garden/synapses/other-incoming-edge.json", edge)
        other["synapses"] = [edge_ref]
        write_json(
            self.destination / ".garden/knowledge/other-incoming-owner.json", other
        )
        item = deepcopy(self.repair["repairs"][0])
        item.update(
            edge=edge_ref, source=edge["source"], replacement_id="other-repaired-edge"
        )
        self.repair["repairs"].append(item)
        plan = self.plan()
        before = {
            key: garden_fingerprint(binding["root"])
            for key, binding in self.bindings.gardens.items()
        }
        replace, selected = os.replace, 0

        def fail_second_stage(source, destination):
            nonlocal selected
            if Path(source).name.startswith(".mindgarden-route-stage-"):
                selected += 1
                if selected == 2:
                    raise OSError("Synthetic second-owner failure")
            return replace(source, destination)

        with patch(
            "mindgarden.application.transactions.os.replace",
            side_effect=fail_second_stage,
        ):
            with self.assertRaises(OSError):
                plan.apply(plan.digest)
        self.assertEqual(
            before,
            {
                key: garden_fingerprint(binding["root"])
                for key, binding in self.bindings.gardens.items()
            },
        )
        self.assertTrue(plan.apply(plan.digest))
        self.assertEqual(len(self.index()["edges"]), 2)
