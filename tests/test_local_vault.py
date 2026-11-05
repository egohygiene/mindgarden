"""Immutable storage and exact portable source-reference conformance."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.filesystem import FilesystemVault
from mindgarden.application.bindings import LocalBindings
from mindgarden.application.storage import content_resolver
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.scope import local_scope
from mindgarden.domain.storage import ContentState
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.support_v1 import add_source, create_garden, write_json


class LocalVaultTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "garden"
        create_garden(self.workspace)
        self.vault = FilesystemVault(self.root / "vault", "synthetic-vault")
        self.configuration = self.root / "bindings.json"
        write_json(self.configuration, {"schema": "mindgarden.local-bindings/v1", "gardens": [{
            "id": "synthetic-garden", "root": str(self.workspace), "scope": local_scope()}],
            "vaults": [{"id": "synthetic-vault", "root": str(self.vault.root), "adapter": "filesystem"}],
            "revoked_sessions": []})

    def initialize(self):
        plan = self.vault.plan_init(digest_bytes(self.configuration.read_bytes()))
        self.vault.initialize(plan, plan["plan_sha256"])

    def test_plan_apply_is_digest_bound_and_idempotent(self):
        args = ["vault", "init", "--local-config", str(self.configuration), "--vault-id", "synthetic-vault"]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(args + ["--plan"]), 0)
        plan = json.loads(output.getvalue())
        self.assertFalse(self.vault.root.exists())
        self.assertNotIn(str(self.root), output.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(args + ["--apply", "--plan-digest", plan["plan_sha256"]]), 0)
        self.assertFalse(self.vault.initialize(plan, plan["plan_sha256"]))
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            self.vault.initialize(plan, "0" * 64)

    def test_duplicate_bytes_are_one_immutable_object_and_work_without_network(self):
        self.initialize()
        with patch("socket.socket", side_effect=AssertionError("Network access attempted")):
            first = self.vault.put(b"Synthetic immutable source.\n")
            second = self.vault.put(b"Synthetic immutable source.\n")
            self.assertEqual(first, second)
            self.assertEqual(self.vault.get(first), b"Synthetic immutable source.\n")
            self.assertEqual(self.vault.audit()["status"], "verified")
        self.assertEqual(len(self.vault.audit()["objects"]), 1)
        self.assertFalse(self.vault.capabilities()["encryption"])
        self.assertFalse(self.vault.capabilities()["remote"])

    def test_missing_unavailable_corrupted_and_unsupported_states(self):
        content_id = "sha256:" + "0" * 64
        self.assertEqual(self.vault.state(content_id), ContentState.UNAVAILABLE)
        self.initialize()
        self.assertEqual(self.vault.state(content_id), ContentState.MISSING)
        content_id = self.vault.put(b"Synthetic source")
        path = self.vault._object_path(content_id)
        path.chmod(0o600); path.write_bytes(b"Tampered synthetic source")
        self.assertEqual(self.vault.state(content_id), ContentState.CORRUPTED)
        with self.assertRaisesRegex(ContractError, "VAULT_CORRUPTED"):
            self.vault.get(content_id)
        self.assertEqual(self.vault.audit()["status"], "invalid")
        manifest = self.vault.manifest(); manifest["format_version"] = "unsupported"
        write_json(self.vault.root / "vault.json", manifest)
        self.assertEqual(self.vault.state(content_id), ContentState.UNSUPPORTED)

    def test_v1_source_ref_resolves_via_bindings_and_normal_cli(self):
        self.initialize()
        content = b"Exact synthetic evidence.\n"
        content_id = self.vault.put(content)
        record = add_source(self.workspace, content, vault_reference={"id": "synthetic-vault", "content_id": content_id})
        self.assertNotIn(str(self.root), json.dumps(record))
        self.assertEqual(inspect_garden(self.workspace).report()["status"], "incomplete")
        bindings = LocalBindings.load(self.configuration)
        snapshot = inspect_garden(self.workspace, content_resolver=content_resolver(bindings))
        self.assertEqual(snapshot.report()["status"], "valid")
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["validate", "--repository-root", str(self.workspace), "--local-config",
                                   str(self.configuration), "--format", "json"]), 0)
        self.assertNotIn(str(self.root), output.getvalue())

    def test_unowned_directories_and_symlinks_are_never_adopted(self):
        self.vault.root.mkdir()
        marker = self.vault.root / "unowned.txt"; marker.write_text("Synthetic untouched file.")
        plan = self.vault.plan_init("0" * 64)
        with self.assertRaises(ContractError):
            self.vault.initialize(plan, plan["plan_sha256"])
        self.assertEqual(marker.read_text(), "Synthetic untouched file.")
        marker.unlink(); self.initialize()
        (self.vault.root / "objects").symlink_to(self.root)
        with self.assertRaisesRegex(ContractError, "PATH_SYMLINK"):
            self.vault.put(b"Synthetic source")

    def test_content_identity_cannot_disagree_with_artifact_checksum(self):
        self.initialize()
        content_id = self.vault.put(b"Synthetic source")
        artifact = {"vault": {"id": "synthetic-vault", "content_id": content_id},
                    "sha256": "0" * 64, "size_bytes": 16}
        with self.assertRaisesRegex(ContractError, "CONTENT_ID"):
            content_resolver(LocalBindings.load(self.configuration))(artifact)
