"""Reviewed migration preserves canonical references and both local stores."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.registry_files import read_snapshot, replace_registry
from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.vault_migration import build_vault_migration_plan
from mindgarden.domain.contracts import ContractRegistry, canonical_json
from mindgarden.domain.scope import local_scope
from mindgarden.domain.storage import StorageAdapters
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.migration_fixture import SyntheticLocalPort, create_fixture
from tests.support_v1 import add_knowledge, write_json
from tests.test_storage_adapters import SyntheticMemoryVault


class VaultMigrationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root / "case")

    def plan(self):
        return build_vault_migration_plan(
            LocalBindings.load(self.fixture["configuration"]),
            self.fixture["target_configuration"],
            "synthetic-vault",
            adapters=self.fixture["adapters"],
        )

    def extension(self):
        document = json.loads(self.fixture["target_configuration"].read_bytes())
        document["vaults"][0]["adapter"] = "synthetic-local"
        write_json(self.fixture["target_configuration"], document)

    def index(self):
        context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        return canonical_json(build_index(context))

    def test_exact_copy_rebind_and_replay_preserve_sources_and_query_bytes(self):
        original = self.fixture["vault"].export_bundle()
        before = self.index()
        garden = garden_fingerprint(self.fixture["workspace"])
        plan = self.plan()
        self.assertEqual(
            ContractRegistry().errors(plan.document(), "vault-migration-plan"), []
        )
        self.assertNotIn(str(self.root), json.dumps(plan.document()))
        self.assertEqual(self.fixture["target"].audit()["objects"], [])
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            self.assertTrue(plan.apply(plan.digest))
            self.assertFalse(plan.apply(plan.digest))
        self.assertEqual(self.fixture["target"].export_bundle(), original)
        self.assertEqual(self.fixture["vault"].export_bundle(), original)
        self.assertEqual(garden_fingerprint(self.fixture["workspace"]), garden)
        self.assertEqual(self.index(), before)
        _, previous = read_snapshot(
            self.fixture["configuration"],
            plan.document()["source_configuration_sha256"],
        )
        self.assertEqual(json.loads(previous), self.fixture["original_configuration"])

    def test_partial_copy_replans_to_same_digest_and_resumes_without_source_loss(self):
        self.extension()
        fault = {"calls": 0, "armed": True}
        adapters = self.fixture["adapters"]
        adapters.remove("synthetic-local")
        adapters.register(
            "synthetic-local",
            lambda binding, identity: SyntheticLocalPort(binding, identity, fault),
        )
        plan = self.plan()
        original = self.fixture["configuration"].read_bytes()
        with self.assertRaisesRegex(
            ContractError, "VAULT_MIGRATION_UNAVAILABLE"
        ) as error:
            plan.apply(plan.digest)
        self.assertNotIn("private detail", str(error.exception))
        self.assertEqual(self.fixture["configuration"].read_bytes(), original)
        copied = len(self.fixture["target"].audit()["objects"])
        self.assertGreater(copied, 0)
        self.assertLess(copied, len(plan.document()["objects"]))
        resumed = self.plan()
        self.assertEqual(resumed.digest, plan.digest)
        fault["armed"] = False
        self.assertTrue(resumed.apply(plan.digest))
        self.assertEqual(
            self.fixture["target"].export_bundle(),
            self.fixture["vault"].export_bundle(),
        )

    def test_independent_reopen_catches_lying_reads_before_rebind(self):
        self.extension()
        adapters = self.fixture["adapters"]
        adapters.remove("synthetic-local")
        generations = []

        def factory(binding, identity):
            port = SyntheticLocalPort(binding, identity)
            generations.append(port)
            if len(generations) >= 3:
                original_get = port.get
                port.get = lambda key: b"x" * len(original_get(key))
            return port

        adapters.register("synthetic-local", factory)
        plan = self.plan()
        before = self.fixture["configuration"].read_bytes()
        with self.assertRaisesRegex(ContractError, "VAULT_MIGRATION_CORRUPTED"):
            plan.apply(plan.digest)
        self.assertEqual(self.fixture["configuration"].read_bytes(), before)
        self.assertGreaterEqual(len(generations), 3)

    def test_stale_source_target_and_garden_inputs_cannot_select_target(self):
        for mutate in (
            lambda: self.fixture["vault"].put(b"New retained original"),
            lambda: add_knowledge(self.fixture["workspace"], "new-reviewed-note"),
            lambda: self.fixture["target_configuration"].write_bytes(
                self.fixture["target_configuration"].read_bytes() + b"\n"
            ),
        ):
            plan = self.plan()
            before = self.fixture["configuration"].read_bytes()
            mutate()
            with self.assertRaisesRegex(ContractError, "VAULT_MIGRATION_STALE"):
                plan.apply(plan.digest)
            self.assertEqual(self.fixture["configuration"].read_bytes(), before)
            self.assertEqual(self.fixture["target"].audit()["objects"], [])

    def test_old_bindings_and_overlapping_targets_fail_before_copy(self):
        bindings = self.fixture["bindings"]
        document = deepcopy(bindings.document)
        document["revoked_sessions"] = ["synthetic-changed-authority"]
        write_json(self.fixture["configuration"], document)
        with self.assertRaisesRegex(ContractError, "VAULT_MIGRATION_STALE"):
            build_vault_migration_plan(
                bindings, self.fixture["target_configuration"], "synthetic-vault"
            )
        target = json.loads(self.fixture["target_configuration"].read_bytes())
        target["vaults"][0]["root"] = str(self.fixture["workspace"] / "invalid-target")
        write_json(self.fixture["target_configuration"], target)
        with self.assertRaisesRegex(ContractError, "VAULT_DESTINATION"):
            self.plan()
        self.assertFalse(Path(target["vaults"][0]["root"]).exists())

    def test_uninitialized_target_and_changed_capabilities_fail_closed(self):
        marker = self.fixture["target"].root / "vault.json"
        content = marker.read_bytes()
        marker.unlink()
        with self.assertRaisesRegex(ContractError, "VAULT_MIGRATION_CORRUPTED"):
            self.plan()
        self.fixture["target"].root.rmdir()
        with self.assertRaisesRegex(ContractError, "VAULT_MIGRATION_UNAVAILABLE"):
            self.plan()
        self.fixture["target"].root.mkdir(mode=0o700)
        marker.write_bytes(content)
        marker.chmod(0o600)
        self.extension()
        plan = self.plan()
        capabilities = SyntheticLocalPort.capabilities
        with patch.object(
            SyntheticLocalPort,
            "capabilities",
            lambda port: {**capabilities(port), "changed": True},
        ):
            with self.assertRaisesRegex(ContractError, "VAULT_MIGRATION_STALE"):
                plan.apply(plan.digest)
        self.assertEqual(self.fixture["target"].audit()["objects"], [])

    def test_restricted_and_unproved_remote_or_encrypted_ports_are_unavailable(self):
        bindings = self.fixture["bindings"]
        bindings.gardens["synthetic-garden"]["scope"] = local_scope("restricted")
        with patch.object(
            self.fixture["adapters"],
            "open",
            side_effect=AssertionError("Provider opened"),
        ):
            with self.assertRaisesRegex(ContractError, "RUNTIME_UNVERIFIED"):
                build_vault_migration_plan(
                    bindings,
                    self.fixture["target_configuration"],
                    "synthetic-vault",
                    adapters=self.fixture["adapters"],
                )
        self.extension()
        capabilities = SyntheticLocalPort.capabilities
        for name in ("remote", "encryption"):
            with patch.object(
                SyntheticLocalPort,
                "capabilities",
                lambda port: {**capabilities(port), name: True},
            ):
                with self.assertRaisesRegex(ContractError, "RUNTIME_UNVERIFIED"):
                    self.plan()

    def test_advertised_backup_methods_must_exist(self):
        memory = SyntheticMemoryVault()
        capabilities = memory.capabilities()
        adapters = StorageAdapters()
        adapters.register("synthetic-memory", lambda binding, identity: memory)
        for capability in ("audit", "export", "restore"):
            with patch.object(
                memory, "capabilities", return_value={**capabilities, capability: True}
            ):
                with self.assertRaisesRegex(ContractError, "STORAGE_CAPABILITIES"):
                    adapters.open({"adapter": "synthetic-memory"}, "synthetic-vault")

    def test_target_extra_objects_are_retained_without_becoming_canonical(self):
        identity = self.fixture["target"].put(b"An unrelated retained target original")
        before = self.index()
        plan = self.plan()
        self.assertTrue(plan.apply(plan.digest))
        self.assertEqual(
            self.fixture["target"].get(identity),
            b"An unrelated retained target original",
        )
        self.assertEqual(self.index(), before)

    def test_wrong_put_identity_prevents_rebinding(self):
        self.extension()
        plan = self.plan()
        before = self.fixture["configuration"].read_bytes()

        def wrong_identity(port, content):
            port.storage.put(content)
            return "sha256:" + "0" * 64

        with patch.object(SyntheticLocalPort, "put", wrong_identity):
            with self.assertRaisesRegex(ContractError, "VAULT_MIGRATION_CORRUPTED"):
                plan.apply(plan.digest)
        self.assertEqual(self.fixture["configuration"].read_bytes(), before)

    def test_removed_target_adapter_never_falls_back_to_filesystem(self):
        self.extension()
        plan = self.plan()
        self.fixture["adapters"].remove("synthetic-local")
        with self.assertRaisesRegex(ContractError, "VAULT_MIGRATION_UNAVAILABLE"):
            plan.apply(plan.digest)
        self.assertEqual(self.fixture["target"].audit()["objects"], [])

    def test_target_private_control_permissions_are_checked_before_provider_access(
        self,
    ):
        self.fixture["target"].root.chmod(0o755)
        with patch.object(
            self.fixture["adapters"],
            "open",
            side_effect=AssertionError("Provider opened"),
        ):
            with self.assertRaisesRegex(ContractError, "REGISTRY_PERMISSIONS"):
                self.plan()
        self.fixture["target"].root.chmod(0o700)

    def test_factory_receives_an_isolated_binding_descriptor(self):
        original = {"adapter": "synthetic-memory", "root": self.root}
        memory = SyntheticMemoryVault()
        adapters = StorageAdapters()

        def factory(binding, identity):
            binding["root"] = self.root / "must-not-change-authority"
            return memory

        adapters.register("synthetic-memory", factory)
        adapters.open(original, "synthetic-vault")
        self.assertEqual(original["root"], self.root)

    def test_complete_offline_migration_and_recovery_matches_committed_golden(self):
        from scripts.vault_migration_demo import workflow

        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            report = workflow(self.root / "proof")
        expected = json.loads(
            (
                Path(__file__).parent / "fixtures/assets/migration-proof.json"
            ).read_bytes()
        )
        self.assertEqual(report, expected)

    def test_uncertain_commit_replays_without_opening_old_provider(self):
        plan = self.plan()

        def interrupted(*args, **kwargs):
            replace_registry(*args, **kwargs)
            raise OSError("Synthetic commit interruption")

        with patch(
            "mindgarden.application.vault_migration.replace_registry",
            side_effect=interrupted,
        ):
            with self.assertRaisesRegex(
                ContractError, "VAULT_MIGRATION_COMMIT_UNCERTAIN"
            ):
                plan.apply(plan.digest)
        with patch(
            "mindgarden.application.vault_migration.inventory",
            side_effect=AssertionError("Old provider opened"),
        ):
            self.assertFalse(plan.apply(plan.digest))
        self.assertEqual(
            self.fixture["target"].export_bundle(),
            self.fixture["vault"].export_bundle(),
        )

    def test_cli_requires_exact_review_and_keeps_private_paths_out_of_plans(self):
        arguments = [
            "vault",
            "migrate",
            "--local-config",
            str(self.fixture["configuration"]),
            "--target-local-config",
            str(self.fixture["target_configuration"]),
            "--vault-id",
            "synthetic-vault",
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(arguments + ["--plan"]), 0)
        plan = json.loads(output.getvalue())
        self.assertNotIn(str(self.root), output.getvalue())
        with (
            redirect_stdout(io.StringIO()) as output,
            redirect_stderr(io.StringIO()) as error,
        ):
            self.assertEqual(
                main(arguments + ["--apply", "--plan-digest", "0" * 64]), 3
            )
        self.assertEqual(output.getvalue(), "")
        self.assertNotIn(str(self.root), error.getvalue())
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(
                main(arguments + ["--apply", "--plan-digest", plan["plan_sha256"]]), 0
            )
        self.assertTrue(json.loads(output.getvalue())["applied"])


if __name__ == "__main__":
    unittest.main()
