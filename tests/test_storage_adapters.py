"""Explicit removable storage adapters, verified bytes and unsupported capabilities."""

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.assets import build_asset_manifest
from mindgarden.application.bindings import LocalBindings
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.storage import content_resolver, open_vault
from mindgarden.application.vault_recovery import build_vault_recovery_plan
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.scope import local_scope
from mindgarden.domain.storage import ContentState, StorageAdapters
from mindgarden.domain.validation import ContractError
from tests import test_local_vault as fixtures
from tests.support_v1 import TIME, write_json, write_session


class SyntheticMemoryVault:
    """Fixture port, deliberately incapable of backup, migration or encryption."""

    def __init__(self): self.objects = {}

    def capabilities(self):
        return {"schema": "mindgarden.storage-capabilities/v1", "adapter": "synthetic-memory", "immutable_put": True,
                "read": True, "checksum_verification": False, "audit": False, "export": False, "restore": False,
                "relocate": False, "encryption": False, "remote": False, "destructive_delete": False}

    def state(self, content_id): return ContentState.AVAILABLE if content_id in self.objects else ContentState.MISSING

    def get(self, content_id):
        if content_id not in self.objects: raise ContractError("STORAGE_UNAVAILABLE: synthetic content unavailable")
        return self.objects[content_id]

    def put(self, content):
        identity = "sha256:" + digest_bytes(content)
        self.objects.setdefault(identity, content)
        return identity


class StorageAdapterTests(unittest.TestCase):
    def setUp(self):
        fixtures.LocalVaultTests.setUp(self)
        document = json.loads(self.configuration.read_bytes()); document["vaults"][0]["adapter"] = "synthetic-memory"
        write_json(self.configuration, document)
        self.bindings = LocalBindings.load(self.configuration)
        self.memory = SyntheticMemoryVault(); self.adapters = StorageAdapters()
        self.adapters.register("synthetic-memory", lambda binding, identity: self.memory)
        self.input = self.root / "synthetic.txt"; self.input.write_bytes(b"Wholly synthetic extension source.\n")
        self.metadata = {"source_id": "synthetic-extension", "title": "Synthetic extension", "origin": "urn:synthetic:storage",
                         "owner": "synthetic-owner", "rights": "Synthetic only.", "captured_at": TIME, "media_type": "text/plain"}

    def import_source(self):
        plan = build_ingestion_plan(self.bindings, "synthetic-garden", "synthetic-vault", self.input, self.metadata,
                                    storage_adapters=self.adapters)
        apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault", storage_adapters=self.adapters)
        return plan

    def test_extension_registration_ingestion_query_and_removal_require_no_domain_change(self):
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            self.import_source()
            snapshot = inspect_garden(self.workspace, content_resolver=content_resolver(self.bindings, adapters=self.adapters)).require_valid()
            self.assertEqual(snapshot.count, 2)
            path = self.root / "session.json"; session = write_session(path, self.configuration)
            session["projections"].append("assets"); session["allowed_review_states"].append("unreviewed")
            write_json(path, bind_session_revisions(self.configuration, session))
            context = QueryContext.load(self.configuration, path, storage_adapters=self.adapters)
            self.assertEqual(len(build_asset_manifest(context)["assets"]), 1)
            self.assertFalse(open_vault(self.bindings, "synthetic-vault", adapters=self.adapters).capabilities()["export"])
            self.adapters.remove("synthetic-memory")
            with self.assertRaisesRegex(ContractError, "STORAGE_UNSUPPORTED"):
                open_vault(self.bindings, "synthetic-vault", adapters=self.adapters)
            with self.assertRaisesRegex(ContractError, "QUERY_INTEGRITY"): context.snapshots()
            self.assertEqual(len(self.memory.objects), 1)

    def test_core_verifies_returned_bytes_even_when_adapter_claims_success(self):
        self.import_source(); identity = next(iter(self.memory.objects)); original = self.memory.objects[identity]
        self.memory.objects[identity] = b"x" * len(original)
        artifact = {"vault": {"id": "synthetic-vault", "content_id": identity}, "sha256": identity[7:], "size_bytes": len(original)}
        with self.assertRaisesRegex(ContractError, "CONTENT_HASH"):
            content_resolver(self.bindings, adapters=self.adapters)(artifact)

    def test_absent_adapter_does_not_fall_back_or_claim_backup_migration(self):
        with self.assertRaisesRegex(ContractError, "STORAGE_UNSUPPORTED"): open_vault(self.bindings, "synthetic-vault")
        with self.assertRaisesRegex(ContractError, "STORAGE_UNSUPPORTED"):
            build_vault_recovery_plan(self.bindings, "synthetic-vault", "relocate", self.root / "destination")
        self.assertFalse((self.root / "destination").exists())

    def test_malformed_capabilities_duplicate_registration_and_read_only_put_fail(self):
        with self.assertRaisesRegex(ContractError, "STORAGE_ADAPTER"):
            self.adapters.register("synthetic-memory", lambda binding, identity: self.memory)
        capabilities = self.memory.capabilities()
        with patch.object(self.memory, "capabilities", return_value={**capabilities, "read": "yes"}):
            with self.assertRaisesRegex(ContractError, "STORAGE_CAPABILITIES"):
                open_vault(self.bindings, "synthetic-vault", adapters=self.adapters)
        plan = build_ingestion_plan(self.bindings, "synthetic-garden", "synthetic-vault", self.input, self.metadata,
                                    storage_adapters=self.adapters)
        with patch.object(self.memory, "capabilities", return_value={**capabilities, "immutable_put": False}):
            with self.assertRaisesRegex(ContractError, "STORAGE_UNSUPPORTED"):
                apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault", storage_adapters=self.adapters)
        self.assertEqual(self.memory.objects, {})

    def test_denied_encrypted_scope_never_opens_an_extension_provider(self):
        path = self.root / "session.json"; session = write_session(path, self.configuration)
        session["allowed_visibilities"] = ["restricted"]; session["request_scope"] = local_scope("restricted")
        write_json(path, bind_session_revisions(self.configuration, session))
        with patch.object(self.adapters, "open", side_effect=AssertionError("Denied provider opened")):
            context = QueryContext.load(self.configuration, path, storage_adapters=self.adapters)
            self.assertEqual(context.snapshots(), {})
            self.assertFalse(context.allows_scope(local_scope("restricted")))
            self.assertEqual(context.output_scope([local_scope("restricted")])["persistence"], "encrypted-vault")
