"""Explicit layout semantics, immutable CSV evidence and existing packet parity."""

from contextlib import redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.ledger_csv import LedgerCSVAdapter
from mindgarden.adapters.filesystem import FilesystemVault
from mindgarden.adapters.mapped_ledger_csv import MappedLedgerCSVAdapter
from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.consultation import plan_packet
from mindgarden.application.ingestion import default_registry
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.storage import open_vault
from mindgarden.domain.contracts import digest_bytes, read_object
from mindgarden.domain.sources import check_adapter_conformance
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_source_adapters as source_fixture
from tests.consultation_fixture import FIXTURES, cli, create_fixture
from tests.support_v1 import TIME, write_json

MAPPINGS = FIXTURES / "mappings"


def arguments(root, garden, configuration, csv_name, mapping_name):
    source = root / csv_name
    mapping = root / mapping_name
    source.write_bytes((MAPPINGS / csv_name).read_bytes())
    mapping.write_bytes((MAPPINGS / mapping_name).read_bytes())
    return [
        "ingest",
        "--repository-root",
        str(garden),
        "--local-config",
        str(configuration),
        "--vault-id",
        "synthetic-vault",
        "--input",
        str(source),
        "--source-id",
        csv_name.removesuffix(".csv"),
        "--title",
        "Reviewed synthetic mapped CSV",
        "--origin",
        "urn:synthetic:" + csv_name,
        "--captured",
        TIME,
        "--owner",
        "synthetic-owner",
        "--rights",
        "Wholly synthetic fixture.",
        "--media-type",
        "text/csv",
        "--adapter",
        "mapped-ledger-csv",
        "--manifest-version",
        "mapping-v1",
        "--ledger-mapping",
        str(mapping),
    ]


class MappedLedgerAdapterTests(unittest.TestCase):
    def test_two_reviewed_layouts_produce_existing_canonical_rows_and_conform(self):
        for name, mapping_name, original in (
            ("layout-a.csv", "layout-a.json", "account-a.csv"),
            ("layout-a-overlap.csv", "layout-a.json", "account-a-overlap.csv"),
            ("layout-b.csv", "layout-b.json", "account-b.csv"),
        ):
            raw = (MAPPINGS / name).read_bytes()
            metadata = {"ledger_mapping": read_object(MAPPINGS / mapping_name)}
            result = MappedLedgerCSVAdapter().normalize(raw, metadata)
            strict = LedgerCSVAdapter().normalize(
                (FIXTURES / original).read_bytes(), {}
            )
            self.assertEqual(
                [item.content for item in result.units],
                [item.content for item in strict.units],
            )
            self.assertEqual(
                check_adapter_conformance(MappedLedgerCSVAdapter(), raw, metadata)[
                    "status"
                ],
                "success",
            )
            self.assertEqual(result.metadata["mapping"], metadata["ledger_mapping"])
            self.assertTrue(
                all(
                    item.metadata["mapping_revision"]
                    == result.metadata["mapping_revision"]
                    for item in result.units
                )
            )

    def test_original_bom_crlf_multiline_and_unicode_spans_are_exact(self):
        raw = b'\xef\xbb\xbfReference,Account,Posted,Value,Unit,Details\r\nfirst,account-a,2026-01-01,-0.10,USD,"caf\xc3\xa9\r\nsecond line"\r\n'
        metadata = {"ledger_mapping": read_object(MAPPINGS / "layout-a.json")}
        unit = MappedLedgerCSVAdapter().normalize(raw, metadata).units[0]
        span = unit.metadata["original_utf8_span"]
        self.assertEqual(raw[span["start"] : span["end"]], raw.split(b"\r\n", 1)[1])
        self.assertEqual(json.loads(unit.content)["description"], "café\r\nsecond line")

    def test_review_unknown_fields_header_dates_and_ambiguous_amounts_fail_safely(self):
        original = read_object(MAPPINGS / "layout-b.json")
        raw = (MAPPINGS / "layout-b.csv").read_bytes()
        for change in (
            lambda m: m["review"].update(
                state="unreviewed", reviewers=[], reviewed_at=None
            ),
            lambda m: m["review_authority"].update(kind="agent"),
            lambda m: m.update(code="PRIVATE-CANARY"),
            lambda m: m["fields"].update(date="unavailable-column"),
        ):
            mapping = deepcopy(original)
            change(mapping)
            with self.assertRaises(ContractError) as error:
                MappedLedgerCSVAdapter().normalize(raw, {"ledger_mapping": mapping})
            self.assertNotIn("PRIVATE-CANARY", str(error.exception))
        for supplied in (
            raw.replace(b"Ref,When", b"When,Ref"),
            raw.replace(b"01/05/2026", b"1/5/2026"),
            raw.replace(b"01/05/2026", b"02/31/2026"),
            raw.replace(b",,300.00", b",100.00,300.00"),
            raw.replace(b",50.00,", b",-50.00,"),
            raw + raw.splitlines(keepends=True)[1],
        ):
            with self.subTest(supplied=supplied[:12]), self.assertRaises(ContractError):
                MappedLedgerCSVAdapter().normalize(
                    supplied, {"ledger_mapping": original}
                )

    def test_mapping_revision_is_separate_from_row_identity_and_immutable_content(self):
        mapping = read_object(MAPPINGS / "layout-a.json")
        raw = (MAPPINGS / "layout-a.csv").read_bytes()
        before = MappedLedgerCSVAdapter().normalize(raw, {"ledger_mapping": mapping})
        changed = deepcopy(mapping)
        changed["date_semantics"] = "transaction-calendar-date"
        after = MappedLedgerCSVAdapter().normalize(raw, {"ledger_mapping": changed})
        self.assertEqual(before.units[0].content, after.units[0].content)
        self.assertNotEqual(before.units[0].identity, after.units[0].identity)
        self.assertNotEqual(
            before.metadata["mapping_revision"], after.metadata["mapping_revision"]
        )
        self.assertEqual(
            default_registry().select("text/csv", "1.0.0").adapter_id, "ledger-csv"
        )


