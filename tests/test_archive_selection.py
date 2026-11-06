"""Historical minimal archives and independent attachment normalization fixtures."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.conversation_archive import ConversationArchiveAdapter
from mindgarden.adapters.legacy_archive import LegacyConversationArchiveAdapter
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan, default_registry
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import search_payload
from mindgarden.domain.contracts import canonical_json, strict_json
from mindgarden.domain.sources import check_adapter_conformance
from mindgarden.domain.validation import ContractError
from tests.archive_fixture import FIXTURE_ROOT, package_bytes, package_members
from tests import test_conversation_archives as fixtures
from tests.support_v1 import write_json, write_session


def legacy_members():
    root = FIXTURE_ROOT / "legacy-v1"
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


class ArchiveSelectionTests(unittest.TestCase):
    def setUp(self):
        fixtures.ConversationArchiveTests.setUp(self)

    def test_catalog_only_and_selected_assets_keep_exact_message_evidence(self):
        adapter = ConversationArchiveAdapter(); captured = package_bytes(package_members())
        all_units = adapter.normalize(captured, {"manifest_version": "3.2.3"})
        metadata = {"manifest_version": "3.2.3", "attachment_selection": {"mode": "catalog-only", "asset_ids": []}}
        catalog = adapter.normalize(captured, metadata)
        self.assertFalse(any(":asset:" in unit.identity for unit in catalog.units))
        self.assertTrue(any(":asset-catalog:" in unit.identity for unit in catalog.units))
        self.assertEqual([u for u in all_units.units if ":message:" in u.identity], [u for u in catalog.units if ":message:" in u.identity])
        metadata["attachment_selection"] = {"mode": "selected", "asset_ids": ["asset-text"]}
        selected = adapter.normalize(captured, metadata)
        self.assertEqual([u for u in selected.units if ":asset:" in u.identity], [u for u in all_units.units if ":asset:" in u.identity])
        self.metadata["attachment_selection"] = {"mode": "catalog-only", "asset_ids": []}
        plan = fixtures.ConversationArchiveTests.plan(self)
        apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        self.assertIn(captured, [self.vault.get(item["content_id"]) for item in self.vault.audit()["objects"]])

    def test_selection_rejects_unknown_assets_and_still_verifies_unselected_bytes(self):
        self.metadata["attachment_selection"] = {"mode": "selected", "asset_ids": ["unknown"]}
        with self.assertRaisesRegex(ContractError, "ARCHIVE_SELECTION"):
            fixtures.ConversationArchiveTests.plan(self)
        self.metadata["attachment_selection"] = {"mode": "catalog-only", "asset_ids": []}
        members = package_members(); members["assets/attachment.txt"] = b"Changed bytes"
        with self.assertRaisesRegex(ContractError, "ARCHIVE_ASSETS"):
            fixtures.ConversationArchiveTests.plan(self, members)
        self.assertEqual(self.vault.audit()["objects"], [])

    def test_json_attachments_are_opaque_evidence_not_control_documents(self):
        members = package_members(); catalog = strict_json(members["ASSET-MANIFEST.json"])
        catalog["assets"][0]["archive_path"] = "assets/attachment.json"
        members["assets/attachment.json"] = members.pop("assets/attachment.txt")
        members["ASSET-MANIFEST.json"] = canonical_json(catalog)
        ConversationArchiveAdapter().normalize(package_bytes(members), {"manifest_version": "3.2.3"})

    def test_legacy_minimal_profile_curates_searchable_prompt_without_network(self):
        members = legacy_members(); self.input.write_bytes(package_bytes(members, inventory=False, prefix="synthetic-legacy/"))
        with patch("socket.socket", side_effect=AssertionError("Network attempted")), patch("subprocess.run", side_effect=AssertionError("Source executed")):
            check_adapter_conformance(LegacyConversationArchiveAdapter(), self.input.read_bytes(), self.metadata)
            plan = build_ingestion_plan(self.bindings, "synthetic-garden", "synthetic-vault", self.input,
                self.metadata, adapter_id="conversation-archive-v1", manifest_version="1.2.1")
            apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
            again = build_ingestion_plan(self.bindings, "synthetic-garden", "synthetic-vault", self.input,
                self.metadata, adapter_id="conversation-archive-v1", manifest_version="1.2.1")
            self.assertFalse(apply_ingestion(again, again.digest, self.bindings, "synthetic-vault"))
        evidence = next(item["evidence"] for item in plan.inputs["normalized_sources"] if item["metadata"].get("source_order") == 0)
        proposal = json.loads((FIXTURE_ROOT / "authored-plan.json").read_text())
        proposal["candidates"][0]["sources"] = evidence
        proposal_path = self.root / "legacy-curation.json"; write_json(proposal_path, proposal)
        curated = build_curation_plan(self.bindings, proposal_path); apply_curation(curated, curated.digest, self.bindings)
        session = self.root / "session.json"; write_session(session, self.configuration)
        result = search_payload(QueryContext.load(self.configuration, session), "evidence")
        self.assertEqual(result["results"][0]["sources"], evidence)

    def test_legacy_missing_identity_remains_snapshot_local(self):
        adapter = LegacyConversationArchiveAdapter(); first = legacy_members()
        before = adapter.normalize(package_bytes(first, inventory=False), self.metadata)
        second = deepcopy(first); document = strict_json(second["CONVERSATION.json"])
        document["messages"].append({"index":3,"role":"user","timestamp":None,"text":"Extra export evidence.","assets":[]})
        second["CONVERSATION.json"] = canonical_json(document)
        after = adapter.normalize(package_bytes(second, inventory=False), self.metadata)
        native_before = next(u for u in before.units if u.metadata.get("source_message_id"))
        native_after = next(u for u in after.units if u.metadata.get("source_message_id") == "synthetic-observed-id")
        self.assertEqual(native_before.identity, native_after.identity)
        self.assertEqual(native_before.content, native_after.content)
        fallback_before = next(u for u in before.units if u.metadata.get("identity_basis") == "snapshot-local-index")
        self.assertNotIn(fallback_before.identity, [u.identity for u in after.units])

    def test_historical_malformed_and_untested_versions_fail_safely(self):
        members = legacy_members(); document = strict_json(members["CONVERSATION.json"])
        document["messages"][0]["assets"] = [{"archive_path":"../unsafe","kind":"file","status":"archived"}]
        members["CONVERSATION.json"] = canonical_json(document)
        with self.assertRaisesRegex(ContractError, "ARCHIVE_PATH"):
            LegacyConversationArchiveAdapter().normalize(package_bytes(members, inventory=False), self.metadata)
        with self.assertRaisesRegex(ContractError, "ADAPTER_UNSUPPORTED"):
            default_registry().select("application/zip", "2.0.1")
