"""Public discovery keeps reviewed selection, integrity and failure isolation."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.federation_files import read_bundle, write_bundle
from mindgarden.application.federation import build_catalog, build_federation
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.federation import BUNDLE_NAMES, public_url, verify_bundle
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.federation_fixture import FEDERATION_FIXTURES, create_fixture
from tests.support_v1 import add_knowledge, write_json
from tests import test_v1_contracts as contract_tests


class FederationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root / "first")
        self.context = self.fixture["context"]
        self.profile = self.fixture["profile"]
        self.bundle = self.fixture["bundle"]

    def materialize(self, fixture=None):
        fixture = fixture or self.fixture
        bundle = fixture["bundle"]
        digest = bundle.plan(fixture["context"], fixture["export"])["plan_sha256"]
        bundle.apply(fixture["context"], fixture["export"], digest)
        return fixture["export"] / bundle.output_root

    def request(self, *fixtures):
        return {"schema": "mindgarden.federation-catalog-request/v1", "bundles": [
            {"directory": str(self.materialize(fixture)), "expected_revision": fixture["bundle"].descriptor["revision"]}
            for fixture in fixtures or [self.fixture]]}

    def refresh(self, **updates):
        session = json.loads(self.fixture["session_path"].read_text())
        session.update(updates)
        write_json(self.fixture["session_path"], bind_session_revisions(self.fixture["configuration"], session))
        self.context = QueryContext.load(self.fixture["configuration"], self.fixture["session_path"])
        return self.context

    def test_offline_public_bundle_has_exact_citations_and_no_control_metadata(self):
        with patch("socket.socket", side_effect=AssertionError("Network attempted")), patch("subprocess.run", side_effect=AssertionError("Process attempted")):
            bundle = build_federation(self.context, self.profile)
            descriptor, index, graph = verify_bundle(bundle.files)
        serialized = b"".join(bundle.files.values())
        canaries = json.loads((FEDERATION_FIXTURES / "negative-cases.json").read_text())["canaries"]
        for value in [str(self.root), self.context.session["id"], self.context.scope_digest(), *canaries]:
            self.assertNotIn(value.encode(), serialized)
        self.assertEqual(len(index["records"]), 3)
        self.assertEqual(len(graph["edges"]), 1)
        prompt = next(record for record in index["records"] if record["reference"]["id"] == "reviewed-prompt")
        self.assertEqual(prompt["sources"], self.fixture["evidence"])
        self.assertEqual(prompt["qualifications"]["epistemic_state"], "proposed")
        self.assertEqual(prompt["review_state"], "approved")
        self.assertEqual(descriptor["capabilities"]["unavailable"], ["remote-fetch", "remote-query", "remote-write", "private-federation", "cryptographic-signatures"])

    def test_projection_schemas_match_official_validator(self):
        contract_tests.V1ContractTests.setUpClass()
        validator = contract_tests.V1ContractTests()
        values = [("federation-descriptor", self.bundle.descriptor),
                  ("federation-index", json.loads(self.bundle.files["index.json"])),
                  ("federation-graph", json.loads(self.bundle.files["graph.json"])),
                  ("federation-plan", self.bundle.plan(self.context, self.fixture["export"])),
                  ("federation-catalog-request", self.request()),
                  ("federation-catalog", build_catalog(self.request()))]
        for contract, value in values:
            with self.subTest(contract=contract):
                self.assertEqual(ContractRegistry().errors(value, contract), [])
                self.assertEqual(list(validator.validator(contract).iter_errors(value)), [])

    def test_clean_rebuild_and_relocated_roots_are_byte_identical(self):
        second = create_fixture(self.root / "clean-rebuild")
        self.assertEqual(self.bundle.files, second["bundle"].files)
        expected = FEDERATION_FIXTURES / "expected"
        self.assertEqual({path.name: path.read_bytes() for path in expected.iterdir()}, self.bundle.files)
        exported = self.materialize()
        relocated = self.root / "relocated-public-bundle"
        shutil.copytree(exported, relocated)
        self.assertEqual(read_bundle(relocated), self.bundle.files)

    def test_denied_bodies_paths_counts_and_presence_do_not_change_public_bytes(self):
        workspace = self.fixture["workspace"]
        denied = add_knowledge(workspace, "denied-note", body="private-body-canary\n")
        denied["content"]["path"] = "../never-open-private.md"
        write_json(workspace / ".garden/knowledge/denied-note.json", denied)
        pending_path = workspace / ".garden/knowledge/unreviewed.json"
        pending = json.loads(pending_path.read_text()); pending["content"]["path"] = "../never-open-unreviewed.md"
        write_json(pending_path, pending)
        configuration = json.loads(self.fixture["configuration"].read_text())
        configuration["gardens"][-1]["root"] = str(self.root / "different-hidden-root-canary")
        write_json(self.fixture["configuration"], configuration)
        read = Path.read_bytes

        def guarded(path):
            if path.name in {"never-open-private.md", "never-open-unreviewed.md", "unreviewed.md", "denied-note.md"}:
                raise AssertionError("Denied body was read")
            return read(path)

        with patch.object(Path, "read_bytes", guarded):
            context = QueryContext.load(self.fixture["configuration"], self.fixture["session_path"])
            self.assertEqual(build_federation(context, self.profile).files, self.bundle.files)

    def test_missing_review_eligibility_and_allowlists_fail_closed(self):
        for update in [{"review": {"state": "unreviewed", "reviewers": [], "reviewed_at": None, "rationale": None}},
                       {"visibility": "private"}, {"kind": "site"}]:
            profile = deepcopy(self.profile); profile.update(update)
            with self.subTest(update=update), self.assertRaisesRegex(ContractError, "FEDERATION_PROFILE"):
                build_federation(self.context, profile)
        profile = deepcopy(self.profile); profile["policy"]["allow"]["kinds"] = []
        with self.assertRaisesRegex(ContractError, "FEDERATION_POLICY"):
            build_federation(self.context, profile)
        profile = deepcopy(self.profile); profile["inputs"][0]["revision"] = None
        with self.assertRaisesRegex(ContractError, "FEDERATION_SELECTION"):
            build_federation(self.context, profile)
        profile = deepcopy(self.profile); profile["inputs"] = [profile["inputs"][0]]
        with self.assertRaisesRegex(ContractError, "FEDERATION_SELECTION"):
            build_federation(self.context, profile)

    def test_public_visibility_does_not_override_never_exportable_or_review_required(self):
        workspace = self.fixture["workspace"]
        for permission in ("never-exportable", "review-required"):
            record = add_knowledge(workspace, permission, visibility="public", body="denied-export-body-canary\n")
            record.update(publication="eligible", scope=local_scope("public", publication=permission))
            record["content"]["path"] = "../never-open-export.md"
            write_json(workspace / f".garden/knowledge/{permission}.json", record)
        read = Path.read_bytes

        def guarded(path):
            if path.name == "never-open-export.md":
                raise AssertionError("Denied publication body was read")
            return read(path)

        with patch.object(Path, "read_bytes", guarded):
            self.assertEqual(build_federation(self.context, self.profile).files, self.bundle.files)

    def test_broad_sessions_missing_capabilities_and_expiration_cannot_export(self):
        context = self.refresh(allowed_visibilities=["public", "organization"])
        with self.assertRaisesRegex(ContractError, "FEDERATION_SCOPE"):
            build_federation(context, self.profile)
        context = self.refresh(allowed_visibilities=["public"], projections=["index"])
        with self.assertRaisesRegex(ContractError, "PROJECTION_DENIED"):
            build_federation(context, self.profile)
        session = json.loads(self.fixture["session_path"].read_text()); session["expires_at"] = "2000-01-01T00:00:00Z"
        write_json(self.fixture["session_path"], session)
        with self.assertRaisesRegex(ContractError, "SESSION_EXPIRED"):
            QueryContext.load(self.fixture["configuration"], self.fixture["session_path"])

    def test_denied_source_publication_inherits_before_evidence_body_reads(self):
        profile = deepcopy(self.profile); profile["inputs"] = []
        empty = build_federation(self.context, profile)
        source_path = self.fixture["workspace"] / ".garden/sources/public-source.json"
        source = json.loads(source_path.read_text())
        source["scope"] = local_scope("public", publication="never-exportable")
        source["artifact"]["path"] = "../never-open-source.txt"
        write_json(source_path, source)
        read = Path.read_bytes

        def guarded(path):
            if path.name in {"never-open-source.txt", "public-source.txt"}:
                raise AssertionError("Denied evidence body was read")
            return read(path)

        with patch.object(Path, "read_bytes", guarded):
            self.refresh()
            index = build_index(self.context)
            self.assertEqual(index["records"], [])
            profile["source_revision"] = index["inputs"][0]["revision"]
            self.assertEqual(build_federation(self.context, profile).files, empty.files)

    def test_changed_inputs_and_profile_invalidate_plans_without_writing(self):
        digest = self.bundle.plan(self.context, self.fixture["export"])["plan_sha256"]
        profile = deepcopy(self.profile); profile["review"]["rationale"] = "A different reviewed control profile."
        changed = build_federation(self.context, profile)
        self.assertEqual(changed.files, self.bundle.files)
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            changed.apply(self.context, self.fixture["export"], digest)
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            self.bundle.apply(self.context, self.root, digest)
        source = self.fixture["workspace"] / ".garden/sources/public-source.txt"
        source.write_bytes(b"Modified evidence.\n")
        with self.assertRaisesRegex(ContractError, "QUERY_INTEGRITY"):
            build_federation(self.context, self.profile)
        with self.assertRaisesRegex(ContractError, "QUERY_INTEGRITY"):
            self.bundle.apply(self.context, self.fixture["export"], digest)
        self.assertEqual(list(self.fixture["export"].iterdir()), [])

    def test_profile_file_bytes_are_rechecked_and_public_input_changes_require_refresh(self):
        path = self.fixture["profile_path"]
        bundle = build_federation(self.context, self.profile, profile_path=path,
                                  profile_sha256=digest_bytes(path.read_bytes()))
        digest = bundle.plan(self.context, self.fixture["export"])["plan_sha256"]
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            bundle.apply(self.context, self.fixture["export"], digest)
        extra = add_knowledge(self.fixture["workspace"], "new-public-record", visibility="public")
        extra["publication"] = "eligible"
        write_json(self.fixture["workspace"] / ".garden/knowledge/new-public-record.json", extra)
        self.refresh()
        with self.assertRaisesRegex(ContractError, "FEDERATION_REVISION"):
            build_federation(self.context, self.profile)

    def test_immutable_output_and_partial_failure_preserve_other_files(self):
        directory = self.materialize()
        plan = self.bundle.plan(self.context, self.fixture["export"])
        self.assertFalse(self.bundle.apply(self.context, self.fixture["export"], plan["plan_sha256"]))
        sibling = self.fixture["export"] / "unrelated.txt"; sibling.write_text("Keep me.\n")
        (directory / "foreign.txt").write_text("Unowned content.\n")
        with self.assertRaisesRegex(ContractError, "FEDERATION_"):
            self.bundle.apply(self.context, self.fixture["export"], plan["plan_sha256"])
        fresh = self.root / "fresh-bundle"
        calls = []

        def interrupted():
            calls.append(1)
            if len(calls) == 3:
                raise ContractError("SESSION_REVOKED: synthetic mid-write revocation")

        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            write_bundle(fresh, self.bundle.files, check_live=interrupted)
        self.assertFalse(fresh.exists())
        self.assertEqual(sibling.read_text(), "Keep me.\n")
        self.assertTrue((directory / "foreign.txt").is_file())

    def test_canonical_vault_and_symlink_destinations_are_rejected(self):
        for output in [self.fixture["workspace"] / ".garden",
                       self.fixture["configuration"].parent / "hidden-vault-canary"]:
            with self.subTest(output=output), self.assertRaisesRegex(ContractError, "FEDERATION_OUTPUT"):
                self.bundle.plan(self.context, output)
        linked = self.root / "symlink"; linked.symlink_to(self.fixture["export"], target_is_directory=True)
        with self.assertRaisesRegex(ContractError, "FEDERATION_PATH|PATH_SYMLINK"):
            self.bundle.plan(self.context, linked)

    def test_revoked_authority_and_missing_export_parent_fail_without_echo(self):
        plan = self.bundle.plan(self.context, self.fixture["export"])
        configuration = json.loads(self.fixture["configuration"].read_text())
        configuration["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.fixture["configuration"], configuration)
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            self.bundle.apply(self.context, self.fixture["export"], plan["plan_sha256"])
        configuration["revoked_sessions"] = []
        write_json(self.fixture["configuration"], configuration)
        missing = self.root / "missing-private-parent-canary"
        plan = self.bundle.plan(self.context, missing)
        with self.assertRaisesRegex(ContractError, "FEDERATION_OUTPUT") as caught:
            self.bundle.apply(self.context, missing, plan["plan_sha256"])
        self.assertNotIn(str(self.root), str(caught.exception))
        self.assertFalse(missing.exists())

    def test_symlinked_and_extra_members_do_not_enter_catalog_or_diagnostics(self):
        request = self.request()
        directory = Path(request["bundles"][0]["directory"])
        target = directory / "index.json"; target.unlink()
        outside = self.root / "private-body-canary.json"; outside.write_text("private-body-canary")
        target.symlink_to(outside)
        result = build_catalog(request)
        self.assertEqual(result["diagnostics"], ["FEDERATION_INVALID"])
        self.assertEqual(result["records"], [])
        self.assertNotIn(b"private-body-canary", canonical_json(result))
        self.assertNotIn(str(self.root).encode(), canonical_json(result))

    def test_catalog_is_deterministic_and_contains_links_without_note_bodies(self):
        second = create_fixture(self.root / "second", "organization-garden")
        request = self.request(self.fixture, second)
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            result = build_catalog(request)
        reverse = {**request, "bundles": list(reversed(request["bundles"]))}
        self.assertEqual(result, build_catalog(reverse))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(result["gardens"]), 2)
        self.assertEqual(len(result["records"]), 6)
        self.assertNotIn(b"Use exact source evidence.", canonical_json(result))
        self.assertNotIn(str(self.root).encode(), canonical_json(result))
        self.assertTrue(all(record["canonical_url"].startswith("https://") for record in result["records"]))

    def test_catalog_isolates_unavailable_stale_corrupt_and_incompatible_bundles(self):
        second = create_fixture(self.root / "second", "organization-garden")
        for failure, expected in [("missing", "FEDERATION_UNAVAILABLE"), ("stale", "FEDERATION_STALE"),
                                  ("corrupt", "FEDERATION_INTEGRITY"), ("version", "FEDERATION_VERSION")]:
            request = self.request(self.fixture, second)
            selected = request["bundles"][0]
            if failure == "missing":
                selected["directory"] = str(self.root / "missing-private-filename-canary")
            elif failure == "stale":
                selected["expected_revision"] = "sha256:" + "0" * 64
            else:
                path = Path(selected["directory"]) / ("index.json" if failure == "corrupt" else "garden.json")
                document = json.loads(path.read_text())
                if failure == "corrupt":
                    document["records"][0]["content"] += "tampered"
                else:
                    document["schema"] = "mindgarden.federation-descriptor/v999"
                write_json(path, document)
            with self.subTest(failure=failure):
                result = build_catalog(request)
                self.assertEqual(result["status"], "partial")
                self.assertEqual(result["diagnostics"], [expected])
                self.assertEqual([garden["garden"] for garden in result["gardens"]], ["organization-garden"])
                self.assertNotIn(str(self.root).encode(), canonical_json(result))
            # Restore only this fixture's exact immutable synthetic files for
            # the next independent corruption case.
            directory = self.fixture["export"] / self.bundle.output_root
            for name, content in self.bundle.files.items():
                (directory / name).write_bytes(content)

    def test_duplicate_id_and_conflicting_canonical_homes_are_quarantined(self):
        request = self.request()
        request["bundles"] *= 2
        result = build_catalog(request)
        self.assertIn("FEDERATION_DUPLICATE_ID", result["diagnostics"])
        self.assertEqual(result["gardens"], [])
        self.assertEqual(result["records"], [])
        second = create_fixture(self.root / "second", "organization-garden")
        profile = deepcopy(second["profile"]); profile["base_uri"] = self.profile["base_uri"]
        second["bundle"] = build_federation(second["context"], profile)
        result = build_catalog(self.request(self.fixture, second))
        self.assertIn("FEDERATION_CANONICAL_CONFLICT", result["diagnostics"])
        self.assertEqual(result["records"], [])

    def test_unsafe_routes_invalid_inputs_and_budget_overflow_fail_without_echo(self):
        cases = json.loads((FEDERATION_FIXTURES / "negative-cases.json").read_text())
        for value in cases["unsafe_routes"]:
            with self.subTest(value=value), self.assertRaisesRegex(ContractError, "FEDERATION_ROUTE") as caught:
                public_url(value, base=True)
            self.assertNotIn(value, str(caught.exception))
        with self.assertRaisesRegex(ContractError, "FEDERATION_REQUEST"):
            build_catalog({"schema": "unknown", "private-root-canary": str(self.root)})
        context = self.refresh(budgets={**self.context.session["budgets"], "max_context_bytes": 16})
        with self.assertRaisesRegex(ContractError, "FEDERATION_BUDGET"):
            build_federation(context, self.profile)

    def test_cli_plan_apply_check_and_partial_catalog_share_services(self):
        shared = ["federation", "build", "--local-config", str(self.fixture["configuration"]),
                  "--scope", str(self.fixture["session_path"]), "--profile", str(self.fixture["profile_path"]),
                  "--output-directory", str(self.fixture["export"])]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([*shared, "--plan"]), 0)
        plan = json.loads(output.getvalue())
        self.assertEqual(list(self.fixture["export"].iterdir()), [])
        for arguments in [["--apply", "--plan-digest", plan["plan_sha256"]], ["--check"]]:
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main([*shared, *arguments]), 0)
            self.assertEqual(json.loads(output.getvalue()), self.bundle.descriptor)
        request = self.request(); request["bundles"].append({"directory": str(self.root / "private-missing-canary"),
                                                           "expected_revision": "sha256:" + "0" * 64})
        path = self.root / "catalog-request.json"; write_json(path, request)
        with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["federation", "catalog", "--input", str(path)]), 3)
        self.assertEqual(json.loads(output.getvalue())["status"], "partial")
        self.assertNotIn(str(self.root), output.getvalue() + errors.getvalue())

    def test_cli_demo_matches_committed_offline_proof_and_preserves_existing_workspaces(self):
        path = Path(__file__).parents[1] / "scripts/federation_demo.py"
        specification = importlib.util.spec_from_file_location("synthetic_federation_demo", path)
        demo = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(demo)
        report = demo.run_demo(self.root / "demo")
        self.assertEqual(report, json.loads((FEDERATION_FIXTURES / "expected-proof.json").read_text()))
        occupied = self.root / "human-workspace"; occupied.mkdir()
        marker = occupied / "human.txt"; marker.write_text("Keep this synthetic file.\n")
        with self.assertRaisesRegex(ValueError, "new or empty"):
            demo.run_demo(occupied)
        self.assertEqual(marker.read_text(), "Keep this synthetic file.\n")


if __name__ == "__main__":
    unittest.main()
