"""Synthetic binary selection, exact caption evidence and immutable originals."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.conversation_archive import ConversationArchiveAdapter
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.validation import ContractError
from tests.archive_fixture import diagram_members, package_bytes
from tests import test_conversation_archives as fixtures


SELECTION = {"mode": "selected", "asset_ids": ["asset-diagram"]}


class ArchiveDiagramTests(unittest.TestCase):
    def setUp(self):
        fixtures.ConversationArchiveTests.setUp(self)
        self.metadata["attachment_selection"] = SELECTION

    def plan(self, members=None):
        self.input.write_bytes(package_bytes(members or diagram_members()))
        return build_ingestion_plan(
            self.bindings,
            "synthetic-garden",
            "synthetic-vault",
            self.input,
            self.metadata,
            adapter_id="conversation-archive",
            manifest_version="2.0.2",
        )

    def test_binary_and_caption_remain_independent_exact_evidence(self):
        for version in ("2.0.0", "2.0.1", "2.0.2"):
            with (
                self.subTest(version=version),
                patch("socket.socket", side_effect=AssertionError("Network attempted")),
            ):
                members = diagram_members(version)
                bundle = ConversationArchiveAdapter().normalize(
                    package_bytes(members),
                    {"manifest_version": version, "attachment_selection": SELECTION},
                )
                diagram = next(
                    u
                    for u in bundle.units
                    if u.identity.endswith(":asset:asset-diagram")
                )
                self.assertEqual(diagram.content, members["assets/diagram.png"])
                self.assertEqual(diagram.media_type, "image/png")
                self.assertEqual(
                    diagram.metadata["original_selector"]["sha256"],
                    digest_bytes(diagram.content),
                )
                scratch = next(
                    u
                    for u in bundle.units
                    if u.identity.endswith(":asset-catalog:asset-scratch")
                )
                self.assertNotEqual(scratch.content, members["assets/scratch.png"])
                message = next(
                    u
                    for u in bundle.units
                    if u.metadata.get("message_id") == "message-prompt"
                )
                self.assertEqual(
                    message.locators, ("json:/content/0/text", "json:/content/2/text")
                )
                self.assertEqual(message.metadata["speaker"], "assistant")
                self.assertEqual(
                    diagram.metadata["asset"]["source_refs"][0]["id"], "message-prompt"
                )

    def test_selected_import_replays_overlaps_and_keeps_full_original(self):
        first = self.plan()
        apply_ingestion(first, first.digest, self.bindings, "synthetic-vault")
        self.assertFalse(
            apply_ingestion(first, first.digest, self.bindings, "synthetic-vault")
        )
        before = [s["source"] for s in first.inputs["normalized_sources"]]
        later = self.plan(diagram_members(revision=2, fallback=True))
        self.assertEqual(
            before, [s["source"] for s in later.inputs["normalized_sources"]]
        )
        apply_ingestion(later, later.digest, self.bindings, "synthetic-vault")
        blobs = [self.vault.get(o["content_id"]) for o in self.vault.audit()["objects"]]
        self.assertIn(package_bytes(diagram_members()), blobs)
        self.assertIn(diagram_members()["assets/diagram.png"], blobs)
        self.assertNotIn(diagram_members()["assets/scratch.png"], blobs)

    def test_unselected_corrupt_binary_still_rejected_and_stale_selection_cannot_apply(
        self,
    ):
        members = diagram_members()
        members["assets/scratch.png"] += b"corrupt"
        with self.assertRaisesRegex(ContractError, "ARCHIVE_ASSETS"):
            self.plan(members)
        self.assertEqual(self.vault.audit()["objects"], [])
        plan = self.plan()
        self.input.write_bytes(package_bytes(diagram_members(revision=2)))
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        self.assertEqual(self.vault.audit()["objects"], [])
