"""Discarded evidence keeps private, exact history during multi-garden routing."""

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.routing import build_routing_plan, snapshots_for
from mindgarden.domain.contracts import digest_bytes, read_object
from mindgarden.domain.validation import ContractError
from tests import test_routing as routing_fixture
from tests import test_source_adapters as source_fixture
from tests.support_v1 import write_json


FIXTURES = Path(__file__).parent / "fixtures/curation"


class RoutingDispositionTests(unittest.TestCase):
    def setUp(self):
        routing_fixture.RoutingTests.setUp(self)
        self.input.write_bytes((FIXTURES / "disposition-source.txt").read_bytes())
        self.metadata["source_id"] = "synthetic-dispositions"
        imported = source_fixture.SourceAdapterTests.plan(self)
        apply_ingestion(imported, imported.digest, self.bindings, "synthetic-vault")
        evidence = imported.inputs["normalized_sources"][0]["evidence"][0]
        lines = self.input.read_bytes().splitlines(keepends=True)
        self.cases = json.loads((FIXTURES / "disposition-cases.json").read_text())
        self.history, self.history_routes = [], []
        for index, case in enumerate(self.cases, 1):
            candidate = {
                "id": "disposition-" + case["classification"],
                "action": case["action"],
                "rationale": case["rationale"],
                "sources": [
                    {
                        **deepcopy(evidence),
                        "locator": f"lines:{index}-{index}",
                        "content_sha256": digest_bytes(lines[index - 1]),
                    }
                ],
                "merge_inputs": [],
            }
            route = {
                **deepcopy(self.request["routes"][0]),
                "candidate": candidate["id"],
                "preferred_gardens": ["synthetic-public"],
                "relevant_gardens": [],
            }
            self.history.append(candidate)
            self.history_routes.append(route)
        self.request["curation"]["candidates"] = deepcopy(self.history)
        self.request["routes"] = deepcopy(self.history_routes)

    def plan(self):
        write_json(self.request_path, self.request)
        return build_routing_plan(self.bindings, self.catalog_path, self.request_path)

    def public_candidate(self):
        template = read_object(
            Path(__file__).parent / "fixtures/conversation-archives/authored-plan.json"
        )["candidates"][0]
        template.update(id="selected-public", sources=self.public_evidence)
        template["output"]["id"] = "selected-public-knowledge"
        route = {
            **deepcopy(self.history_routes[0]),
            "candidate": template["id"],
            "public_review": deepcopy(template["output"]["review"]),
        }
        self.request["curation"]["candidates"].append(template)
        self.request["routes"].append(route)
        root = self.bindings.garden("synthetic-public")["root"] / ".garden"
        manifest = read_object(root / "garden.json")
        manifest["publication"]["allow"] = {
            "kinds": ["procedure"],
            "domains": ["knowledge-systems"],
            "topics": ["prompt-bank"],
        }
        write_json(root / "garden.json", manifest)
        return root

    def test_history_only_retains_each_reason_exact_evidence_and_original(self):
        vault = self.vault.audit()
        originals = {
            path: path.read_bytes()
            for path in (self.workspace / ".garden").rglob("*")
            if path.is_file()
        }
        with patch("subprocess.Popen", side_effect=AssertionError("Source executed")):
            plan = self.plan()
            self.assertEqual(set(plan.changes), {"synthetic-garden"})
            self.assertEqual(
                {item["state"] for item in plan.decisions}, {"history-only"}
            )
            self.assertTrue(plan.apply(plan.digest))
            self.assertFalse(plan.apply(plan.digest))
            repeated = self.plan()
            self.assertFalse(repeated.apply(repeated.digest))
        snapshot = snapshots_for(self.bindings)["synthetic-garden"]
        self.assertFalse(
            any(
                record["schema"] == "mindgarden.knowledge/v1"
                for record in snapshot.records.values()
            )
        )
        for candidate in self.history:
            receipt = snapshot.records[
                "curation-" + self.request["curation"]["id"] + "-" + candidate["id"]
            ]
            self.assertEqual(
                receipt["decisions"],
                [
                    {
                        "candidate": candidate["id"],
                        "action": candidate["action"],
                        "rationale": candidate["rationale"],
                        "sources": candidate["sources"],
                        "output": None,
                    }
                ],
            )
            self.assertEqual(receipt["scope"]["visibility"], "personal")
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(self.vault.audit(), vault)

    def test_public_selection_excludes_private_history_and_rolls_back_together(self):
        public = self.public_candidate()
        plan = self.plan()
        before = {
            key: garden_fingerprint(binding["root"])
            for key, binding in self.bindings.gardens.items()
        }
        replace = os.replace
        selected = 0

        def fail_second_stage(source, destination):
            nonlocal selected
            if Path(source).name.startswith(".mindgarden-route-stage-"):
                selected += 1
                if selected == 2:
                    raise OSError("Synthetic second destination failure")
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
        self.assertTrue((public / "knowledge/selected-public-knowledge.json").is_file())
        public_content = b"".join(
            path.read_bytes() for path in public.rglob("*") if path.is_file()
        )
        for private in [b"PRIVATE-", *[item["id"].encode() for item in self.history]]:
            self.assertNotIn(private, public_content)
        private_content = b"".join(
            path.read_bytes()
            for path in (self.workspace / ".garden/provenance").glob("*.json")
        )
        self.assertIn(b"PRIVATE-DISPOSITION-CANARY", private_content)
        self.assertNotIn(b"PRIVATE-SOURCE-CANARY", private_content)

    def test_changed_reason_or_wrong_evidence_hash_cannot_apply(self):
        plan = self.plan()
        before = garden_fingerprint(self.workspace)
        changed = deepcopy(self.request)
        changed["curation"]["candidates"][0]["rationale"] = "Changed authored decision."
        write_json(self.request_path, changed)
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            plan.apply(plan.digest)
        self.request["curation"]["candidates"][0]["sources"][0]["content_sha256"] = (
            "0" * 64
        )
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            self.plan()
        self.assertEqual(garden_fingerprint(self.workspace), before)

    def test_history_requires_a_personal_controller_with_declared_contracts(self):
        for controller in ("synthetic-public", "synthetic-organization", "unavailable"):
            with self.subTest(controller=controller):
                self.request["curation"]["garden"] = controller
                with self.assertRaisesRegex(ContractError, "ROUTE_HISTORY_PRIVATE"):
                    self.plan()
        self.request["curation"]["garden"] = "synthetic-garden"
        manifest_path = self.workspace / ".garden/garden.json"
        manifest = read_object(manifest_path)
        manifest["contracts"]["writes"].remove("mindgarden.curation-receipt/v1")
        write_json(manifest_path, manifest)
        for entry in self.catalog["gardens"]:
            if entry["id"] == "synthetic-garden":
                entry["contracts"] = deepcopy(manifest["contracts"])
        write_json(self.catalog_path, self.catalog)
        with self.assertRaisesRegex(ContractError, "CAPABILITY_UNDECLARED"):
            self.plan()
