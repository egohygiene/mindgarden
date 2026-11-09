"""Pinned producer/consumer boundary without importing capture providers."""

from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_STORED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mindgarden.adapters.captured_source import CapturedSourceAdapter, MANIFEST
from mindgarden.application.ingestion import apply_ingestion, default_registry
from mindgarden.application.storage import content_resolver
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.sources import check_adapter_conformance, normalize_source
from mindgarden.domain.validation import ContractError
from tests import test_source_adapters as source_fixtures

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/captured-source/synthetic-source.zip"


def package(members):
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        for name, content in sorted(members.items()):
            archive.writestr(name, content)
    return output.getvalue()


def unpack(content):
    with ZipFile(BytesIO(content)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


class CapturedSourceTests(unittest.TestCase):
    def setUp(self):
        source_fixtures.SourceAdapterTests.setUp(self)
        self.input.write_bytes(FIXTURE.read_bytes())
        self.metadata.update(
            media_type="application/vnd.mindcap.captured-source+zip",
            source_id="synthetic-reference-source",
        )
        self.adapter = CapturedSourceAdapter()

    def plan(self):
        return source_fixtures.SourceAdapterTests.plan(self, manifest_version="1")

    def test_pinned_wire_and_default_selection_preserve_inert_exact_evidence(self):
        with (
            patch("socket.socket", side_effect=AssertionError("Network attempted")),
            patch("subprocess.run", side_effect=AssertionError("Process attempted")),
        ):
            self.assertIsInstance(
                default_registry().select(self.metadata["media_type"], "1"),
                CapturedSourceAdapter,
            )
            report = check_adapter_conformance(
                self.adapter, self.input.read_bytes(), self.metadata
            )
            normalized = normalize_source(
                self.adapter, self.input.read_bytes(), self.metadata
            )
        self.assertEqual(len(report["units"]), 2)
        self.assertIn(
            b"javascript:synthetic_do_not_execute()",
            b"".join(unit.content for unit in normalized.units),
        )
        self.assertEqual(
            normalized.metadata["producer"]["revision"],
            "7ee766c1c34adad239fc602499f624979a2d9cac",
        )
        self.assertFalse(normalized.metadata["capabilities"]["knowledge_review"])

    def test_same_plan_apply_repeat_and_new_observation_do_not_duplicate_units(self):
        plan = self.plan()
        self.assertTrue(
            apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        )
        self.assertFalse(
            apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        )
        before = inspect_garden(
            self.workspace, content_resolver=content_resolver(self.bindings)
        ).require_valid()
        originals = {
            identity: canonical_json(record)
            for identity, record in before.records.items()
        }
        members = unpack(self.input.read_bytes())
        manifest = json.loads(members[MANIFEST])
        manifest["captured_at"] = "2026-11-05T00:00:00Z"
        manifest["previous_bundle_sha256"] = digest_bytes(self.input.read_bytes())
        members[MANIFEST] = canonical_json(manifest)
        self.input.write_bytes(package(members))
        second = self.plan()
        apply_ingestion(second, second.digest, self.bindings, "synthetic-vault")
        after = inspect_garden(
            self.workspace, content_resolver=content_resolver(self.bindings)
        ).require_valid()
        normalized = [
            r
            for r in after.records.values()
            if r["schema"] == "mindgarden.source/v1" and r["kind"] == "normalized"
        ]
        self.assertEqual(len(normalized), 2)
        self.assertTrue(
            all(
                canonical_json(after.records[key]) == content
                for key, content in originals.items()
            )
        )
        self.assertEqual(
            list((self.workspace / ".garden/knowledge").glob("*.json")), []
        )

    def test_changed_plan_rejected_before_vault_writes(self):
        plan = self.plan()
        members = unpack(self.input.read_bytes())
        manifest = json.loads(members[MANIFEST])
        manifest["captured_at"] = "2026-11-05T00:00:00Z"
        members[MANIFEST] = canonical_json(manifest)
        self.input.write_bytes(package(members))
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        self.assertEqual(self.vault.audit()["objects"], [])

    def test_raw_corruption_extra_members_duplicate_units_and_bad_lineage_fail(self):
        original = unpack(self.input.read_bytes())
        for kind in (
            "corrupt",
            "extra",
            "duplicate",
            "lineage",
            "locator",
            "capability",
        ):
            members = deepcopy(original)
            manifest = json.loads(members[MANIFEST])
            if kind == "corrupt":
                members["raw/references.json"] = b"Synthetic corruption"
            if kind == "extra":
                members["extra.txt"] = b"Synthetic extra member"
            if kind == "duplicate":
                manifest["units"].append(deepcopy(manifest["units"][0]))
            if kind == "lineage":
                manifest["units"][0]["original_members"] = ["missing"]
            if kind == "locator":
                manifest["units"][0]["locators"] = ["json:/missing"]
            if kind == "capability":
                manifest["capabilities"]["knowledge_review"] = True
            members[MANIFEST] = canonical_json(manifest)
            with self.subTest(kind=kind), self.assertRaises(ContractError):
                normalize_source(self.adapter, package(members), self.metadata)

    def test_partial_empty_capture_is_not_reported_as_complete_source(self):
        members = unpack(self.input.read_bytes())
        manifest = json.loads(members[MANIFEST])
        manifest.update(
            units=[], status="partial", warnings=["CAPTURE_WARNINGS_PRESENT"]
        )
        members[MANIFEST] = canonical_json(manifest)
        result = normalize_source(self.adapter, package(members), self.metadata)
        self.assertEqual(result.units, ())
        self.assertEqual(result.metadata["status"], "partial")
        self.assertFalse(result.metadata["capabilities"]["delta"])

    def test_private_plan_has_no_physical_paths_or_public_source_records(self):
        preview = self.plan().document()
        self.assertNotIn(str(self.root), json.dumps(preview))
        self.assertEqual(ContractRegistry().errors(preview, "change-plan"), [])
        self.assertTrue(
            all(
                r["visibility"] == "private"
                for name, content in self.plan().files.items()
                if name.startswith("sources/")
                for r in [json.loads(content)]
            )
        )


if __name__ == "__main__":
    unittest.main()
