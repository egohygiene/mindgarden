"""Synthetic-only local registry lifecycle, safety and compatibility evidence."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.registry_files import create_control, history_directory, preserve_snapshot, read_snapshot, registry_writer
from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.registry import apply_registry_plan, build_registry_plan, registry_report
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.registry import registry_location, selected_view, verify_session_view, view_reference
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.support_v1 import add_knowledge, create_garden
from tests import test_v1_contracts as contract_tests

FIXTURES = Path(__file__).parent / "fixtures/registry"


@unittest.skipUnless(sys.platform.startswith("linux"), "registry filesystem checkpoint supports Linux")
class RegistryTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = self.root / "private-config/registry.json"
        self.garden = self.root / "canonical"
        create_garden(self.garden)
        add_knowledge(self.garden, body="personal-content-canary\n")

    def apply(self, operation, request):
        plan = build_registry_plan(self.registry, operation, request)
        self.assertTrue(apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"]))
        return plan

    def initialize(self):
        return self.apply("init", {})

    def register(self, root=None, scope=None, garden=None):
        return self.apply("register", {"root": str(root or self.garden), "scope": scope or local_scope(),
                                       "expected_garden": garden, "expected_owners": []})

    def document(self):
        return json.loads(self.registry.read_text())

    def test_preview_and_saved_apply_are_private_idempotent_and_non_destructive(self):
        before = garden_fingerprint(self.garden)
        plan = build_registry_plan(self.registry, "init", {})
        self.assertFalse(self.registry.parent.exists())
        self.assertEqual(ContractRegistry().errors(plan.document(), "registry-plan"), [])
        self.assertTrue(apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"]))
        self.assertFalse(apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"]))
        self.assertEqual(self.registry.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.registry.parent.stat().st_mode & 0o777, 0o700)
        plan = self.register()
        self.assertFalse(apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"]))
        self.assertEqual(garden_fingerprint(self.garden), before)
        self.assertEqual(LocalBindings.load(self.registry).garden("synthetic-garden")["root"], self.garden)
        self.assertEqual(registry_report(self.registry, doctor=True)["status"], "ready")

    def test_registration_reads_only_manifest_and_unregistration_preserves_every_garden_file(self):
        self.initialize()
        before = {path.relative_to(self.garden): path.read_bytes() for path in self.garden.rglob("*") if path.is_file()}
        read = Path.read_bytes

        def manifest_only(path):
            if path.is_relative_to(self.garden) and path.name != "garden.json":
                raise AssertionError("Registration opened canonical content")
            return read(path)

        with patch.object(Path, "read_bytes", manifest_only):
            self.register()
            self.apply("unregister", {"garden": "synthetic-garden"})
        self.assertEqual(before, {path.relative_to(self.garden): path.read_bytes() for path in self.garden.rglob("*") if path.is_file()})
        self.assertEqual(self.document()["gardens"], [])

    def test_duplicate_identity_nested_ownership_and_scope_overrides_fail(self):
        self.initialize(); self.register()
        duplicate = self.root / "duplicate"; create_garden(duplicate)
        nested = self.garden / "nested"; create_garden(nested, "nested-garden")
        for root in (duplicate, nested):
            with self.subTest(root=root), self.assertRaisesRegex(ContractError, "REGISTRY_CONFLICT"):
                build_registry_plan(self.registry, "register", {"root": str(root), "scope": local_scope(), "expected_garden": None, "expected_owners": []})
        with self.assertRaisesRegex(ContractError, "SCOPE_CONFLICT"):
            build_registry_plan(self.registry, "register", {"root": str(self.garden), "scope": local_scope("public"), "expected_garden": None, "expected_owners": []})
        with self.assertRaisesRegex(ContractError, "REGISTRY_OWNER"):
            build_registry_plan(self.registry, "register", {"root": str(self.garden), "scope": local_scope(), "expected_garden": None, "expected_owners": ["different-owner"]})

    def test_scope_runtime_is_denied_before_any_root_probe(self):
        self.initialize()
        for scope in (local_scope("restricted"), local_scope("personal", persistence="encrypted-vault")):
            with patch("mindgarden.application.registry.explicit_root", side_effect=AssertionError("Unsupported root probed")):
                with self.assertRaisesRegex(ContractError, "REGISTRY_RUNTIME"):
                    build_registry_plan(self.registry, "register", {"root": "/restricted-root-canary", "scope": scope,
                                                                  "expected_garden": None, "expected_owners": []})

    def test_stale_digest_manifest_and_registry_do_not_commit(self):
        self.initialize()
        request = {"root": str(self.garden), "scope": local_scope(), "expected_garden": None, "expected_owners": []}
        plan = build_registry_plan(self.registry, "register", request)
        before = self.registry.read_bytes()
        with self.assertRaisesRegex(ContractError, "REGISTRY_PLAN_STALE"):
            apply_registry_plan(self.registry, plan.document(), "0" * 64)
        manifest = self.garden / ".garden/garden.json"
        value = json.loads(manifest.read_text()); value["title"] = "Changed synthetic title"
        manifest.write_bytes(canonical_json(value))
        with self.assertRaisesRegex(ContractError, "REGISTRY_PLAN_STALE"):
            apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"])
        self.assertEqual(before, self.registry.read_bytes())
        plan = build_registry_plan(self.registry, "register", request)
        value = self.document(); value["revoked_sessions"] = ["synthetic-revocation"]
        self.registry.write_bytes(canonical_json(value))
        with self.assertRaisesRegex(ContractError, "REGISTRY_PLAN_STALE"):
            apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"])
        self.assertEqual(self.document()["revoked_sessions"], ["synthetic-revocation"])

    def test_root_replacement_and_unsafe_control_locations_fail_closed(self):
        self.initialize()
        plan = build_registry_plan(self.registry, "register", {"root": str(self.garden), "scope": local_scope(),
                                                               "expected_garden": None, "expected_owners": []})
        old = self.root / "old-root"; self.garden.rename(old)
        shutil.copytree(old, self.garden)
        with self.assertRaisesRegex(ContractError, "REGISTRY_PLAN_STALE"):
            apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"])
        link = self.root / "link"; link.symlink_to(self.registry.parent, target_is_directory=True)
        with self.assertRaisesRegex(ContractError, "REGISTRY_PATH"):
            build_registry_plan(link / "registry.json", "init", {})
        repository = self.root / "repository"; (repository / ".git").mkdir(parents=True)
        (repository / ".git/HEAD").write_text("ref: refs/heads/synthetic\n")
        with self.assertRaisesRegex(ContractError, "REGISTRY_TRACKED"):
            build_registry_plan(repository / "registry.json", "init", {})
        with self.assertRaisesRegex(ContractError, "REGISTRY_PATH"):
            build_registry_plan(self.garden / ".garden/registry.json", "init", {})
        self.registry.chmod(0o644)
        with self.assertRaisesRegex(ContractError, "REGISTRY_PERMISSIONS"):
            registry_report(self.registry)

    def test_atomic_failure_preserves_previous_config_and_can_retry_exact_plan(self):
        self.initialize()
        plan = build_registry_plan(self.registry, "register", {"root": str(self.garden), "scope": local_scope(),
                                                               "expected_garden": None, "expected_owners": []})
        before = self.registry.read_bytes()
        with patch("mindgarden.adapters.registry_files.os.replace", side_effect=OSError("private-registry-path-canary")):
            with self.assertRaisesRegex(ContractError, "REGISTRY_IO") as caught:
                apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"])
        self.assertNotIn("private-registry-path-canary", str(caught.exception))
        self.assertEqual(self.registry.read_bytes(), before)
        self.assertEqual(read_snapshot(self.registry, digest_bytes(before))[1], before)
        self.assertTrue(apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"]))
        self.assertFalse(list(self.registry.parent.glob(".mindgarden-registry-*")))

    def test_kernel_writer_lease_releases_without_deleting_its_lock_file(self):
        self.initialize()
        plan = build_registry_plan(self.registry, "set-view", {"id": "empty-view", "gardens": []})
        with registry_writer(self.registry), self.assertRaisesRegex(ContractError, "REGISTRY_LOCKED"):
            apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"])
        self.assertTrue(apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"]))

    def test_private_directory_failure_keeps_diagnostics_free_of_local_paths(self):
        plan = build_registry_plan(self.registry, "init", {})
        with patch.object(Path, "mkdir", side_effect=PermissionError("private-registry-path-canary")):
            with self.assertRaisesRegex(ContractError, "REGISTRY_IO") as caught:
                apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"])
        self.assertNotIn("private-registry-path-canary", str(caught.exception))
        self.assertFalse(self.registry.exists())

    def test_full_history_is_preserved_and_existing_snapshot_can_be_verified(self):
        self.initialize()
        with patch("mindgarden.adapters.registry_files.MAX_SNAPSHOTS", 2):
            first = b"synthetic first history checkpoint"
            second = b"synthetic second history checkpoint"
            revision = preserve_snapshot(self.registry, first)
            preserve_snapshot(self.registry, second)
            self.assertEqual(preserve_snapshot(self.registry, first), revision)
            with self.assertRaisesRegex(ContractError, "REGISTRY_HISTORY"):
                preserve_snapshot(self.registry, b"do not silently prune history")
        self.assertEqual(read_snapshot(self.registry, revision)[1], first)
        self.assertEqual(len(list(history_directory(self.registry).glob("[!.]*.json"))), 2)

    def test_saved_plans_cannot_enter_restored_roots_or_replace_registry_state(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["registry", "init", "--registry", str(self.registry), "--output", str(self.registry)]), 3)
        self.assertFalse(self.registry.exists())
        self.assertIn("REGISTRY_LOCATION", errors.getvalue())
        self.initialize(); self.register()
        revision = digest_bytes(self.registry.read_bytes())
        self.apply("unregister", {"garden": "synthetic-garden"})
        output = self.garden / "control-plans/restore.json"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["registry", "restore", "--registry", str(self.registry), "--revision", revision,
                                   "--output", str(output)]), 3)
        self.assertFalse(output.parent.exists())
        self.assertIn("REGISTRY_LOCATION", errors.getvalue())

    def test_missing_roots_doctor_and_unregister_never_discover_or_delete_content(self):
        self.initialize(); self.register()
        moved = self.root / "moved-garden"; self.garden.rename(moved)
        report = registry_report(self.registry, doctor=True)
        self.assertEqual(report["status"], "degraded")
        self.assertNotIn(str(self.garden), json.dumps(report))
        with patch("mindgarden.application.registry.explicit_root", side_effect=AssertionError("Unregister probed content")):
            self.apply("unregister", {"garden": "synthetic-garden"})
        self.assertTrue((moved / ".garden/knowledge/synthetic-prompt.md").is_file())

    def test_views_prune_on_unregister_and_generations_cannot_revive_sessions(self):
        self.initialize(); self.register()
        self.apply("set-view", {"id": "focus", "gardens": ["synthetic-garden"]})
        before = self.registry.read_bytes(); revision = digest_bytes(before)
        view = selected_view(self.document(), "focus")
        session = {"registry_view": view_reference(view), "readable": [{"garden": "synthetic-garden"}]}
        verify_session_view(self.document(), session)
        self.apply("unregister", {"garden": "synthetic-garden"})
        with self.assertRaisesRegex(ContractError, "SESSION_VIEW_STALE"):
            verify_session_view(self.document(), session)
        current = self.document(); current["revoked_sessions"] = ["still-revoked"]
        self.registry.write_bytes(canonical_json(current))
        plan = self.apply("restore", {"revision": revision})
        self.assertIn("still-revoked", self.document()["revoked_sessions"])
        self.assertFalse(apply_registry_plan(self.registry, plan.document(), plan.document()["plan_sha256"]))
        with self.assertRaisesRegex(ContractError, "SESSION_VIEW_STALE"):
            verify_session_view(self.document(), session)
        self.assertEqual(selected_view(self.document(), "focus")["gardens"], ["synthetic-garden"])

    def test_corrupt_snapshots_and_stale_manifest_diagnostics_do_not_overwrite(self):
        self.initialize(); plan = self.register()
        old = plan.before_sha256
        backup = history_directory(self.registry) / (old + ".json")
        backup.write_bytes(b"corrupted")
        before = self.registry.read_bytes()
        with self.assertRaisesRegex(ContractError, "REGISTRY_SNAPSHOT"):
            build_registry_plan(self.registry, "restore", {"revision": old})
        self.assertEqual(before, self.registry.read_bytes())
        manifest = self.garden / ".garden/garden.json"
        value = json.loads(manifest.read_text()); value["title"] = "New title"
        manifest.write_bytes(canonical_json(value))
        self.assertEqual(registry_report(self.registry, doctor=True)["gardens"][0]["state"], "stale")

    def test_legacy_bindings_adoption_preserves_vaults_and_canonical_files(self):
        vault = self.root / "source-vault"; vault.mkdir(); original = vault / "original.bin"; original.write_bytes(b"Synthetic original\x00")
        legacy = {"schema": "mindgarden.local-bindings/v1", "gardens": [{"id": "synthetic-garden", "root": str(self.garden), "scope": local_scope()}],
                  "vaults": [{"id": "synthetic-vault", "root": str(vault), "adapter": "filesystem"}], "revoked_sessions": []}
        create_control(self.registry, canonical_json(legacy))
        before = garden_fingerprint(self.garden)
        self.apply("init", {})
        self.assertEqual(self.document()["vaults"], legacy["vaults"])
        self.assertEqual(original.read_bytes(), b"Synthetic original\x00")
        self.assertEqual(before, garden_fingerprint(self.garden))

    def test_schemas_match_reference_validator_and_paths_are_not_portable_records(self):
        self.initialize(); plan = self.register()
        contract_tests.V1ContractTests.setUpClass(); reference = contract_tests.V1ContractTests()
        for name, document in [("local-bindings", self.document()), ("registry", self.document()["registry"]), ("registry-plan", plan.document())]:
            with self.subTest(contract=name):
                self.assertEqual(ContractRegistry().errors(document, name), [])
                self.assertEqual(list(reference.validator(name).iter_errors(document)), [])
        self.assertEqual(plan.document()["publication"], "never-exportable")
        self.assertNotIn("personal-content-canary", json.dumps(plan.document()))

    def test_cli_plan_file_apply_list_inspect_doctor_and_unregister(self):
        plan_path = self.root / "plans/initial.json"
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["registry", "init", "--registry", str(self.registry), "--output", str(plan_path)]), 0)
        plan = json.loads(output.getvalue())
        self.assertFalse(self.registry.exists())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["registry", "apply", "--registry", str(self.registry), "--plan", str(plan_path), "--plan-digest", plan["plan_sha256"]]), 0)
        self.register()
        for command in ("list", "inspect", "doctor"):
            arguments = ["registry", command, "--registry", str(self.registry)]
            if command == "inspect":
                arguments += ["--garden-id", "synthetic-garden"]
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(arguments), 0)
            self.assertEqual(json.loads(output.getvalue())["classification"], "machine-local-control")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["registry", "apply", "--registry", str(self.registry), "--plan", str(plan_path), "--plan-digest", "0" * 64]), 3)
        self.assertNotIn(str(self.root), errors.getvalue())


class RegistryLocationTests(unittest.TestCase):
    def test_platform_locations_and_unsupported_filesystem_are_explicit(self):
        cases = json.loads((FIXTURES / "cases.json").read_text())["platforms"]
        for case in cases:
            with self.subTest(platform=case["platform"]):
                self.assertEqual(registry_location(case["platform"], case["user_home"], case["environment"]), case["expected"])
        with self.assertRaisesRegex(ContractError, "REGISTRY_LOCATION"):
            registry_location("linux", "/synthetic/user", {"XDG_CONFIG_HOME": "relative"})
        with patch("sys.platform", "win32"), self.assertRaisesRegex(ContractError, "REGISTRY_PLATFORM"):
            build_registry_plan(Path("/unavailable/registry.json"), "init", {})
