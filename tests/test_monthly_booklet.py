"""Reviewed monthly figures, exact print provenance, and live download authority."""

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.booklet import (
    BOOKLET_MONTH,
    RENDERER,
    booklet_artifact,
    booklet_preview,
    read_booklet_request,
)
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.source_evidence import resolve_source_evidence_batch
from mindgarden.application.storage import open_vault
from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object
from mindgarden.domain.ledger import transaction_key
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.visit_demo import prepare_demo
from tests.consultation_fixture import cli, create_fixture
from tests.packet_freshness_fixture import correct_fixture
from tests.support_v1 import write_json


USD = {
    "month": "2026-01",
    "currency": "USD",
    "income": "2500.00",
    "expense": "-230.25",
    "refund": "10.00",
    "transfer": "0.00",
    "uncategorized": "-19.99",
    "net_movement": "2259.76",
}


class BookletTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def test_printable_willow_edition_binds_exact_citations_and_approved_totals(self):
        config, original = prepare_demo(self.root / "visit")
        session = read_object(original)
        session["projections"].append("source-evidence")
        request = read_booklet_request()
        session["source_grants"] = [item["source"] for item in request["sources"]]
        path = self.root / "explicit-booklet-scope.json"
        write_json(path, bind_session_revisions(config, session))
        context = QueryContext.load(config, path)
        before = {
            path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()
        }

        with (
            patch("socket.socket", side_effect=AssertionError("Network attempted")),
            patch("subprocess.Popen", side_effect=AssertionError("Process attempted")),
        ):
            preview = booklet_preview(context, BOOKLET_MONTH)
            pdf_type, pdf = booklet_artifact(
                context, BOOKLET_MONTH, preview["plan_sha256"], "pdf"
            )
            evidence_type, evidence = booklet_artifact(
                context, BOOKLET_MONTH, preview["plan_sha256"], "evidence"
            )

        self.assertEqual(preview["totals"], [USD])
        self.assertEqual(preview["timezone"], "UTC")
        self.assertEqual(preview["scope"]["publication"], "never-exportable")
        self.assertEqual(len(preview["transactions"]), 8)
        transfers = [
            item
            for item in preview["transactions"]
            if item["classification"] == "transfer"
        ]
        self.assertEqual(
            sorted(item["amount"] for item in transfers), ["-300.00", "300.00"]
        )
        self.assertEqual(transfers[0]["paired_with"], transfers[1]["id"])
        self.assertEqual(
            preview["coverage"][1]["missing_declared_intervals"],
            [{"start": "2026-01-01", "end": "2026-01-09"}],
        )
        self.assertEqual(preview["coverage"][2]["status"], "no-supplied-transactions")
        self.assertEqual(len(preview["unresolved_transactions"]), 1)
        self.assertEqual(preview["evidence"], request["sources"])
        verified = resolve_source_evidence_batch(context, preview["evidence"])
        for item, result in zip(preview["evidence"], verified, strict=True):
            self.assertEqual(
                item["content_sha256"], digest_bytes(result["text"].encode())
            )
            self.assertEqual(item["source"], result["source"])
            self.assertEqual(item["locator"], result["locator"])
            self.assertIn(item["content_sha256"].encode(), pdf)

        self.assertEqual(pdf_type, "application/pdf")
        self.assertTrue(pdf.startswith(b"%PDF-1.4"))
        self.assertIn(b"Net movement 2259.76", pdf)
        self.assertIn(b"Expense outflow -230.25", pdf)
        xref = int(pdf.rsplit(b"startxref\n", 1)[1].splitlines()[0])
        entries = pdf[xref:].splitlines()
        self.assertEqual(entries[0], b"xref")
        self.assertIn(b"/MediaBox [0 0 612 792]", pdf)
        object_count = int(entries[1].split()[1])
        for number, entry in enumerate(entries[3 : 2 + object_count], 1):
            offset = int(entry.split()[0])
            self.assertTrue(pdf[offset:].startswith(f"{number} 0 obj\n".encode()))
        self.assertEqual(digest_bytes(pdf), preview["pdf_sha256"])
        self.assertEqual(evidence_type, "application/json; charset=utf-8")
        manifest = json.loads(evidence)
        self.assertEqual(
            manifest, {**preview, "schema": "mindgarden.monthly-booklet-evidence/v1"}
        )
        self.assertEqual(manifest["renderer"], RENDERER)
        self.assertEqual(
            manifest["plan_sha256"],
            digest_bytes(
                canonical_json({k: v for k, v in preview.items() if k != "plan_sha256"})
            ),
        )
        self.assertNotIn(str(self.root).encode(), evidence + pdf)
        self.assertEqual(
            before,
            {
                path: path.read_bytes()
                for path in self.root.rglob("*")
                if path.is_file()
            },
        )

    def test_no_extra_source_authority_and_invalid_month_or_review_fail_closed(self):
        config, path = prepare_demo(self.root / "visit")
        context = QueryContext.load(config, path)
        with (
            patch.object(
                context,
                "snapshots",
                side_effect=AssertionError("Source read attempted"),
            ),
            self.assertRaisesRegex(ContractError, "PROJECTION_DENIED"),
        ):
            booklet_preview(context, BOOKLET_MONTH)
        session = read_object(path)
        session["projections"].append("source-evidence")
        session["source_grants"] = [read_booklet_request()["sources"][0]["source"]]
        second = self.root / "sources-ungranted.json"
        write_json(second, bind_session_revisions(config, session))
        context = QueryContext.load(config, second)
        with patch.object(
            context, "snapshots", side_effect=AssertionError("Source read attempted")
        ):
            with self.assertRaisesRegex(ContractError, "BOOKLET_UNAVAILABLE"):
                booklet_preview(context, "2026-02")
            with self.assertRaisesRegex(ContractError, "BOOKLET_REVIEW"):
                booklet_artifact(context, BOOKLET_MONTH, "invalid", "pdf")
            with self.assertRaisesRegex(ContractError, "SOURCE_GRANT"):
                booklet_preview(context, BOOKLET_MONTH)

    def test_corrected_ledger_requires_new_approval_and_preserves_the_old_edition(self):
        fixture = create_fixture(self.root / "ledger")
        request = fixture["request"]
        euro = fixture["root"] / "fictional-euro.csv"
        euro.write_text(
            "transaction_id,account_id,date,amount,currency,description\n"
            "euro-income,account-b,2026-01-15,100.00,EUR,Synthetic received amount\n"
            "euro-expense,account-b,2026-01-16,-20.50,EUR,Synthetic outflow\n"
        )
        arguments = list(fixture["imports"][0]["arguments"])
        for flag, value in (
            ("--input", str(euro)),
            ("--source-id", "euro-example"),
            ("--origin", "urn:synthetic:eur"),
        ):
            arguments[arguments.index(flag) + 1] = value
        plan = cli(arguments)
        cli(arguments + ["--apply", "--plan-digest", plan["plan_sha256"]])
        request["sources"].extend(
            item["evidence"][0] for item in plan["inputs"]["normalized_sources"]
        )
        request["currencies"].append({"code": "EUR", "scale": 2})
        for category in ("income", "expense"):
            identity = transaction_key("account-b", "euro-" + category)
            request["selection"].append(identity)
            request["decisions"].append(
                {
                    "transaction": identity,
                    "category": category,
                    "paired_with": None,
                    "rationale": "Explicit fictional EUR ledger review.",
                }
            )
        scope = read_object(fixture["session_path"])
        scope["source_grants"] = [item["source"] for item in request["sources"]]
        write_json(
            fixture["session_path"],
            bind_session_revisions(fixture["configuration"], scope),
        )
        context = QueryContext.load(fixture["configuration"], fixture["session_path"])
        vault = open_vault(context.bindings, "synthetic-vault")
        objects = vault.audit()["objects"]
        with patch(
            "mindgarden.application.booklet.read_booklet_request", return_value=request
        ):
            first = booklet_preview(context, BOOKLET_MONTH)
            first_pdf = booklet_artifact(
                context, BOOKLET_MONTH, first["plan_sha256"], "pdf"
            )[1]
        self.assertEqual([item["currency"] for item in first["totals"]], ["EUR", "USD"])
        self.assertEqual(first["totals"][0]["net_movement"], "79.50")
        self.assertEqual(first["totals"][1], USD)
        self.assertIn(b"Net movement 79.50", first_pdf)
        download = self.root / "approved-prior.pdf"
        download.write_bytes(first_pdf)

        corrected = correct_fixture(fixture)
        with patch(
            "mindgarden.application.booklet.read_booklet_request",
            return_value=corrected["request"],
        ):
            second = booklet_preview(corrected["context"], BOOKLET_MONTH)
            self.assertEqual(second["totals"][0], first["totals"][0])
            self.assertEqual(second["totals"][1]["net_movement"], "2159.76")
            self.assertNotEqual(first["inputs_sha256"], second["inputs_sha256"])
            self.assertNotEqual(first["plan_sha256"], second["plan_sha256"])
            with self.assertRaisesRegex(ContractError, "BOOKLET_REVIEW"):
                booklet_artifact(
                    corrected["context"], BOOKLET_MONTH, first["plan_sha256"], "pdf"
                )
            second_pdf = booklet_artifact(
                corrected["context"], BOOKLET_MONTH, second["plan_sha256"], "pdf"
            )[1]
        self.assertIn(b"Net movement 2159.76", second_pdf)
        self.assertNotEqual(first_pdf, second_pdf)
        self.assertEqual(download.read_bytes(), first_pdf)
        self.assertTrue(all(item in vault.audit()["objects"] for item in objects))
