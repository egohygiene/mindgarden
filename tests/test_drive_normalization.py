"""Mapped captured CSV handoff, exact occurrences, stale plans and recovery."""

from contextlib import redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.drive_source import DriveCaptureAdapter
from mindgarden.adapters.filesystem import FilesystemVault
from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.consultation import plan_packet
from mindgarden.application.drive_capture import collect
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import digest_bytes, read_object
from mindgarden.domain.packet_dependencies import reconcile_packet
from mindgarden.domain.sources import check_adapter_conformance
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.consultation_fixture import cli
from tests.mapped_drive_fixture import (
    create_fixture,
    ingest_arguments,
    normalization,
    packet_inputs,
)
from tests.support_v1 import write_json


class DriveNormalizationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root)
        self.provider = self.fixture["provider"]
        self.checkpoint = self.root / "capture-checkpoint.json"

    def capture(self):
        return collect(
            self.fixture["binding"],
            self.provider,
            self.fixture["vault"],
            self.checkpoint,
        )[0]

    def normalized(self, content, configuration=None):
        return DriveCaptureAdapter().normalize(
            content,
            {
                "source_scope": self.fixture["binding"]["scope"],
                "drive_normalization": normalization()
                if configuration is None
                else configuration,
            },
        )

    def apply(self, archive):
        arguments = ingest_arguments(self.fixture, archive)
        preview = cli(arguments)
        cli(arguments + ["--apply", "--plan-digest", preview["plan_sha256"]])
        return arguments, preview

    def test_layouts_overlap_and_every_provider_occurrence_keep_exact_original_spans(
        self,
    ):
        archive = self.capture()
        bundle = self.normalized(archive)
        self.assertEqual(len(bundle.units), 8)
        self.assertEqual(
            {item["adapter"] for item in bundle.metadata["normalization_states"]},
            {"mapped-ledger-csv"},
        )
        occurrences = [
            item
            for unit in bundle.units
            for item in unit.metadata["provider_occurrences"]
        ]
        self.assertEqual(len(occurrences), 9)
        for item in occurrences:
            raw = self.provider.data[item["provider_file_id"]]
            self.assertEqual(item["member_sha256"], digest_bytes(raw))
            span = item["original_utf8_span"]
            self.assertTrue(raw[span["start"] : span["end"]].strip())
            self.assertTrue(item["mapping_revision"].startswith("sha256:"))
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            result = check_adapter_conformance(
                DriveCaptureAdapter(),
                archive,
                {
                    "source_scope": self.fixture["binding"]["scope"],
                    "drive_normalization": normalization(),
                },
            )
        self.assertEqual(result["status"], "success")

    def test_unknown_duplicate_unreviewed_and_incompatible_mapping_selection_fail_closed(
        self,
    ):
        archive = self.capture()
        for change in (
            lambda value: value["mappings"][0].update(
                file_id="private-unavailable-canary"
            ),
            lambda value: value["mappings"].append(deepcopy(value["mappings"][0])),
            lambda value: value["review"].update(state="in-review"),
            lambda value: value["review_authority"].update(kind="agent"),
            lambda value: value["mappings"][0]["mapping"]["review"].update(
                state="in-review"
            ),
            lambda value: value.update(executable="private-canary"),
        ):
            configuration = normalization()
            change(configuration)
            with self.subTest(), self.assertRaises(ContractError) as error:
                self.normalized(archive, configuration)
            self.assertNotIn("private-", str(error.exception))
        with self.assertRaises(ContractError):
            DriveCaptureAdapter().normalize(
                archive, {"source_scope": self.fixture["binding"]["scope"]}
            )

    def test_occurrence_budget_bounds_metadata_even_when_overlaps_deduplicate(self):
        archive = self.capture()
        adapter = DriveCaptureAdapter()
        with patch.object(adapter, "limits", {**adapter.limits, "units": 8}):
            with self.assertRaisesRegex(ContractError, "CAPTURE_BUDGET"):
                adapter.normalize(
                    archive,
                    {
                        "source_scope": self.fixture["binding"]["scope"],
                        "drive_normalization": normalization(),
                    },
                )

    def test_changed_configuration_rejects_old_apply_before_any_additional_vault_write(
        self,
    ):
        arguments = ingest_arguments(self.fixture, self.capture())
        preview = cli(arguments)
        before = garden_fingerprint(self.fixture["garden"])
        objects = self.fixture["vault"].audit()["objects"]
        configuration = normalization()
        configuration["mappings"][0]["mapping"]["date_semantics"] = (
            "transaction-calendar-date"
        )
        write_json(self.fixture["normalization_path"], configuration)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                main(arguments + ["--apply", "--plan-digest", preview["plan_sha256"]]),
                3,
            )
        self.assertEqual(garden_fingerprint(self.fixture["garden"]), before)
        self.assertEqual(self.fixture["vault"].audit()["objects"], objects)

    def test_replay_configuration_provenance_and_unsupported_adapter_options(self):
        arguments, preview = self.apply(self.capture())
        again = cli(arguments)
        self.assertFalse(
            cli(arguments + ["--apply", "--plan-digest", again["plan_sha256"]])[
                "applied"
            ]
        )
        self.assertEqual(len(preview["inputs"]["normalized_sources"]), 8)
        records = b"".join(
            path.read_bytes()
            for path in (self.fixture["garden"] / ".garden").rglob("*.json")
        )
        self.assertIn(b"reviewed-drive-normalization", records)
        self.assertIn(b"provider_occurrences", records)
        self.assertNotIn(str(self.fixture["normalization_path"]).encode(), records)
        arguments[arguments.index("--adapter") + 1] = "ledger-csv"
        with redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(arguments), 3)
        self.assertIn("CAPTURE_MAPPING", error.getvalue())

    def test_partial_capture_resumes_and_missing_configured_file_is_not_silently_ignored(
        self,
    ):
        self.provider.fail = "file-b"
        with self.assertRaisesRegex(ContractError, "CAPTURE_UNAVAILABLE"):
            self.capture()
        self.provider.fail = None
        archive = self.capture()
        self.assertEqual(self.provider.reads.count("file-a"), 1)
        self.assertEqual(len(self.normalized(archive).units), 8)
        self.provider.items.pop("file-b")
        self.fixture["binding"]["captured_at"] = "2026-11-13T00:00:00Z"
        with self.assertRaisesRegex(ContractError, "CAPTURE_MAPPING_SELECTION"):
            self.normalized(self.capture())
        self.assertEqual(len(self.normalized(archive).units), 8)

    def test_provider_correction_stales_packet_and_fresh_exact_review_changes_only_one_row(
        self,
    ):
        _, before = self.apply(self.capture())
        context, request = packet_inputs(self.fixture, before)
        _, old_files = plan_packet(context, request)
        original_objects = self.fixture["vault"].audit()["objects"]
        self.provider.replace(
            "file-a", self.provider.data["file-a"].replace(b"2500.00", b"2400.00")
        )
        self.provider.items["file-a"]["version"] = "2"
        self.fixture["binding"]["captured_at"] = "2026-11-13T00:00:00Z"
        _, after = self.apply(self.capture())
        refreshed, current_request = packet_inputs(self.fixture, after)
        current_request["review"]["rationale"] = (
            "Author reviewed the corrected selected provider revision and packet."
        )
        _, new_files = plan_packet(refreshed, current_request)
        old_ids = {item["source"]["id"] for item in request["sources"]}
        new_ids = {item["source"]["id"] for item in current_request["sources"]}
        self.assertEqual(len(old_ids & new_ids), 7)
        self.assertEqual(
            json.loads(new_files["packet.json"])["totals"][0]["net_movement"], "2159.76"
        )
        result = reconcile_packet(
            json.loads(new_files["packet-dependencies.json"]),
            json.loads(old_files["packet-dependencies.json"]),
        )
        self.assertEqual(result["state"], "stale")
        self.assertIn("selected-evidence-changed", result["reasons"])
        self.assertTrue(
            all(
                item in self.fixture["vault"].audit()["objects"]
                for item in original_objects
            )
        )
        self.assertEqual(
            json.loads(old_files["packet.json"])["totals"][0]["net_movement"], "2259.76"
        )

    def test_clean_vault_restore_and_removed_mapping_filename_preserve_packet_and_dependencies(
        self,
    ):
        _, preview = self.apply(self.capture())
        context, request = packet_inputs(self.fixture, preview)
        _, files = plan_packet(context, request)
        self.assertEqual(
            json.loads(files["packet.json"])["totals"][0]["net_movement"], "2259.76"
        )
        vault = self.fixture["vault"]
        backup = vault.export_bundle()
        restored = FilesystemVault(self.root / "restored-vault", "synthetic-vault")
        restored.restore_bundle(backup, digest_bytes(backup))
        vault.root.rename(self.root / "retained-original-vault")
        self.fixture["normalization_path"].rename(
            self.root / "retained-normalization.json"
        )
        configuration = read_object(self.fixture["configuration"])
        configuration["vaults"][0]["root"] = str(restored.root)
        write_json(self.fixture["configuration"], configuration)
        session = read_object(context.session_path)
        write_json(
            context.session_path,
            bind_session_revisions(self.fixture["configuration"], session),
        )
        current = QueryContext.load(self.fixture["configuration"], context.session_path)
        self.assertEqual(plan_packet(current, request)[1], files)
        self.assertNotIn(str(self.root).encode(), b"".join(files.values()))
