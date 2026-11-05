"""Portable backups, clean restore, relocation and non-destructive failure proof."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.filesystem import FilesystemVault
from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.storage import content_resolver
from mindgarden.application.vault_recovery import build_vault_recovery_plan, referenced_content
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.validation import ContractError
from mindgarden.domain.zip_package import read_zip
from mindgarden.interfaces.cli import main
from tests.archive_fixture import package_bytes
from tests.support_v1 import add_knowledge, write_json, write_session
from tests import test_source_adapters as source_tests


class VaultRecoveryTests(unittest.TestCase):
    def setUp(self):
        source_tests.SourceAdapterTests.setUp(self)
        imported = source_tests.SourceAdapterTests.plan(self)
        apply_ingestion(imported, imported.digest, self.bindings, "synthetic-vault")
        self.evidence = imported.inputs["normalized_sources"][0]["evidence"]
        add_knowledge(self.workspace, sources=self.evidence)
        self.session_path = self.root / "session.json"; write_session(self.session_path, self.configuration)
        self.backup = self.root / "backup.zip"

    def plan(self, operation, destination=None, **options):
        return build_vault_recovery_plan(self.bindings, "synthetic-vault", operation,
                                         destination or self.backup, **options)

    def test_deterministic_export_clean_restore_and_portable_references(self):
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            bundle = self.vault.export_bundle()
            self.assertEqual(bundle, self.vault.export_bundle())
            plan = self.plan("export")
            self.assertEqual(ContractRegistry().errors(plan.document(), "vault-recovery-plan"), [])
            self.assertNotIn(str(self.root), json.dumps(plan.document()))
            self.assertTrue(plan.apply(plan.digest)); self.assertFalse(plan.apply(plan.digest))
            destination = self.root / "restored"
            restore = self.plan("restore", destination, input_path=self.backup)
            self.assertTrue(restore.apply(restore.digest)); self.assertFalse(restore.apply(restore.digest))
        restored = FilesystemVault(destination, "synthetic-vault")
        self.assertEqual(restored.export_bundle(), bundle)
        self.assertEqual(restored.audit(referenced_content(self.bindings, "synthetic-vault"))["status"], "verified")
        self.assertFalse(restored.capabilities()["encryption"])
        self.assertFalse(restored.capabilities()["remote"])
        self.assertFalse(restored.capabilities()["destructive_delete"])

    def test_relocation_preserves_metadata_and_rebuilds_identical_index(self):
        context = QueryContext.load(self.configuration, self.session_path)
        before = canonical_json(build_index(context))
        original_garden = garden_fingerprint(self.workspace)
        original_bundle = self.vault.export_bundle()
        target = self.root / "relocated"
        plan = self.plan("relocate", target)
        self.assertTrue(plan.apply(plan.digest)); self.assertFalse(plan.apply(plan.digest))
        self.assertEqual(garden_fingerprint(self.workspace), original_garden)
        self.assertEqual(self.vault.export_bundle(), original_bundle)
        self.assertEqual(json.loads(self.configuration.read_text())["vaults"][0]["root"], str(target))
        with self.assertRaisesRegex(ContractError, "SESSION_CONFIGURATION"):
            build_index(context)
        moved_context = QueryContext.load(self.configuration, self.session_path)
        self.assertEqual(before, canonical_json(build_index(moved_context)))
        inspect_garden(self.workspace, content_resolver=content_resolver(LocalBindings.load(self.configuration))).require_valid()

    def test_missing_referenced_object_is_distinct_from_empty_verified_inventory(self):
        content_id = self.evidence[0]["source"]["revision"]
        self.vault._object_path(content_id).unlink()
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["vault", "audit", "--local-config", str(self.configuration),
                                   "--vault-id", "synthetic-vault"]), 3)
        audit = json.loads(output.getvalue())
        self.assertEqual(audit["coverage"], "inventory-and-supplied-references")
        self.assertTrue(any(item["content_id"] == content_id and item["state"] == "missing" for item in audit["objects"]))
        with self.assertRaisesRegex(ContractError, "VAULT_INTEGRITY"):
            self.plan("export")
        self.assertFalse(self.backup.exists())

    def test_stale_inventory_input_or_garden_never_selects_destination(self):
        plan = self.plan("export")
        self.vault.put(b"New unreferenced synthetic capture")
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            plan.apply(plan.digest)
        self.assertFalse(self.backup.exists())
        plan = self.plan("export"); plan.apply(plan.digest)
        destination = self.root / "restore-stale"
        restore = self.plan("restore", destination, input_path=self.backup)
        self.backup.write_bytes(self.backup.read_bytes() + b"modified")
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            restore.apply(restore.digest)
        self.assertFalse(destination.exists())
        plan = self.plan("relocate", self.root / "relocate-stale")
        add_knowledge(self.workspace, "new-note")
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            plan.apply(plan.digest)
        self.assertFalse(plan.destination.exists())

    def test_corrupt_unsafe_wrong_identity_and_incomplete_backups_fail_before_restore(self):
        members = read_zip(self.vault.export_bundle())
        object_path = next(path for path in members if path.startswith("objects/"))
        corrupted = dict(members); corrupted[object_path] = b"Tampered synthetic object"
        missing = dict(members); del missing[object_path]
        escaped = dict(members); escaped["../escape.txt"] = b"Synthetic traversal"
        wrong = dict(members); descriptor = json.loads(wrong["vault.json"]); descriptor["id"] = "wrong-vault"
        wrong["vault.json"] = canonical_json(descriptor)
        for index, candidate in enumerate((corrupted, missing, escaped, wrong)):
            self.backup.write_bytes(package_bytes(candidate))
            destination = self.root / ("invalid-restore-" + str(index))
            with self.assertRaises(ContractError):
                self.plan("restore", destination, input_path=self.backup)
            self.assertFalse(destination.exists())

    def test_unowned_occupied_nested_and_linked_destinations_are_preserved(self):
        marker_root = self.root / "unowned"; marker_root.mkdir()
        marker = marker_root / "human.txt"; marker.write_text("Synthetic human-owned data.")
        with self.assertRaises(ContractError):
            self.plan("relocate", marker_root)
        self.assertEqual(marker.read_text(), "Synthetic human-owned data.")
        for destination in (self.workspace / "vault", self.vault.root / "nested"):
            with self.assertRaises(ContractError):
                self.plan("relocate", destination)
        linked = self.root / "linked"; linked.symlink_to(marker_root, target_is_directory=True)
        with self.assertRaisesRegex(ContractError, "VAULT_DESTINATION"):
            self.plan("relocate", linked)

    def test_failed_rebind_retains_verified_copy_and_original_for_same_plan_retry(self):
        destination = self.root / "relocated"
        plan = self.plan("relocate", destination)
        original_bindings = self.configuration.read_bytes()
        with patch("mindgarden.application.vault_recovery.replace_bindings", side_effect=OSError("Synthetic rebind failure")):
            with self.assertRaises(OSError):
                plan.apply(plan.digest)
        self.assertEqual(self.configuration.read_bytes(), original_bindings)
        self.assertEqual(FilesystemVault(destination, "synthetic-vault").export_bundle(), self.vault.export_bundle())
        self.assertTrue(plan.apply(plan.digest))
        self.assertTrue(self.vault.root.is_dir())

    def test_writer_lease_releases_after_error_and_rejects_concurrent_mutation(self):
        with self.vault.exclusive():
            with self.assertRaisesRegex(ContractError, "VAULT_BUSY"):
                self.vault.put(b"Concurrent synthetic mutation")
        self.assertEqual(self.vault.get(self.vault.put(b"After lease")), b"After lease")

    def test_cli_export_restore_and_relocate_use_reviewed_plan_digests(self):
        for operation, extra in (
                ("export", ["--output", str(self.backup)]),
                ("restore", ["--input", str(self.backup), "--destination", str(self.root / "restored-cli")]),
                ("relocate", ["--destination", str(self.root / "relocated-cli")])):
            arguments = ["vault", operation, "--local-config", str(self.configuration), "--vault-id", "synthetic-vault", *extra]
            with redirect_stdout(io.StringIO()) as preview:
                self.assertEqual(main(arguments + ["--plan"]), 0)
            document = json.loads(preview.getvalue())
            with redirect_stdout(io.StringIO()) as applied:
                self.assertEqual(main(arguments + ["--apply", "--plan-digest", document["plan_sha256"]]), 0)
            self.assertEqual(ContractRegistry().errors(json.loads(applied.getvalue()), "vault-recovery-plan"), [])
