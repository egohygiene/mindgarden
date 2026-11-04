"""Explained routing, explicit public review, canonical homes and recovery."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.records import provenance_record
from mindgarden.application.routing import build_routing_plan, snapshots_for
from mindgarden.application.transactions import journal_path, recover_routing
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.support_v1 import TIME, add_source, create_garden, reference, write_json
from tests import test_source_adapters as source_tests


class RoutingTests(unittest.TestCase):
    def setUp(self):
        source_tests.SourceAdapterTests.setUp(self)
        imported = source_tests.SourceAdapterTests.plan(self)
        apply_ingestion(imported, imported.digest, self.bindings, "synthetic-vault")
        self.private_evidence = imported.inputs["normalized_sources"][0]["evidence"]
        configuration = json.loads(self.configuration.read_text())
        for identity, kind, visibility, classification in (
                ("synthetic-repository", "repository", "private", "personal"),
                ("synthetic-organization", "organization", "internal", "organization"),
                ("synthetic-public", "repository", "public", "public")):
            root = self.root / identity
            garden = create_garden(root, identity, visibility)
            manifest = json.loads((garden / "garden.json").read_text()); manifest["kind"] = kind
            write_json(garden / "garden.json", manifest)
            configuration["gardens"].append({"id": identity, "root": str(root), "scope": local_scope(classification)})
        write_json(self.configuration, configuration)
        self.bindings = LocalBindings.load(self.configuration)
        public_root = self.bindings.garden("synthetic-public")["root"]
        content = b"Explicitly public synthetic source.\n"
        raw = add_source(public_root, content, record_id="public-capture")
        raw.update(visibility="public", scope=local_scope("public"))
        write_json(public_root / ".garden/sources/public-capture.json", raw)
        normalized = deepcopy(raw)
        normalized.update(id="public-normalized", kind="normalized", publication="eligible",
                          inputs=[reference("synthetic-public", "public-capture", digest_bytes(content))],
                          review={"state": "approved", "reviewers": ["synthetic-reviewer"], "reviewed_at": TIME,
                                  "rationale": "Explicit synthetic public evidence review."})
        provenance = provenance_record("synthetic-public", "provenance-public-normalized", "public-normalized", digest_bytes(content),
            inputs=[{"artifact": normalized["inputs"][0], "sha256": digest_bytes(content), "role": "source"}],
            transformations=({"name": "normalize-synthetic-public-source", "version": "1.0.0", "parameters": {}},),
            created_at=TIME, rights="Public synthetic fixture.", origin="urn:synthetic:public", scope=local_scope("public"))
        normalized["provenance"] = [reference("synthetic-public", provenance["id"], digest_bytes(canonical_json(provenance)))]
        write_json(public_root / ".garden/provenance/provenance-public-normalized.json", provenance)
        write_json(public_root / ".garden/sources/public-normalized.json", normalized)
        self.public_evidence = [{"source": reference("synthetic-public", "public-normalized", digest_bytes(content)),
                                 "locator": "artifact", "content_sha256": digest_bytes(content)}]
        snapshots = snapshots_for(self.bindings)
        self.catalog = {"schema": "mindgarden.garden-catalog/v1", "id": "synthetic-catalog", "private_fallback": "synthetic-garden",
                        "gardens": [{"id": identity, "scope": self.bindings.garden(identity)["scope"],
                                     **{field: snapshot.manifest[field] for field in ("kind", "owners", "canonical_uri", "contracts")},
                                     "domains": snapshot.manifest["routing"]["domains"]}
                                    for identity, snapshot in sorted(snapshots.items())]}
        self.catalog_path = self.root / "catalog.json"; write_json(self.catalog_path, self.catalog)
        base = json.loads((Path(__file__).parent / "fixtures/conversation-archives/authored-plan.json").read_text())
        template = base["candidates"][0]
        candidates, routes = [], []
        for name, evidence, preferred, relevant in (
                ("personal", self.private_evidence, ["synthetic-organization"], ["synthetic-repository"]),
                ("repository", self.private_evidence, ["synthetic-repository"], []),
                ("organization", self.public_evidence, ["synthetic-organization"], [])):
            candidate = deepcopy(template)
            candidate.update(id="candidate-" + name, sources=evidence)
            candidate["output"].update(id="routed-" + name, title="Synthetic " + name + " knowledge")
            candidates.append(candidate)
            routes.append({"candidate": candidate["id"], "preferred_gardens": preferred, "relevant_gardens": relevant,
                           "confidence": "medium", "rationale": "Explicit synthetic routing decision.", "public_review": None})
        base["candidates"] = candidates
        self.request = {"schema": "mindgarden.routing-plan/v1", "id": "synthetic-routing", "curation": base, "routes": routes}
        self.request_path = self.root / "routes.json"; write_json(self.request_path, self.request)

    def plan(self):
        return build_routing_plan(self.bindings, self.catalog_path, self.request_path)

    def test_three_garden_kinds_explain_home_fallback_and_stable_references(self):
        self.assertEqual(ContractRegistry().errors(self.catalog, "garden-catalog"), [])
        self.assertEqual(ContractRegistry().errors(self.request, "routing-plan"), [])
        plan = self.plan()
        self.assertNotIn(str(self.root), json.dumps(plan.document()))
        personal = next(item for item in plan.decisions if item["candidate"] == "candidate-personal")
        self.assertEqual(personal["state"], "private-fallback")
        self.assertEqual(personal["canonical_home"]["garden"], "synthetic-garden")
        self.assertEqual(personal["references"][0]["garden"], "synthetic-repository")
        self.assertTrue(personal["rejected_alternatives"])
        self.assertTrue(plan.apply(plan.digest))
        self.assertFalse(plan.apply(plan.digest))
        snapshots = snapshots_for(self.bindings)
        canonical = [record for snapshot in snapshots.values() for record in snapshot.records.values()
                     if record.get("x-routing", {}).get("role") == "canonical"]
        self.assertEqual(len(canonical), 3)
        self.assertEqual(len({item["x-routing"]["unit"] for item in canonical}), 3)
        again = self.plan(); self.assertFalse(again.apply(again.digest))
        for garden in ("synthetic-garden", "synthetic-repository", "synthetic-organization"):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["validate", "--repository-root", str(self.bindings.garden(garden)["root"]),
                                       "--local-config", str(self.configuration), "--format", "json"]), 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "valid")

    def test_missing_fallback_stays_unresolved_and_check_returns_contract_failure(self):
        self.catalog["private_fallback"] = None; write_json(self.catalog_path, self.catalog)
        plan = self.plan()
        personal = next(item for item in plan.decisions if item["candidate"] == "candidate-personal")
        self.assertIsNone(personal["canonical_home"])
        self.assertEqual(personal["state"], "unresolved")
        with redirect_stdout(io.StringIO()):
            result = main(["route", "--local-config", str(self.configuration), "--catalog", str(self.catalog_path),
                           "--input", str(self.request_path), "--check"])
        self.assertEqual(result, 3)

    def test_public_routes_require_review_and_cannot_receive_private_sources(self):
        self.request["curation"]["candidates"] = [self.request["curation"]["candidates"][0]]
        self.request["routes"] = [self.request["routes"][0]]
        route = self.request["routes"][0]; route.update(preferred_gardens=["synthetic-public"], relevant_gardens=[])
        write_json(self.request_path, self.request)
        self.assertEqual(self.plan().decisions[0]["state"], "private-fallback")
        candidate = self.request["curation"]["candidates"][0]
        candidate["sources"] = self.public_evidence
        write_json(self.request_path, self.request)
        self.assertEqual(self.plan().decisions[0]["state"], "private-fallback")
        route["public_review"] = deepcopy(candidate["output"]["review"])
        write_json(self.request_path, self.request)
        plan = self.plan(); self.assertEqual(plan.decisions[0]["state"], "routed")
        plan.apply(plan.digest)
        output = json.loads((self.bindings.garden("synthetic-public")["root"] / ".garden/knowledge/routed-personal.json").read_text())
        self.assertEqual(output["publication"], "eligible")
        self.assertEqual(output["sources"], self.public_evidence)
        public_bytes = b"".join(path.read_bytes() for path in
                                (self.bindings.garden("synthetic-public")["root"] / ".garden").rglob("*.json"))
        for private_value in (digest_bytes(self.request_path.read_bytes()), digest_bytes(self.catalog_path.read_bytes()),
                              "synthetic-garden", "candidate-personal", "synthetic-routing:candidate-personal"):
            self.assertNotIn(private_value.encode(), public_bytes)
        self.assertTrue((self.workspace / ".garden/provenance/routing-synthetic-routing.json").is_file())

    def test_changed_target_invalidates_digest_and_cannot_overwrite_human_content(self):
        plan = self.plan()
        path = self.workspace / ".garden/knowledge/routed-personal.md"
        path.write_text("Synthetic human-owned content.\n")
        with self.assertRaisesRegex(ContractError, "PLAN_CONFLICT"):
            plan.apply(plan.digest)
        self.assertEqual(path.read_text(), "Synthetic human-owned content.\n")
        self.assertFalse((self.workspace / ".mindgarden-write.lock").exists())

    def test_partial_selection_failure_restores_every_original(self):
        plan = self.plan()
        before = {key: garden_fingerprint(item["root"]) for key, item in self.bindings.gardens.items()}
        replace = os.replace; selected = 0

        def fail_second_stage(source, destination):
            nonlocal selected
            if Path(source).name.startswith(".mindgarden-route-stage-"):
                selected += 1
                if selected == 2:
                    raise OSError("Synthetic second target selection failure")
            return replace(source, destination)

        with patch("mindgarden.application.transactions.os.replace", side_effect=fail_second_stage):
            with self.assertRaises(OSError):
                plan.apply(plan.digest)
        self.assertEqual(before, {key: garden_fingerprint(item["root"]) for key, item in self.bindings.gardens.items()})
        self.assertFalse(journal_path(self.bindings, plan.digest).exists())
        self.assertTrue(plan.apply(plan.digest))

    def test_failed_rollback_retains_last_original_and_explicit_recovery_converges(self):
        plan = self.plan(); replace = os.replace
        before = {key: garden_fingerprint(item["root"]) for key, item in self.bindings.gardens.items()}

        def fail_selection_and_rollback(source, destination):
            if Path(source).name.startswith((".mindgarden-route-stage-", ".mindgarden-route-backup-")):
                raise OSError("Synthetic interrupted selection and rollback")
            return replace(source, destination)

        with patch("mindgarden.application.transactions.os.replace", side_effect=fail_selection_and_rollback):
            with self.assertRaises(OSError):
                plan.apply(plan.digest)
        self.assertTrue(journal_path(self.bindings, plan.digest).exists())
        self.assertTrue(list(self.workspace.glob(".mindgarden-route-backup-*")))
        with redirect_stdout(io.StringIO()) as validation:
            self.assertEqual(main(["validate", "--repository-root", str(self.workspace), "--format", "json"]), 3)
        self.assertEqual(json.loads(validation.getvalue())["diagnostics"][0]["code"], "WRITE_LOCKED")
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["route", "--local-config", str(self.configuration), "--recover",
                                   "--plan-digest", plan.digest]), 0)
        self.assertEqual(json.loads(output.getvalue())["state"], "rolled-back")
        self.assertEqual(before, {key: garden_fingerprint(item["root"]) for key, item in self.bindings.gardens.items()})
        self.assertFalse(journal_path(self.bindings, plan.digest).exists())

    def test_retargeting_a_placed_unit_requires_explicit_deferred_transfer(self):
        plan = self.plan(); plan.apply(plan.digest)
        self.request["routes"][1]["preferred_gardens"] = ["synthetic-garden"]
        write_json(self.request_path, self.request)
        with self.assertRaisesRegex(ContractError, "ROUTE_REVISION_REQUIRED"):
            self.plan()
