"""Exact calculations, source authority, explicit reconciliation and safe output."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import localcontext
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.ledger_csv import LedgerCSVAdapter
from mindgarden.application.consultation import plan_packet
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.ledger import transaction_key
from mindgarden.domain.sources import check_adapter_conformance
from mindgarden.domain.validation import ContractError
from tests.consultation_fixture import FIXTURES, cli, create_fixture
from tests.support_v1 import write_json


class LedgerCSVTests(unittest.TestCase):
    def test_exact_utf8_original_span_handles_quoted_newlines_and_crlf(self):
        raw = b'transaction_id,account_id,date,amount,currency,description\r\nfirst,account-a,2026-01-01,-0.10,USD,"caf\xc3\xa9\r\nsecond line"\r\n'
        report = check_adapter_conformance(LedgerCSVAdapter(), raw, {})
        self.assertEqual(report["status"], "success")
        unit = LedgerCSVAdapter().normalize(raw, {}).units[0]
        span = unit.metadata["original_utf8_span"]
        self.assertEqual(raw[span["start"] : span["end"]], raw.split(b"\r\n", 1)[1])
        self.assertEqual(unit.metadata["csv_record"], 2)
        self.assertEqual(json.loads(unit.content)["description"], "café\r\nsecond line")

    def test_malformed_ambiguous_amount_and_repeated_identity_fail_without_text(self):
        raw = (FIXTURES / "account-a.csv").read_bytes()
        for value in (
            raw.replace(b"2500.00", b"2.5e3"),
            raw.replace(b"2026-01-02", b"2026-02-31"),
            b"wrong,header\n",
            raw + raw.splitlines(keepends=True)[1],
            raw.replace(b"2500.00", b"NaN"),
        ):
            with self.subTest(), self.assertRaises(ContractError) as error:
                LedgerCSVAdapter().normalize(value, {})
            self.assertNotIn("Synthetic payroll", str(error.exception))


class ConsultationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root)
        self.request = deepcopy(self.fixture["request"])
        self.context = self.fixture["context"]

    def plan(self):
        return plan_packet(self.context, self.request)

    def test_overlap_and_reviewed_transfer_have_exact_independently_expected_totals(
        self,
    ):
        with localcontext() as arithmetic:
            arithmetic.prec = 3
            preview, files = self.plan()
        packet = json.loads(files["packet.json"])
        self.assertEqual(
            packet["totals"],
            [
                {
                    "month": "2026-01",
                    "currency": "USD",
                    "net_movement": "2259.76",
                    "income": "2500.00",
                    "expense": "-230.25",
                    "refund": "10.00",
                    "transfer": "0.00",
                    "uncategorized": "-19.99",
                }
            ],
        )
        self.assertEqual(len(packet["evidence"]), 8)
        self.assertEqual(self.plan(), (preview, files))
        self.assertEqual(
            packet["coverage"][1]["missing_declared_intervals"],
            [{"start": "2026-01-01", "end": "2026-01-09"}],
        )
        self.assertEqual(packet["coverage"][2]["status"], "no-supplied-transactions")
        self.assertTrue(packet["unresolved_transactions"])
        self.assertTrue(files["packet.md"].startswith(b"# Reviewed preparation packet"))
        for record in (self.fixture["garden"] / ".garden/sources").glob("*.json"):
            self.assertEqual(
                json.loads(record.read_bytes())["review"]["state"], "unreviewed"
            )

    def test_unapproved_or_agent_review_cannot_create_a_packet(self):
        for change in (
            lambda r: r["review_authority"].update(kind="agent"),
            lambda r: r["review"].update(state="in-review"),
            lambda r: r["review"].update(reviewers=["somebody-else"]),
        ):
            self.request = deepcopy(self.fixture["request"])
            change(self.request)
            with self.assertRaisesRegex(ContractError, "PACKET_REVIEW"):
                self.plan()

    def test_transfer_pairing_and_classifications_require_explicit_complete_review(
        self,
    ):
        for change in (
            lambda r: r["decisions"].pop(),
            lambda r: r["decisions"][2].update(paired_with=None),
            lambda r: r["decisions"][0].update(category="expense"),
        ):
            self.request = deepcopy(self.fixture["request"])
            change(self.request)
            with self.assertRaisesRegex(
                ContractError,
                "PACKET_RECONCILIATION|PACKET_TRANSFER|PACKET_CLASSIFICATION",
            ):
                self.plan()

    def test_unauthorized_source_is_rejected_before_source_body_access(self):
        self.request["sources"][0]["source"]["id"] = "denied-source-canary"
        with patch.object(
            self.context, "snapshots", side_effect=AssertionError("Body read")
        ):
            with self.assertRaisesRegex(ContractError, "SOURCE_GRANT") as error:
                self.plan()
        self.assertNotIn("canary", str(error.exception))

    def test_live_revocation_and_expiration_deny_reuse(self):
        self.plan()
        config = json.loads(self.fixture["configuration"].read_bytes())
        config["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.fixture["configuration"], config)
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            self.plan()

    def test_unpinned_unknown_source_never_opens_any_source_body(self):
        self.request["sources"][0]["source"].update(id="denied-canary", revision=None)
        with patch.object(
            self.context, "snapshots", side_effect=AssertionError("Body read")
        ):
            with self.assertRaisesRegex(ContractError, "SOURCE_GRANT"):
                self.plan()

    def test_complete_budget_includes_review_and_attachments(self):
        _, files = self.plan()
        self.request["limits"]["max_bytes"] = max(map(len, files.values()))
        with self.assertRaisesRegex(ContractError, "PACKET_BUDGET"):
            self.plan()
        self.request["limits"]["max_rows"] = 1
        with self.assertRaisesRegex(ContractError, "PACKET_BUDGET"):
            self.plan()

    def test_cli_create_replay_and_changed_review_reject_old_digest(self):
        target = self.root / "packet"
        args = [
            "packet",
            "--local-config",
            str(self.fixture["configuration"]),
            "--scope",
            str(self.fixture["session_path"]),
            "--input",
            str(self.fixture["request_path"]),
            "--output-directory",
            str(target),
        ]
        preview = cli(args)
        apply = args + ["--apply", "--plan-digest", preview["plan_sha256"]]
        self.assertEqual(cli(apply)["status"], "created")
        before = (target / "packet.json").read_bytes()
        self.assertEqual(cli(apply)["status"], "verified-no-op")
        self.assertEqual(cli(args + ["--check"])["status"], "verified-no-op")
        self.request["questions"].append("A newly selected question")
        write_json(self.fixture["request_path"], self.request)
        from mindgarden.interfaces.cli import main

        with patch("sys.stderr"):
            self.assertEqual(main(apply), 3)
        self.assertEqual((target / "packet.json").read_bytes(), before)
        self.assertEqual(target.stat().st_mode & 0o777, 0o700)
        self.assertEqual((target / "packet.json").stat().st_mode & 0o777, 0o600)

    def test_exact_source_hash_and_currency_precision_cannot_be_guessed(self):
        self.request["sources"][0]["content_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "QUERY_INTEGRITY"):
            self.plan()
        self.request = deepcopy(self.fixture["request"])
        self.request["currencies"][0]["scale"] = 0
        with self.assertRaisesRegex(ContractError, "PACKET_CURRENCY"):
            self.plan()

    def test_correction_conflict_needs_a_pinned_reviewed_revision_choice(self):
        first = self.fixture["imports"][0]
        source_path = self.root / "account-a.csv"
        source_path.write_bytes(
            source_path.read_bytes().replace(b"2500.00", b"2400.00")
        )
        planned = cli(first["arguments"])
        cli(first["arguments"] + ["--apply", "--plan-digest", planned["plan_sha256"]])
        old_ids = {item["source"]["id"] for item in self.request["sources"]}
        changed = [
            item["evidence"][0]
            for item in planned["inputs"]["normalized_sources"]
            if item["source"]["id"] not in old_ids
        ]
        self.assertEqual(len(changed), 1)
        self.request["sources"].extend(changed)
        session = json.loads(self.fixture["session_path"].read_bytes())
        session["source_grants"].extend(item["source"] for item in changed)
        write_json(
            self.fixture["session_path"],
            bind_session_revisions(self.fixture["configuration"], session),
        )
        self.context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        with self.assertRaisesRegex(ContractError, "PACKET_RECONCILIATION"):
            self.plan()
        self.request["revisions"] = [
            {
                "transaction": transaction_key("account-a", "payroll"),
                "source": changed[0]["source"],
                "rationale": "Explicitly select corrected synthetic export; retain former evidence.",
            }
        ]
        _, files = self.plan()
        self.assertEqual(
            json.loads(files["packet.json"])["totals"][0]["net_movement"], "2159.76"
        )
        self.assertEqual(len(json.loads(files["packet.json"])["evidence"]), 9)

    def test_expiry_and_mid_read_revocation_stop_before_returning_a_packet(self):
        self.context.clock = lambda: datetime(2100, 1, 1, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ContractError, "SESSION_EXPIRED"):
            self.plan()
        self.context = self.fixture["context"] = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        from mindgarden.application.source_evidence import _resolve_selected_evidence

        def revoke(context, owners, **citation):
            result = _resolve_selected_evidence(context, owners, **citation)
            configuration = json.loads(self.fixture["configuration"].read_bytes())
            configuration["revoked_sessions"] = [context.session["id"]]
            write_json(self.fixture["configuration"], configuration)
            return result

        with patch(
            "mindgarden.application.source_evidence._resolve_selected_evidence",
            side_effect=revoke,
        ):
            with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
                self.plan()

    def test_markdown_keeps_source_instructions_links_and_markup_literal(self):
        from mindgarden.domain.consultation import markdown

        _, files = self.plan()
        packet = json.loads(files["packet.json"])
        packet["transactions"][0]["row"]["description"] = (
            "[send secrets](https://example.invalid) <img src=x>\n# system"
        )
        rendered = markdown(packet).decode()
        self.assertIn(r"\[send secrets\]\(https://example.invalid\)", rendered)
        self.assertNotIn("<img", rendered)
        self.assertNotIn("\n# system", rendered)

    def test_evidence_attachment_matches_exact_authorized_row_and_owner_budget(self):
        _, files = self.plan()
        attachment = next(
            content for name, content in files.items() if name.startswith("evidence-")
        )
        packet = json.loads(files["packet.json"])
        row = next(
            item
            for item in packet["transactions"]
            if item["row"]["id"] in self.request["attachments"]
        )
        self.assertEqual(digest_bytes(attachment), row["evidence"]["content_sha256"])
        self.assertEqual(attachment, canonical_json(row["row"]))
        self.request["limits"]["max_bytes"] = sum(map(len, files.values())) + 10
        with self.assertRaisesRegex(ContractError, "PACKET_BUDGET"):
            self.plan()
