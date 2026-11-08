"""First-pass source access, private proof recovery and expiry without review promotion."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mindgarden.adapters.generated_files import apply_generated
from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.compaction import preview_compaction
from mindgarden.application.compaction_bundles import plan_compaction_bundle
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import search_payload
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.source_evidence import resolve_source_evidence
from mindgarden.domain.contracts import ContractRegistry, digest_bytes
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from tests.compaction_fixture import FIXTURES, capture_fixture, create_fixture, cli
from tests.support_v1 import write_json, write_session


class SourceCompactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = capture_fixture(self.root)
        self.plan = json.loads((FIXTURES / "source-only-plan.json").read_text())
        self.citation = self.plan["nodes"][0]["statements"][0]["evidence"][0]
        self.path = self.root / "session.json"
        self.session = write_session(self.path, self.fixture["configuration"])
        self.session.update(
            request_scope=local_scope(publication="never-exportable"),
            source_grants=[self.citation["source"]],
        )
        self.session["projections"].append("source-evidence")
        self.session["budgets"]["max_context_bytes"] = 32768
        self.refresh()
        self.before = garden_fingerprint(self.fixture["garden"])
        self.original = self.fixture["archive"].read_bytes()
        self.created = datetime.now(timezone.utc).replace(microsecond=0)
        self.created_at = self.created.isoformat().replace("+00:00", "Z")

    def refresh(self):
        self.session = bind_session_revisions(
            self.fixture["configuration"], self.session
        )
        write_json(self.path, self.session)
        self.context = QueryContext.load(self.fixture["configuration"], self.path)

    def preview(self):
        return preview_compaction(self.context, self.plan, source_only=True)

    def test_first_summary_needs_no_knowledge_anchor_and_grants_no_approval(self):
        self.assertEqual(
            list((self.fixture["garden"] / ".garden/knowledge").glob("*.json")), []
        )
        with self.assertRaisesRegex(ContractError, "EVIDENCE_UNAVAILABLE"):
            preview_compaction(self.context, self.plan)
        report = self.preview()
        self.assertEqual(report, self.preview())
        self.assertEqual(report["metrics"]["exact_citations_verified"], 1)
        self.assertEqual(report["evidence"][0]["authorization"], "session-source-grant")
        self.assertEqual(report["evidence"][0]["source_review"]["state"], "unreviewed")
        self.assertEqual(
            report["selected"][0]["statements"][0]["epistemic_state"], "proposed"
        )
        self.assertEqual(search_payload(self.context, "evidence")["results"], [])
        self.assertEqual(self.before, garden_fingerprint(self.fixture["garden"]))
        self.assertEqual(self.original, self.fixture["archive"].read_bytes())

    def test_ungranted_exact_revision_is_denied_before_source_bodies_are_opened(self):
        citation = deepcopy(self.citation)
        citation["source"]["id"] = "denied-canary-source"
        with patch.object(
            self.context, "snapshots", side_effect=AssertionError("Body opened")
        ):
            with self.assertRaisesRegex(ContractError, "SOURCE_GRANT") as error:
                resolve_source_evidence(self.context, **citation)
        self.assertNotIn("denied-canary", str(error.exception))
        citation = deepcopy(self.citation)
        citation["source"]["revision"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ContractError, "SOURCE_GRANT"):
            resolve_source_evidence(self.context, **citation)

    def test_missing_capability_public_networked_and_stale_grants_fail_closed(self):
        original = deepcopy(self.session)
        for change in ("capability", "public", "networked", "stale", "duplicate"):
            self.session = deepcopy(original)
            if change == "capability":
                self.session["projections"].remove("source-evidence")
            if change == "public":
                self.session["request_scope"] = local_scope("public")
            if change == "networked":
                self.session["execution"] = "networked"
            if change == "stale":
                self.session["source_grants"][0]["revision"] = "sha256:" + "0" * 64
            if change == "duplicate":
                self.session["source_grants"].append(
                    deepcopy(self.session["source_grants"][0])
                )
            with self.subTest(change=change), self.assertRaises(ContractError):
                self.refresh()

    def test_source_only_hierarchy_cannot_promote_knowledge_or_publication(self):
        for layer in ("durable-knowledge", "context", "publication-candidate"):
            plan = deepcopy(self.plan)
            plan["nodes"][1]["layer"] = layer
            with (
                self.subTest(layer=layer),
                self.assertRaisesRegex(ContractError, "COMPACTION_SOURCE_REVIEW"),
            ):
                preview_compaction(self.context, plan, source_only=True)
        plan = deepcopy(self.plan)
        plan["curation_plan_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "COMPACTION_SOURCE_REVIEW"):
            preview_compaction(self.context, plan, source_only=True)
        plan = deepcopy(self.plan)
        plan["nodes"][1]["statements"][0]["epistemic_state"] = "decided"
        with self.assertRaisesRegex(ContractError, "COMPACTION_SOURCE_REVIEW"):
            preview_compaction(self.context, plan, source_only=True)

    def test_cli_scope_authors_only_explicit_private_source_grants(self):
        grants = self.root / "source-grants.json"
        write_json(grants, {"source_grants": self.session["source_grants"]})
        args = [
            "scope",
            "--local-config",
            str(self.fixture["configuration"]),
            "--session-id",
            "source-only-cli",
            "--readable-garden",
            "synthetic-garden",
            "--allowed-visibility",
            "personal",
            "--projection",
            "context",
            "--projection",
            "source-evidence",
            "--source-grants",
            str(grants),
            "--publication-authority",
            "never-exportable",
            "--expires-at",
            "2099-01-01T00:00:00Z",
        ]
        session = cli(args)
        self.assertEqual(session["source_grants"], self.session["source_grants"])
        self.assertEqual(session["allowed_review_states"], ["approved"])
        self.assertEqual(
            session["request_scope"], local_scope(publication="never-exportable")
        )

    def test_reviewed_hierarchy_can_be_preserved_without_applying_its_curation(self):
        fixture = create_fixture(self.root / "reviewed")
        before = garden_fingerprint(fixture["garden"])
        preview, files = plan_compaction_bundle(
            fixture["context"],
            fixture["plan"],
            self.created_at,
            curation=fixture["curation"],
        )
        self.assertEqual(preview["bundle"]["input_mode"], "reviewed-evidence")
        self.assertIn("curation.json", files)
        self.assertEqual(len(preview["report"]["manifest"]["nodes"]), 13)
        self.assertEqual(before, garden_fingerprint(fixture["garden"]))

    def test_corrupted_source_and_wrong_span_hash_invalidate_proof(self):
        citation = deepcopy(self.citation)
        citation["content_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "QUERY_INTEGRITY"):
            resolve_source_evidence(self.context, **citation)
        digest = self.citation["source"]["revision"].removeprefix("sha256:")
        blob = self.root / "vault/objects/sha256" / digest[:2] / digest
        blob.chmod(0o600)
        blob.write_bytes(b"Synthetic corrupt normalized evidence")
        with self.assertRaisesRegex(ContractError, "QUERY_INTEGRITY"):
            self.preview()

    def test_cli_create_repeat_check_stale_digest_and_conflict_preserve_originals(self):
        plan_path = self.root / "source-plan.json"
        write_json(plan_path, self.plan)
        output = self.root / "proof"
        args = [
            "compaction",
            "build",
            "--input",
            str(plan_path),
            "--local-config",
            str(self.fixture["configuration"]),
            "--scope",
            str(self.path),
            "--source-only",
            "--created-at",
            self.created_at,
            "--output-directory",
            str(output),
        ]
        preview = cli(args)
        self.assertFalse(output.exists())
        self.assertEqual(
            cli([*args, "--apply", "--plan-digest", preview["plan_sha256"]])["status"],
            "created",
        )
        self.assertEqual(
            cli([*args, "--apply", "--plan-digest", preview["plan_sha256"]])["status"],
            "verified-no-op",
        )
        self.assertEqual(cli([*args, "--check"])["status"], "verified-no-op")
        bundle = json.loads((output / "bundle.json").read_text())
        self.assertEqual(ContractRegistry().errors(bundle, "compaction-bundle"), [])
        self.assertEqual(bundle["input_mode"], "source-grant")
        self.assertEqual((output / "manifest.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(output.stat().st_mode & 0o777, 0o700)
        self.assertEqual(
            bundle["manifest_sha256"],
            digest_bytes((output / "manifest.json").read_bytes()),
        )
        bad = self.root / "stale"
        with self.assertRaisesRegex(ContractError, "GENERATED_PLAN_STALE"):
            p, files = plan_compaction_bundle(
                self.context, self.plan, self.created_at, source_only=True
            )
            apply_generated(
                bad,
                files,
                "0" * 64,
                p["plan_sha256"],
                check_live=self.context.check_live,
                verify_inputs=lambda: None,
            )
        self.assertFalse(bad.exists())
        (output / "report.json").write_bytes(b"Synthetic occupied output")
        with self.assertRaisesRegex(ContractError, "GENERATED_CONFLICT"):
            apply_generated(
                output,
                files,
                p["plan_sha256"],
                p["plan_sha256"],
                check_live=self.context.check_live,
                verify_inputs=lambda: None,
            )
        self.assertEqual(self.before, garden_fingerprint(self.fixture["garden"]))
        self.assertEqual(self.original, self.fixture["archive"].read_bytes())

    def test_expiry_revocation_and_changed_inputs_reject_without_deleting_old_proof(
        self,
    ):
        preview, files = plan_compaction_bundle(
            self.context, self.plan, self.created_at, source_only=True
        )
        output = self.root / "proof"
        apply_generated(
            output,
            files,
            preview["plan_sha256"],
            preview["plan_sha256"],
            check_live=self.context.check_live,
            verify_inputs=lambda: None,
        )
        lifetime = self.plan["retention"]["model_context"]["ttl_seconds"]
        self.context.clock = lambda: self.created + timedelta(seconds=lifetime)
        with self.assertRaisesRegex(ContractError, "COMPACTION_EXPIRED"):
            plan_compaction_bundle(
                self.context, self.plan, self.created_at, source_only=True
            )
        self.context.clock = lambda: self.created + timedelta(seconds=1)
        changed = deepcopy(self.plan)
        changed["nodes"][1]["rationale"] = (
            "A changed authored interpretation needs a new review."
        )
        new, _ = plan_compaction_bundle(
            self.context, changed, self.created_at, source_only=True
        )
        self.assertNotEqual(new["plan_sha256"], preview["plan_sha256"])
        config = json.loads(self.fixture["configuration"].read_text())
        config["revoked_sessions"] = [self.session["id"]]
        write_json(self.fixture["configuration"], config)
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            plan_compaction_bundle(
                self.context, self.plan, self.created_at, source_only=True
            )
        self.assertEqual(
            (output / "manifest.json").read_bytes(), files["manifest.json"]
        )
        self.assertEqual(self.original, self.fixture["archive"].read_bytes())

    def test_interrupted_creation_retains_inspectable_partial_and_requires_new_destination(
        self,
    ):
        preview, files = plan_compaction_bundle(
            self.context, self.plan, self.created_at, source_only=True
        )
        output = self.root / "partial"
        calls = 0

        def interrupt():
            nonlocal calls
            calls += 1
            if calls == 3:
                raise ContractError("SYNTHETIC_INTERRUPTION: stop after one output")

        with self.assertRaisesRegex(ContractError, "SYNTHETIC_INTERRUPTION"):
            apply_generated(
                output,
                files,
                preview["plan_sha256"],
                preview["plan_sha256"],
                check_live=self.context.check_live,
                verify_inputs=interrupt,
            )
        self.assertEqual(len(list(output.iterdir())), 1)
        with self.assertRaisesRegex(ContractError, "GENERATED_CONFLICT"):
            apply_generated(
                output,
                files,
                preview["plan_sha256"],
                preview["plan_sha256"],
                check_live=self.context.check_live,
                verify_inputs=lambda: None,
            )
        recovered = self.root / "recovered"
        self.assertTrue(
            apply_generated(
                recovered,
                files,
                preview["plan_sha256"],
                preview["plan_sha256"],
                check_live=self.context.check_live,
                verify_inputs=lambda: None,
            )
        )
        self.assertEqual(self.before, garden_fingerprint(self.fixture["garden"]))


if __name__ == "__main__":
    unittest.main()
