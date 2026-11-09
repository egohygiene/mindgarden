"""Exact graph copies, v2 splits/replacements and private transaction recovery."""

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import graph_payload, search_payload
from mindgarden.application.routing import snapshots_for
from mindgarden.application.routing_lifecycle import build_transition_plan
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.routing_transitions import canonical_reference
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from tests import test_routing_lifecycle as fixtures
from tests.support_v1 import (
    FIXTURES,
    add_knowledge,
    reference,
    write_json,
    write_session,
)


class RoutingTransferTests(unittest.TestCase):
    def setUp(self):
        fixtures.RoutingLifecycleTests.setUp(self)

    def plan(self):
        write_json(self.request_path, self.request)
        return build_transition_plan(self.bindings, self.request_path)

    def attach_graph(self):
        target = add_knowledge(self.workspace, "related-prompt", sources=self.evidence)
        claim = json.loads((FIXTURES / "claim.json").read_text())
        claim.update(
            garden="synthetic-garden",
            id="attached-claim",
            subject=self.request["from"][0],
            statement="A retained assistant suggestion remains unverified.",
            epistemic_state="assumed",
            confidence="low",
            visibility="private",
            scope=local_scope(),
            evidence=[
                {
                    "target": self.evidence[0],
                    "relationship": "uncertain",
                    "rationale": "Exact evidence, not verification.",
                }
            ],
        )
        write_json(self.workspace / ".garden/claims/attached-claim.json", claim)
        edge = json.loads((FIXTURES / "synapse.json").read_text())
        edge.update(
            garden="synthetic-garden",
            id="attached-edge",
            source=self.request["from"][0],
            target=reference(
                "synthetic-garden", target["id"], target["content"]["sha256"]
            ),
            type="supports",
            visibility="private",
            scope=local_scope(),
            status="active",
            review=self.original["review"],
            evidence=self.evidence,
        )
        write_json(self.workspace / ".garden/synapses/attached-edge.json", edge)
        self.original.update(
            claims=[
                reference(
                    "synthetic-garden", claim["id"], digest_bytes(canonical_json(claim))
                )
            ],
            synapses=[
                reference(
                    "synthetic-garden", edge["id"], digest_bytes(canonical_json(edge))
                )
            ],
            **{
                "x-curation": {
                    "attribution": "assistant-suggestion",
                    "epistemic_state": "unverified",
                    "caveats": ["Do not promote during transfer."],
                    "uncertainty": ["Unmeasured."],
                    "contradictions": [edge["target"]],
                }
            },
        )
        write_json(
            self.workspace / ".garden/knowledge/synthetic-prompt.json", self.original
        )
        return claim, edge

    def curate(self, outputs, name):
        proposal = json.loads(
            (Path(__file__).parent / "fixtures/curation/authored-plan.json").read_text()
        )
        template = proposal["candidates"][0]
        proposal.update(id=name, candidates=[])
        for number, changes in enumerate(outputs):
            candidate = deepcopy(template)
            candidate.update(
                id=name + str(number),
                sources=self.evidence,
                merge_inputs=self.request["from"],
            )
            candidate["output"].update(claims=[], synapses=[], **changes)
            if candidate["output"]["kind"] == "reference":
                candidate["action"] = "reference"
            proposal["candidates"].append(candidate)
        path = self.root / (name + ".json")
        write_json(path, proposal)
        plan = build_curation_plan(self.bindings, path)
        apply_curation(plan, plan.digest, self.bindings)
        records = [
            json.loads(
                (
                    self.workspace / ".garden/knowledge" / (changes["id"] + ".json")
                ).read_text()
            )
            for changes in outputs
        ]
        return [
            reference(r["garden"], r["id"], r["content"]["sha256"]) for r in records
        ]

    def split_request(self):
        children = self.curate(
            [
                {"id": "split-one", "body": "First reviewed child.\n"},
                {"id": "split-two", "body": "Second reviewed child.\n"},
            ],
            "authored-children",
        )
        review = self.original["review"]
        edges = [
            {
                "id": "anchor-edge-" + str(i),
                "type": "references",
                "target": child,
                "directed": True,
                "review": review,
                "rationale": "Explicit reviewed split child.",
            }
            for i, child in enumerate(children)
        ]
        # Supply the explicit links after the children have exact represented revisions.
        proposal = json.loads(
            (Path(__file__).parent / "fixtures/curation/authored-plan.json").read_text()
        )
        candidate = deepcopy(proposal["candidates"][0])
        candidate.update(
            action="reference", sources=self.evidence, merge_inputs=self.request["from"]
        )
        candidate["output"].update(
            id="split-anchor",
            kind="reference",
            body="Reviewed map of the two split units.\n",
            claims=[],
            synapses=edges,
        )
        proposal.update(id="authored-anchor", candidates=[candidate])
        path = self.root / "anchor.json"
        write_json(path, proposal)
        plan = build_curation_plan(self.bindings, path)
        apply_curation(plan, plan.digest, self.bindings)
        anchor = json.loads(
            (self.workspace / ".garden/knowledge/split-anchor.json").read_text()
        )
        self.request.update(
            schema="mindgarden.routing-transition/v2",
            operation="split",
            id="reviewed-split",
            to=reference(anchor["garden"], anchor["id"], anchor["content"]["sha256"]),
            split_targets=children,
        )

    def test_move_retains_exact_graph_review_attribution_and_originals(self):
        claim, edge = self.attach_graph()
        before = {
            p: p.read_bytes()
            for p in (self.workspace / ".garden").rglob("*")
            if p.is_file()
        }
        plan = self.plan()
        with patch("socket.socket", side_effect=AssertionError("Network")):
            self.assertTrue(plan.apply(plan.digest))
            self.assertFalse(self.plan().apply(self.plan().digest))
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)
        moved = json.loads(
            (self.destination / ".garden/knowledge/moved-prompt.json").read_text()
        )
        self.assertEqual(moved["x-curation"], self.original["x-curation"])
        copied_claim = json.loads(
            (
                self.destination
                / ".garden/claims"
                / (moved["claims"][0]["id"] + ".json")
            ).read_text()
        )
        copied_edge = json.loads(
            (
                self.destination
                / ".garden/synapses"
                / (moved["synapses"][0]["id"] + ".json")
            ).read_text()
        )
        for field in (
            "review",
            "authors",
            "evidence",
            "epistemic_state",
            "confidence",
            "statement",
        ):
            self.assertEqual(copied_claim[field], claim[field])
        self.assertEqual(copied_edge["target"], edge["target"])
        self.assertEqual(copied_edge["review"], edge["review"])
        self.assertEqual(copied_claim["subject"], copied_edge["source"])
        session = self.root / "query.json"
        write_session(session, self.configuration)
        context = QueryContext.load(self.configuration, session)
        self.assertFalse(
            any(
                r["reference"]["id"] == "attached-claim"
                for r in search_payload(context, "retained assistant")["results"]
            )
        )
        graph = graph_payload(context)
        self.assertTrue(
            any(e["source"] == "other-garden/moved-prompt" for e in graph["edges"])
        )

    def test_graph_transfer_second_cutover_failure_rolls_back_and_retries(self):
        self.attach_graph()
        plan = self.plan()
        before = {
            garden: garden_fingerprint(binding["root"])
            for garden, binding in self.bindings.gardens.items()
        }
        replace = os.replace
        count = 0

        def fail(source, destination):
            nonlocal count
            if (
                Path(source).name.startswith(".mindgarden-route-stage-")
                and Path(destination).name == ".garden"
            ):
                count += 1
                if count == 2:
                    raise OSError("Synthetic graph transfer cutover failure")
            return replace(source, destination)

        with patch("os.replace", side_effect=fail), self.assertRaises(OSError):
            plan.apply(plan.digest)
        self.assertEqual(
            before,
            {
                garden: garden_fingerprint(binding["root"])
                for garden, binding in self.bindings.gardens.items()
            },
        )
        self.assertTrue(plan.apply(plan.digest))

    def test_transfer_preserves_conflicting_destination_and_rejects_scope_weakening(
        self,
    ):
        claim, _ = self.attach_graph()
        marker = self.destination / ".garden/knowledge/moved-prompt.md"
        marker.write_text("Synthetic human-owned destination.")
        with self.assertRaisesRegex(ContractError, "PLAN_CONFLICT"):
            self.plan()
        self.assertEqual(marker.read_text(), "Synthetic human-owned destination.")
        marker.unlink()  # remove only this test's own synthetic conflicting file
        claim["scope"] = local_scope(publication="never-exportable")
        write_json(self.workspace / ".garden/claims/attached-claim.json", claim)
        self.original["claims"][0]["revision"] = "sha256:" + digest_bytes(
            canonical_json(claim)
        )
        write_json(
            self.workspace / ".garden/knowledge/synthetic-prompt.json", self.original
        )
        before = garden_fingerprint(self.workspace)
        with self.assertRaisesRegex(ContractError, "ROUTE_TRANSITION_SCOPE"):
            self.plan()
        self.assertEqual(before, garden_fingerprint(self.workspace))

    def test_reviewed_split_keeps_one_canonical_anchor_and_exact_children(self):
        self.split_request()
        original = (
            self.workspace / ".garden/knowledge/synthetic-prompt.json"
        ).read_bytes()
        self.assertEqual(
            ContractRegistry().errors(
                self.request, "urn:egohygiene:mindgarden:routing-transition:v2"
            ),
            [],
        )
        self.assertTrue(ContractRegistry().errors(self.request, "routing-transition"))
        plan = self.plan()
        self.assertTrue(plan.apply(plan.digest))
        self.assertFalse(self.plan().apply(self.plan().digest))
        records = [
            r for s in snapshots_for(self.bindings).values() for r in s.records.values()
        ]
        self.assertEqual(
            canonical_reference(self.request["from"][0], records), self.request["to"]
        )
        self.assertEqual(
            (self.workspace / ".garden/knowledge/synthetic-prompt.json").read_bytes(),
            original,
        )
        receipt = next(
            r
            for r in records
            if r.get("x-routing-transition", {}).get("operation") == "split"
        )
        self.assertEqual(
            receipt["x-routing-transition"]["split_targets"],
            self.request["split_targets"],
        )
        session = self.root / "query.json"
        write_session(session, self.configuration)
        result = search_payload(
            QueryContext.load(self.configuration, session), "reviewed"
        )
        self.assertFalse(
            any(r["reference"]["id"] == "synthetic-prompt" for r in result["results"])
        )

    def test_split_requires_exact_distinct_reviewed_lineage_and_anchor_links(self):
        self.split_request()
        valid = deepcopy(self.request)
        for mutation in (
            lambda r: r["split_targets"].__setitem__(1, r["split_targets"][0]),
            lambda r: r["split_targets"][0].__setitem__(
                "revision", "sha256:" + "0" * 64
            ),
            lambda r: r.__setitem__("to", r["split_targets"][0]),
        ):
            self.request = deepcopy(valid)
            mutation(self.request)
            with self.assertRaises(ContractError):
                self.plan()
        self.request = valid
        unrelated = add_knowledge(
            self.workspace, "unrelated-child", sources=self.evidence
        )
        self.request["split_targets"][0] = reference(
            "synthetic-garden", unrelated["id"], unrelated["content"]["sha256"]
        )
        with self.assertRaisesRegex(ContractError, "ROUTE_SPLIT_LINEAGE"):
            self.plan()

    def test_supersession_requires_explicit_relationship_and_exact_lineage(self):
        replacement = self.curate(
            [{"id": "replacement", "body": "Reviewed replacement knowledge.\n"}],
            "authored-replacement",
        )[0]
        self.request.update(
            schema="mindgarden.routing-transition/v2",
            operation="supersede",
            to=replacement,
        )
        with self.assertRaisesRegex(ContractError, "ROUTE_SUPERSESSION"):
            self.plan()
        # A distinct reviewed replacement is authored with explicit supersession.
        replacement = self.curate(
            [
                {
                    "id": "replacement-two",
                    "body": "Second reviewed replacement.\n",
                    "supersedes": self.request["from"],
                }
            ],
            "authored-replacement-two",
        )[0]
        self.request["to"] = replacement
        plan = self.plan()
        self.assertTrue(plan.apply(plan.digest))
        records = [
            r for s in snapshots_for(self.bindings).values() for r in s.records.values()
        ]
        self.assertEqual(
            canonical_reference(self.request["from"][0], records), replacement
        )
