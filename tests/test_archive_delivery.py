"""Packaging provenance is data, with runtime details confined to the original."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.conversation_archive import ConversationArchiveAdapter
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.domain.contracts import canonical_json, digest_bytes, strict_json
from mindgarden.domain.validation import ContractError
from tests.archive_fixture import (
    FIXTURE_ROOT,
    package_bytes,
    package_members,
    v2_members,
)
from tests.test_archive_continuation import CONTINUATION
from tests import test_conversation_archives as fixtures


def variants():
    for version in ("2.0.0", "2.0.1", "2.0.2"):
        yield version, v2_members(version, fallback=True)
    for version in ("3.2.2", "3.2.3"):
        for profile in ("full-source", "summary-journey"):
            yield version, package_members(profile, version, fallback=True)


def with_delivery(members, delivery):
    members = dict(members)
    manifest = strict_json(members["ARCHIVE-MANIFEST.json"])
    manifest["delivery"] = delivery
    members["ARCHIVE-MANIFEST.json"] = canonical_json(manifest)
    return members


class ArchiveDeliveryTests(unittest.TestCase):
    def setUp(self):
        fixtures.ConversationArchiveTests.setUp(self)

    def test_delivery_privacy_across_supported_source_profiles_preserves_exact_evidence(
        self,
    ):
        private = strict_json((FIXTURE_ROOT / "delivery-private.json").read_bytes())
        for version, members in variants():
            with self.subTest(
                version=version, profile=members.get("JOURNEY.md") is not None
            ):
                adapter = ConversationArchiveAdapter()
                original = adapter.normalize(
                    package_bytes(members), {"manifest_version": version}
                )
                changed = adapter.normalize(
                    package_bytes(with_delivery(members, private)),
                    {"manifest_version": version},
                )
                self.assertEqual(original.units, changed.units)
                self.assertEqual(original.transformations, changed.transformations)
                metadata = canonical_json(changed.metadata)
                self.assertNotIn(b"CANARY", metadata)
                self.assertNotIn(b"/synthetic/runtime", metadata)
                history = changed.metadata["delivery"]["attempts"]
                self.assertEqual(
                    [item["result"] for item in history],
                    ["failed-transient", "success"],
                )
                self.assertEqual(
                    [item["archive_created"] for item in history], [False, True]
                )
                self.assertEqual(history[0]["path_id"], "withheld")
                self.assertEqual(history[1]["path_id"], "fallback-local-filesystem")
                self.assertIn(
                    "attempt_extensions",
                    changed.metadata["delivery"]["metadata_withheld"],
                )

    def test_unknown_free_text_is_never_echoed_as_portable_delivery_metadata(self):
        version, members = next(variants())
        delivery = strict_json(members["ARCHIVE-MANIFEST.json"])["delivery"]
        for key in ("status", "method"):
            delivery[key] = "SYNTHETIC-PRIVATE-CANARY"
        for key in ("path_id", "result", "error_class"):
            delivery["attempts"][0][key] = "SYNTHETIC-PRIVATE-CANARY"
        bundle = ConversationArchiveAdapter().normalize(
            package_bytes(with_delivery(members, delivery)),
            {"manifest_version": version},
        )
        self.assertNotIn(b"CANARY", canonical_json(bundle.metadata))
        self.assertEqual(bundle.metadata["producer_validation"], "incomplete")
        self.assertEqual(bundle.metadata["full_producer_conformance"], "not-claimed")

    def test_import_retains_private_original_without_runtime_details_in_records_or_preview(
        self,
    ):
        private = strict_json((FIXTURE_ROOT / "delivery-private.json").read_bytes())
        original = package_bytes(with_delivery(v2_members("2.0.1"), private))
        self.input.write_bytes(original)
        with (
            patch("socket.socket", side_effect=AssertionError("Network attempted")),
            patch("subprocess.Popen", side_effect=AssertionError("Source executed")),
        ):
            plan = build_ingestion_plan(
                self.bindings,
                "synthetic-garden",
                "synthetic-vault",
                self.input,
                self.metadata,
                adapter_id="conversation-archive",
                manifest_version="2.0.1",
            )
            self.assertNotIn(b"CANARY", canonical_json(plan.document()))
            self.assertTrue(
                all(b"CANARY" not in content for content in plan.files.values())
            )
            apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        self.assertEqual(self.vault.get("sha256:" + digest_bytes(original)), original)
        self.assertIn(b"CANARY", original)
        self.assertEqual(
            list((self.workspace / ".garden/knowledge").glob("*.json")), []
        )

    def test_malformed_or_oversized_delivery_fails_without_echo_or_writes(self):
        base = strict_json(v2_members(fallback=True)["ARCHIVE-MANIFEST.json"])[
            "delivery"
        ]
        mutations = [
            {"attempts": base["attempts"] * 33},
            {"limitations": "SYNTHETIC-CANARY"},
            {"method": {"private": "SYNTHETIC-CANARY"}},
            {
                "attempts": [
                    {**base["attempts"][0], "archive_created": "SYNTHETIC-CANARY"}
                ]
            },
            {
                "attempts": [
                    {**base["attempts"][0], "path_id": "SYNTHETIC-CANARY" * 100}
                ]
            },
        ]
        for mutation in mutations:
            self.input.write_bytes(
                package_bytes(with_delivery(v2_members(), {**base, **mutation}))
            )
            with (
                self.subTest(fields=list(mutation)),
                self.assertRaisesRegex(ContractError, "ARCHIVE_DELIVERY") as error,
            ):
                build_ingestion_plan(
                    self.bindings,
                    "synthetic-garden",
                    "synthetic-vault",
                    self.input,
                    self.metadata,
                    adapter_id="conversation-archive",
                    manifest_version="2.0.2",
                )
            self.assertNotIn("CANARY", str(error.exception))
        self.assertEqual(self.vault.audit()["objects"], [])

    def test_known_v2_continuation_remains_summary_derived_without_invented_attribution(
        self,
    ):
        for version in ("2.0.0", "2.0.1", "2.0.2"):
            members = v2_members(version)
            members["CONTINUATION.md"] = CONTINUATION
            bundle = ConversationArchiveAdapter().normalize(
                package_bytes(members), {"manifest_version": version}
            )
            unit = next(
                unit
                for unit in bundle.units
                if unit.metadata.get("evidence_kind") == "continuation-state"
            )
            self.assertEqual(unit.content, CONTINUATION)
            self.assertTrue(unit.metadata["summary_derived"])
            self.assertNotIn("message_id", unit.metadata)
            self.assertNotIn("speaker", unit.metadata)
            self.assertEqual(
                unit.metadata["original_selector"]["sha256"], digest_bytes(CONTINUATION)
            )
