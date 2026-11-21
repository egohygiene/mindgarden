"""Independent monthly/category/currency expectations through ordinary services."""

from copy import deepcopy
from decimal import Decimal, localcontext
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.consultation import plan_packet
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.source_evidence import resolve_source_evidence_batch
from mindgarden.domain.ledger import transaction_key
from tests.consultation_fixture import FIXTURES, cli, create_fixture
from tests.support_v1 import write_json


class ConsultationPeriodTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fixture = create_fixture(Path(temporary.name))
        self.request = deepcopy(self.fixture["request"])
        source = self.fixture["root"] / "two-periods.csv"
        source.write_bytes((FIXTURES / "two-periods.csv").read_bytes())
        args = list(self.fixture["imports"][0]["arguments"])
        for flag, value in (
            ("--input", str(source)),
            ("--source-id", "two-periods"),
            ("--origin", "urn:synthetic:two-periods"),
        ):
            args[args.index(flag) + 1] = value
        planned = cli(args)
        cli(args + ["--apply", "--plan-digest", planned["plan_sha256"]])
        self.request["sources"].extend(
            unit["evidence"][0] for unit in planned["inputs"]["normalized_sources"]
        )
        rows = (
            ("account-a", "payroll-feb", "income"),
            ("account-a", "groceries-feb", "expense"),
            ("account-a", "refund-feb", "refund"),
            ("account-a", "transfer-out-feb", "transfer"),
            ("account-b", "transfer-in-feb", "transfer"),
            ("account-b", "subscriptions-feb", "expense"),
            ("account-b", "euro-sale", "income"),
            ("account-b", "euro-supply", "expense"),
        )
        pairs = {
            "transfer-out-feb": transaction_key("account-b", "transfer-in-feb"),
            "transfer-in-feb": transaction_key("account-a", "transfer-out-feb"),
        }
        for account, identity, category in rows:
            key = transaction_key(account, identity)
            self.request["decisions"].append(
                {
                    "transaction": key,
                    "category": category,
                    "paired_with": pairs.get(identity),
                    "rationale": "Authored synthetic classification; no inferred conversion.",
                }
            )
            self.request["selection"].append(key)
        self.request["period"]["end"] = "2026-02-28"
        self.request["currencies"].append({"code": "EUR", "scale": 2})
        for interval in self.request["coverage"]:
            interval["end"] = "2026-02-28"
        session = json.loads(self.fixture["session_path"].read_bytes())
        session["source_grants"] = [s["source"] for s in self.request["sources"]]
        write_json(
            self.fixture["session_path"],
            bind_session_revisions(self.fixture["configuration"], session),
        )
        self.context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )

    def test_exact_monthly_series_separates_currencies_and_supports_comparisons(self):
        with (
            patch("socket.socket", side_effect=AssertionError("Network")),
            patch("subprocess.run", side_effect=AssertionError("Model")),
            localcontext() as arithmetic,
        ):
            arithmetic.prec = 3
            first = plan_packet(self.context, self.request)
        packet = json.loads(first[1]["packet.json"])
        self.assertEqual(
            packet["totals"],
            json.loads((FIXTURES / "two-period-totals.json").read_bytes()),
        )
        self.assertEqual(len(packet["evidence"]), 16)
        usd = [r for r in packet["totals"] if r["currency"] == "USD"]
        self.assertEqual(
            Decimal(usd[1]["net_movement"]) - Decimal(usd[0]["net_movement"]),
            Decimal("10.14"),
        )
        self.assertEqual(packet["questions"], self.request["questions"])
        self.assertEqual(first, plan_packet(self.context, self.request))
        self.assertNotIn(str(self.fixture["root"]), first[1]["packet.json"].decode())

    def test_selected_inputs_drive_chart_rows_and_evidence_without_currency_conversion(
        self,
    ):
        omitted = transaction_key("account-b", "euro-sale")
        self.request["selection"].remove(omitted)
        # Sources select calculation inputs; selection controls displayed rows.
        # Excluding a contributor requires an explicit reviewed input change.
        verified = resolve_source_evidence_batch(self.context, self.request["sources"])
        self.request["sources"] = [
            source
            for source, evidence in zip(self.request["sources"], verified)
            if json.loads(evidence["text"])["id"] != omitted
        ]
        self.request["decisions"] = [
            d for d in self.request["decisions"] if d["transaction"] != omitted
        ]
        _, files = plan_packet(self.context, self.request)
        packet = json.loads(files["packet.json"])
        euro = next(r for r in packet["totals"] if r["currency"] == "EUR")
        self.assertEqual(euro["income"], "0.00")
        self.assertEqual(euro["net_movement"], "-12.34")
        self.assertNotIn("Synthetic euro sale", files["packet.json"].decode())
        self.assertNotIn(omitted, json.dumps(packet["evidence"]))
        self.assertEqual(packet["questions"], self.request["questions"])


if __name__ == "__main__":
    unittest.main()