class MappedLedgerIngestionTests(unittest.TestCase):
    def setUp(self):
        source_fixture.SourceAdapterTests.setUp(self)
        self.arguments = arguments(
            self.root,
            self.workspace,
            self.configuration,
            "layout-a.csv",
            "layout-a.json",
        )

    def test_cli_mapping_change_invalidates_review_before_any_vault_write(self):
        preview = cli(self.arguments)
        self.assertEqual(
            preview["inputs"]["metadata"]["ledger_mapping_input_sha256"],
            digest_bytes((self.root / "layout-a.json").read_bytes()),
        )
        fingerprint = garden_fingerprint(self.workspace)
        mapping = read_object(self.root / "layout-a.json")
        mapping["date_semantics"] = "transaction-calendar-date"
        write_json(self.root / "layout-a.json", mapping)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                main(
                    self.arguments
                    + ["--apply", "--plan-digest", preview["plan_sha256"]]
                ),
                3,
            )
        self.assertEqual(garden_fingerprint(self.workspace), fingerprint)
        self.assertEqual(self.vault.audit()["objects"], [])

    def test_repeated_import_retains_original_bytes_and_mapping_provenance(self):
        preview = cli(self.arguments)
        original = (self.root / "layout-a.csv").read_bytes()
        first = cli(
            self.arguments + ["--apply", "--plan-digest", preview["plan_sha256"]]
        )
        self.assertTrue(first["applied"])
        again = cli(self.arguments)
        self.assertFalse(
            cli(self.arguments + ["--apply", "--plan-digest", again["plan_sha256"]])[
                "applied"
            ]
        )
        self.assertEqual(self.vault.get("sha256:" + digest_bytes(original)), original)
        records = [
            read_object(path)
            for path in (self.workspace / ".garden/provenance").glob("*.json")
        ]
        parameters = [
            step["parameters"]
            for record in records
            for step in record.get("transformations", [])
            if step["name"] == "reviewed-ledger-csv-mapping"
        ]
        self.assertTrue(parameters)
        self.assertEqual(parameters[0]["mapping"]["id"], "synthetic-layout-a")


class MappedLedgerPacketTests(unittest.TestCase):
    def test_both_layouts_and_overlap_feed_the_existing_reviewed_packet(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = create_fixture(root)
            _, original_files = plan_packet(fixture["context"], fixture["request"])
            original_packet = json.loads(original_files["packet.json"])
            citations = {}
            for csv_name, mapping_name in (
                ("layout-a.csv", "layout-a.json"),
                ("layout-a-overlap.csv", "layout-a.json"),
                ("layout-b.csv", "layout-b.json"),
            ):
                args = arguments(
                    root,
                    fixture["garden"],
                    fixture["configuration"],
                    csv_name,
                    mapping_name,
                )
                preview = cli(args)
                cli(args + ["--apply", "--plan-digest", preview["plan_sha256"]])
                for unit in preview["inputs"]["normalized_sources"]:
                    citation = unit["evidence"][0]
                    citations[citation["source"]["id"]] = citation
            self.assertEqual(len(citations), 8)
            request = deepcopy(fixture["request"])
            request["sources"] = sorted(
                citations.values(), key=lambda item: item["source"]["id"]
            )
            session = read_object(fixture["session_path"])
            session["source_grants"] = [item["source"] for item in request["sources"]]
            write_json(
                fixture["session_path"],
                bind_session_revisions(fixture["configuration"], session),
            )
            context = QueryContext.load(
                fixture["configuration"], fixture["session_path"]
            )
            _, files = plan_packet(context, request)
            packet = json.loads(files["packet.json"])
            self.assertEqual(packet["totals"], original_packet["totals"])
            self.assertEqual(packet["totals"][0]["net_movement"], "2259.76")
            self.assertEqual(len(packet["evidence"]), 8)
            self.assertTrue(
                all(
                    value["original"]["mapping_revision"].startswith("sha256:")
                    for value in packet["transactions"]
                )
            )
            self.assertTrue(
                all(
                    value["original"]["original_utf8_span"]["start"]
                    < value["original"]["original_utf8_span"]["end"]
                    for value in packet["transactions"]
                )
            )
            vault = open_vault(context.bindings, "synthetic-vault")
            bundle = vault.export_bundle()
            restored = FilesystemVault(
                root / "restored-mapped-vault", "synthetic-vault"
            )
            restored.restore_bundle(bundle, digest_bytes(bundle))
            vault.root.rename(root / "retained-unbound-vault")
            for name in ("layout-a.json", "layout-b.json"):
                (root / name).rename(root / ("retained-" + name))
            configuration = read_object(fixture["configuration"])
            configuration["vaults"][0]["root"] = str(restored.root)
            write_json(fixture["configuration"], configuration)
            write_json(
                fixture["session_path"],
                bind_session_revisions(fixture["configuration"], session),
            )
            restored_context = QueryContext.load(
                fixture["configuration"], fixture["session_path"]
            )
            self.assertEqual(plan_packet(restored_context, request)[1], files)
