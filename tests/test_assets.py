"""Mixed source inventory, exact triage lineage, denied counts and no deletion."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.assets import RETAIN, apply_asset_review, build_asset_manifest, build_asset_review_plan
from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.query import QueryContext
from mindgarden.application.records import artifact_reference
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.storage import content_resolver
from mindgarden.domain.assets import asset_review_heads
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_local_vault as fixtures
from tests.support_v1 import TIME, write_json, write_session

FIXTURES = Path(__file__).parent / "fixtures/assets"


class AssetTests(unittest.TestCase):
    def setUp(self):
        fixtures.LocalVaultTests.setUp(self); fixtures.LocalVaultTests.initialize(self)
        self.bindings = LocalBindings.load(self.configuration)
        self.input = self.root / "synthetic.png"; self.input.write_bytes((FIXTURES / "synthetic.png").read_bytes())
        self.metadata = {"source_id": "synthetic-image", "title": "Synthetic image", "origin": "urn:synthetic:image",
                         "owner": "synthetic-owner", "rights": "Wholly synthetic fixture.", "captured_at": TIME, "media_type": "image/png"}
        self.import_media()
        self.snapshot = inspect_garden(self.workspace, content_resolver=content_resolver(self.bindings)).require_valid()
        self.source = next(record for record in self.snapshot.records.values()
                           if record["schema"] == "mindgarden.source/v1" and record["kind"] == "captured")
        self.reference = artifact_reference("synthetic-garden", self.source["id"], self.source["artifact"]["sha256"])
        self.session_path = self.root / "asset-session.json"

    def import_media(self):
        plan = build_ingestion_plan(self.bindings, "synthetic-garden", "synthetic-vault", self.input, self.metadata)
        apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        return plan

    def context(self, *, unreviewed=True, projections=True, **updates):
        session = write_session(self.session_path, self.configuration)
        if projections: session["projections"].append("assets")
        if unreviewed: session["allowed_review_states"].append("unreviewed")
        session.update(updates)
        write_json(self.session_path, bind_session_revisions(self.configuration, session))
        return QueryContext.load(self.configuration, self.session_path)

    def request(self, state="keep", previous=None, operation="synthetic-review"):
        return {"schema": "mindgarden.asset-review-request/v1", "id": operation, "source": self.reference,
                "state": state, "authority": {"kind": "human", "id": "synthetic-owner"},
                "review": {"state": "approved", "reviewers": ["synthetic-owner"], "reviewed_at": TIME,
                           "rationale": "Synthetic metadata-only triage; preserve every original."},
                "previous": previous, "retention": dict(RETAIN), "copy_policy": "reference-only"}

    def test_media_duplicates_share_one_normalized_identity_and_inventory_asset(self):
        self.assertEqual(self.vault.get("sha256:" + self.source["artifact"]["sha256"]), self.input.read_bytes())
        self.input = self.root / "renamed.png"; self.input.write_bytes((FIXTURES / "synthetic.png").read_bytes())
        self.metadata.update(source_id="alias-image", origin="urn:synthetic:image-alias")
        self.import_media(); self.import_media()
        snapshot = inspect_garden(self.workspace, content_resolver=content_resolver(self.bindings)).require_valid()
        normalized = [record for record in snapshot.records.values() if record["schema"] == "mindgarden.source/v1" and record["kind"] == "normalized"]
        self.assertEqual(len(normalized), 1)
        manifest = build_asset_manifest(self.context())
        self.assertEqual(ContractRegistry().errors(manifest, "asset-manifest"), [])
        self.assertEqual(len(manifest["assets"]), 1); self.assertEqual(len(manifest["assets"][0]["sources"]), 2)
        self.assertNotIn(str(self.root), json.dumps(manifest)); self.assertEqual(manifest["publication"], "never-exportable")
        self.assertEqual(manifest["scope"]["publication"], "never-exportable")

    def test_every_supported_triage_state_preserves_original_and_review_history(self):
        before = self.vault.export_bundle(); original = canonical_json(self.source); previous = None
        for state in json.loads((FIXTURES / "review-cases.json").read_bytes())["supported"]:
            request = self.request(state, previous, "synthetic-" + state)
            plan = build_asset_review_plan(self.bindings, "synthetic-garden", request)
            self.assertEqual(ContractRegistry().errors(plan.document(), "change-plan"), [])
            self.assertTrue(apply_asset_review(plan, plan.digest, self.bindings))
            self.assertFalse(apply_asset_review(plan, plan.digest, self.bindings))
            item = build_asset_manifest(self.context())["assets"][0]
            self.assertEqual(item["state"], state); previous = item["review"]["event"]
            self.assertEqual(self.vault.export_bundle(), before)
            self.assertEqual((self.workspace / (".garden/sources/" + self.source["id"] + ".json")).read_bytes(), original)
            self.assertEqual(self.source["review"]["state"], "unreviewed")

    def test_changed_evidence_target_and_previous_review_invalidate_plans(self):
        request = self.request(); bad = deepcopy(request); bad["source"]["revision"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ContractError, "ASSET_SOURCE_STALE"): build_asset_review_plan(self.bindings, "synthetic-garden", bad)
        plan = build_asset_review_plan(self.bindings, "synthetic-garden", request)
        apply_asset_review(plan, plan.digest, self.bindings)
        with self.assertRaisesRegex(ContractError, "ASSET_REVIEW_STALE"):
            build_asset_review_plan(self.bindings, "synthetic-garden", self.request(operation="stale-next-review"))
        item = build_asset_manifest(self.context())["assets"][0]
        next_plan = build_asset_review_plan(self.bindings, "synthetic-garden", self.request("archived", item["review"]["event"], "next-review"))
        self.metadata["source_id"] = "another-observation"; self.import_media()
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"): apply_asset_review(next_plan, next_plan.digest, self.bindings)

    def test_unknown_retention_restricted_copy_and_agent_authority_fail_closed(self):
        changes = ({"retention": {**RETAIN, "policy": "delete-now"}}, {"copy_policy": "approved-copy"},
                   {"state": "restricted"}, {"authority": {"kind": "agent", "id": "synthetic-agent"}},
                   {"authority": {"kind": "human", "id": "different-human"}})
        before = garden_fingerprint(self.workspace)
        for change in changes:
            with self.assertRaisesRegex(ContractError, "ASSET_REVIEW_INVALID|ASSET_COPY_UNAVAILABLE|RUNTIME_UNVERIFIED"):
                build_asset_review_plan(self.bindings, "synthetic-garden", {**self.request(), **change})
        self.assertEqual(garden_fingerprint(self.workspace), before)

    def test_conflicting_review_forks_are_invalid_without_deleting_any_original(self):
        first = build_asset_review_plan(self.bindings, "synthetic-garden", self.request())
        fork = build_asset_review_plan(self.bindings, "synthetic-garden", self.request("archived", operation="forked-review"))
        apply_asset_review(first, first.digest, self.bindings)
        for relative, content in fork.files.items(): (self.workspace / ".garden" / relative).write_bytes(content)
        snapshot = inspect_garden(self.workspace, content_resolver=content_resolver(self.bindings))
        self.assertIn("ASSET_REVIEW_CONFLICT", [item.code for item in snapshot.diagnostics])
        self.assertEqual(self.vault.get("sha256:" + self.source["artifact"]["sha256"]), self.input.read_bytes())

    def test_source_review_grant_and_projection_permission_precede_body_reads(self):
        denied = self.context(unreviewed=False)
        with patch("mindgarden.adapters.filesystem.FilesystemVault.get", side_effect=AssertionError("Denied source read")):
            self.assertEqual(build_asset_manifest(denied)["assets"], [])
        denied = self.context(projections=False)
        with patch.object(denied, "snapshots", side_effect=AssertionError("Unauthorized inventory read")):
            with self.assertRaisesRegex(ContractError, "PROJECTION_DENIED"): build_asset_manifest(denied)
        public = self.context(request_scope=local_scope("public"))
        with patch.object(public, "snapshots", side_effect=AssertionError("Public inventory read")):
            with self.assertRaisesRegex(ContractError, "PUBLICATION_DENIED"): build_asset_manifest(public)

    def test_inventory_obeys_expiry_revocation_and_serialized_budget(self):
        context = self.context(); context.clock = lambda: datetime(2100, 1, 1, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ContractError, "SESSION_EXPIRED"): build_asset_manifest(context)
        context = self.context(); config = json.loads(self.configuration.read_bytes()); config["revoked_sessions"] = [context.session["id"]]
        write_json(self.configuration, config)
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"): build_asset_manifest(context)
        config["revoked_sessions"] = []; write_json(self.configuration, config)
        context = self.context(); session = deepcopy(context.session); session["budgets"]["max_output_bytes"] = 256
        write_json(self.session_path, bind_session_revisions(self.configuration, session))
        with self.assertRaisesRegex(ContractError, "QUERY_BUDGET"):
            build_asset_manifest(QueryContext.load(self.configuration, self.session_path))

    def test_cli_emits_no_partial_private_data_on_public_denial(self):
        self.context(request_scope=local_scope("public"))
        arguments = ["asset", "inventory", "--local-config", str(self.configuration), "--scope", str(self.session_path), "--diagnostic-format", "json"]
        with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(arguments), 3)
        self.assertEqual(output.getvalue(), ""); self.assertNotIn(self.source["id"], errors.getvalue())
        self.assertNotIn(str(self.root), errors.getvalue()); self.assertNotIn("Synthetic image", errors.getvalue())
        self.assertEqual(json.loads(errors.getvalue())["diagnostics"][0]["code"], "PUBLICATION_DENIED")
