"""Versioned v2 source fixtures and independent final-package verification."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.conversation_archive import ConversationArchiveAdapter
from mindgarden.application.ingestion import (
    apply_ingestion,
    build_ingestion_plan,
    default_registry,
)
from mindgarden.domain.contracts import canonical_json, digest_bytes, strict_json
from mindgarden.domain.sources import check_adapter_conformance
from mindgarden.domain.validation import ContractError
from mindgarden.domain.zip_package import read_zip, verify_inventory
from tests.archive_fixture import FIXTURE_ROOT, package_bytes, package_members
from tests import test_conversation_archives as fixtures


def v2_members(version="2.0.2", revision=1, fallback=False):
    members = package_members()
    members.pop("routing/PLAN.json")
    members.pop("routing/PLAN.md")
    manifest = strict_json(
        (FIXTURE_ROOT / "v2-source/ARCHIVE-MANIFEST.json").read_bytes()
    )
    manifest.update(spec_version=version, archive_revision=revision)
    if fallback:
        manifest["delivery"].update(
            method="fallback-local-packager",
            attempts=[
                {
                    "path_id": "primary-file-runtime",
                    "result": "failed-transient",
                    "error_class": "transport-or-wrapper-error",
                    "archive_created": False,
                },
                {
                    "path_id": "fallback-local-filesystem",
                    "result": "success",
                    "error_class": None,
                    "archive_created": True,
                },
            ],
        )
    members["ARCHIVE-MANIFEST.json"] = canonical_json(manifest)
    return members


class ArchiveV2Tests(unittest.TestCase):
    def setUp(self):
        fixtures.ConversationArchiveTests.setUp(self)

    def plan(self, members, version):
        self.input.write_bytes(package_bytes(members))
        return build_ingestion_plan(
            self.bindings,
            "synthetic-garden",
            "synthetic-vault",
            self.input,
            self.metadata,
            adapter_id="conversation-archive",
            manifest_version=version,
        )

    def test_version_matrix_retains_exact_evidence_and_attachment_selection(self):
        adapter = ConversationArchiveAdapter()
        for version in ("2.0.0", "2.0.1", "2.0.2"):
            self.assertIsInstance(
                default_registry().select("application/zip", version),
                ConversationArchiveAdapter,
            )
            for mode in ("all", "catalog-only", "selected"):
                with (
                    self.subTest(version=version, mode=mode),
                    patch("socket.socket", side_effect=AssertionError("Network")),
                    patch(
                        "subprocess.run", side_effect=AssertionError("Source executed")
                    ),
                ):
                    metadata = {
                        "manifest_version": version,
                        "attachment_selection": {
                            "mode": mode,
                            "asset_ids": ["asset-text"] if mode == "selected" else [],
                        },
                    }
                    members = v2_members(version)
                    result = check_adapter_conformance(
                        adapter,
                        package_bytes(members, prefix="synthetic-unit/"),
                        metadata,
                    )
                    # Conformance checks determinism; inspect the same independently normalized view.
                    self.assertIsNotNone(result)
                    normalized = adapter.normalize(
                        package_bytes(members, prefix="synthetic-unit/"), metadata
                    )
                    message = next(
                        u
                        for u in normalized.units
                        if u.metadata.get("message_id") == "message-prompt"
                    )
                    self.assertEqual(
                        message.content,
                        canonical_json(
                            strict_json(members["CONVERSATION.json"])["messages"][1]
                        ),
                    )
                    self.assertEqual(message.metadata["speaker"], "assistant")
                    self.assertEqual(message.locators, ("json:/content/0/text",))
                    self.assertEqual(
                        message.metadata["original_selector"]["member_sha256"],
                        digest_bytes(members["CONVERSATION.json"]),
                    )
                    self.assertEqual(
                        normalized.metadata["full_producer_conformance"], "not-claimed"
                    )
                    self.assertEqual(len(normalized.metadata["branches"]), 2)

    def test_overlapping_v2_and_v3_exports_keep_unit_identity_and_original_observations(
        self,
    ):
        first = self.plan(v2_members("2.0.0"), "2.0.0")
        apply_ingestion(first, first.digest, self.bindings, "synthetic-vault")
        second = self.plan(v2_members("2.0.2", revision=2), "2.0.2")
        apply_ingestion(second, second.digest, self.bindings, "synthetic-vault")
        third = self.plan(package_members(revision=3), "3.2.3")
        self.assertEqual(
            [s["source"] for s in first.inputs["normalized_sources"]],
            [s["source"] for s in second.inputs["normalized_sources"]],
        )
        self.assertEqual(
            [s["source"] for s in first.inputs["normalized_sources"]],
            [s["source"] for s in third.inputs["normalized_sources"]],
        )
        apply_ingestion(third, third.digest, self.bindings, "synthetic-vault")
        self.assertFalse(
            apply_ingestion(third, third.digest, self.bindings, "synthetic-vault")
        )

    def test_two_pass_primary_and_fallback_packages_reopen_without_recursive_hash(self):
        for fallback in (False, True):
            members = v2_members("2.0.1", fallback=fallback)
            first = read_zip(package_bytes(members))
            verify_inventory(first)
            report = strict_json(members["VALIDATION.json"])
            report["checks"].append(
                {
                    "id": "first-package-reopen",
                    "status": "pass",
                    "method": "independent ZIP/CRC/SHA-256 reopen",
                    "evidence": [],
                    "notes": [],
                }
            )
            members["VALIDATION.json"] = canonical_json(report)
            final_zip = package_bytes(members)
            final = read_zip(final_zip)
            self.assertEqual(
                verify_inventory(final)["VALIDATION.json"],
                digest_bytes(members["VALIDATION.json"]),
            )
            self.assertNotIn("MANIFEST.sha256", verify_inventory(final))
            self.assertEqual(
                len(digest_bytes(final_zip)), 64
            )  # final ZIP digest stays external
            normalized = ConversationArchiveAdapter().normalize(
                final_zip, {"manifest_version": "2.0.1"}
            )
            if not fallback:
                ordinary = [(u.identity, u.content) for u in normalized.units]
            else:
                self.assertEqual(
                    ordinary, [(u.identity, u.content) for u in normalized.units]
                )
                self.assertEqual(
                    [
                        a["archive_created"]
                        for a in normalized.metadata["delivery"]["attempts"]
                    ],
                    [False, True],
                )

    def test_malformed_controls_layers_and_unselected_assets_fail_before_writes(self):
        cases = []
        for name, key, value in (
            ("ARCHIVE-MANIFEST.json", "schema_version", "2.1"),
            ("ARCHIVE-MANIFEST.json", "spec_version", "2.0.3"),
            ("ARCHIVE-MANIFEST.json", "options", {}),
            ("CONVERSATION.json", "schema_version", "3.0"),
            ("VALIDATION.json", "overall", "fail"),
        ):
            members = v2_members()
            obj = strict_json(members[name])
            obj[key] = value
            members[name] = canonical_json(obj)
            cases.append(members)
        members = v2_members()
        del members["VISUAL-INSIGHTS.md"]
        cases.append(members)
        members = v2_members()
        members["assets/attachment.txt"] = b"changed"
        cases.append(members)
        self.metadata["attachment_selection"] = {
            "mode": "catalog-only",
            "asset_ids": [],
        }
        for members in cases:
            with (
                self.subTest(digest=digest_bytes(package_bytes(members))),
                self.assertRaises(ContractError),
            ):
                self.plan(members, "2.0.2")
        self.assertEqual(self.vault.audit()["objects"], [])

    def test_changed_package_invalidates_plan_before_vault_writes(self):
        plan = self.plan(v2_members(), "2.0.2")
        self.input.write_bytes(package_bytes(v2_members(revision=2)))
        with self.assertRaises(ContractError):
            apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        self.assertEqual(self.vault.audit()["objects"], [])
