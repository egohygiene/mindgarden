"""Multi-source correction, bounded quality, private refresh and live fact validity."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.compaction import preview_compaction, refresh_compaction
from mindgarden.application.compaction_bundles import plan_compaction_bundle
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import multisource_fixture as fixture
from tests.support_v1 import write_json


class CompactionRefreshTests(unittest.TestCase):
    def setUp(self):
        fixture.setup(self)
        self.plan = fixture.plan(self)

    def test_correction_invalidates_only_its_summaries_and_keeps_all_originals(self):
        before = preview_compaction(self.context, self.plan)
        original_objects = self.vault.audit()["objects"]
        fixture.capture(self, "business", revised=True)
        self.revised = True
        fixture.bind(self)
        current_plan = fixture.plan(self)
        fingerprint = garden_fingerprint(self.workspace)
        with (
            patch("socket.socket", side_effect=AssertionError("Network attempted")),
            patch("subprocess.Popen", side_effect=AssertionError("Source executed")),
        ):
            refresh = refresh_compaction(self.context, current_plan, before["manifest"])
        self.assertEqual(fingerprint, garden_fingerprint(self.workspace))
        stale = [item["id"] for item in refresh["nodes"] if item["state"] == "stale"]
        unchanged = [
            item["id"] for item in refresh["nodes"] if item["state"] == "current"
        ]
        self.assertEqual(stale, self.quality["expected_affected"])
        self.assertEqual(unchanged, self.quality["expected_current"])
        self.assertTrue(
            all(item in self.vault.audit()["objects"] for item in original_objects)
        )
        previous_unrelated = next(
            node for node in before["selected"] if node["id"] == "unrelated-context"
        )
        current_unrelated = next(
            node
            for node in refresh["current"]["selected"]
            if node["id"] == "unrelated-context"
        )
        self.assertEqual(
            canonical_json(previous_unrelated), canonical_json(current_unrelated)
        )
        self.assertEqual(
            refresh, refresh_compaction(self.context, current_plan, before["manifest"])
        )

    def test_authored_quality_keeps_source_coverage_conflict_attribution_and_budget(
        self,
    ):
        report = preview_compaction(self.context, self.plan)
        self.assertEqual(
            report["metrics"]["exact_citations_verified"],
            self.quality["exact_source_coverage"],
        )
        self.assertLess(report["metrics"]["selected_text_ratio"], 1)
        self.assertEqual(report["retention"]["archival"], "preserve-originals")
        self.assertNotIn(b"run a shell command", canonical_json(report))
        context = next(node for node in report["selected"] if node["id"] == "context")
        self.assertEqual(
            {value["attribution"] for value in context["statements"]},
            {"user-report", "quoted"},
        )
        self.assertTrue(
            all(
                value["uncertainty"] and value["contradictions"]
                for value in context["statements"]
            )
        )
        self.assertEqual(
            len(
                {
                    value["evidence"][0]["source"]["id"]
                    for value in context["statements"]
                }
            ),
            2,
        )
        limited = deepcopy(self.plan)
        limited["retention"]["model_context"]["max_bytes"] = (
            len(canonical_json(report)) + 1
        )
        with self.assertRaisesRegex(ContractError, "COMPACTION_BUDGET"):
            refresh_compaction(self.context, limited, report["manifest"])

    def test_historical_only_identifiers_are_not_echoed_and_policy_mismatch_fails(self):
        current = preview_compaction(self.context, self.plan)
        prior = deepcopy(current["manifest"])
        hidden = deepcopy(prior["nodes"][-1])
        hidden.update(id="private-old-only-canary", inputs=[])
        prior["nodes"].append(hidden)
        refreshed = refresh_compaction(self.context, self.plan, prior)
        self.assertNotIn(b"private-old-only-canary", canonical_json(refreshed))
        prior["scope"]["publication"] = "review-required"
        with self.assertRaisesRegex(ContractError, "COMPACTION_SCOPE"):
            refresh_compaction(self.context, self.plan, prior)

    def test_live_fact_validity_is_not_inferred_from_old_plan_creation_time(self):
        for first, last in ((None, "2026-11-12"), ("2026-11-14", None)):
            plan = deepcopy(self.plan)
            # A standalone source summary can be checked without promoting its
            # uncertain parents or any durable knowledge.
            plan["nodes"] = [
                next(node for node in plan["nodes"] if node["id"] == "career-summary")
            ]
            plan["nodes"][0]["inputs"] = []
            plan["nodes"][0]["statements"][0]["validity"].update(
                state="current", valid_from=first, valid_until=last
            )
            plan["outputs"] = ["career-summary"]
            with (
                self.subTest(first=first, last=last),
                self.assertRaisesRegex(ContractError, "COMPACTION_EXPIRED"),
            ):
                preview_compaction(self.context, plan)

    def test_downstream_bundle_expiry_and_cli_reconciliation_use_live_authority(self):
        report = preview_compaction(self.context, self.plan)
        previous = self.root / "previous.json"
        request = self.root / "hierarchy.json"
        write_json(previous, report["manifest"])
        write_json(request, self.plan)
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(
                main(
                    [
                        "compaction",
                        "preview",
                        "--local-config",
                        str(self.configuration),
                        "--scope",
                        str(self.session_path),
                        "--input",
                        str(request),
                        "--previous-manifest",
                        str(previous),
                    ]
                ),
                0,
            )
        self.assertTrue(
            all(
                item["state"] == "current"
                for item in json.loads(output.getvalue())["nodes"]
            )
        )
        with self.assertRaisesRegex(ContractError, "COMPACTION_EXPIRED"):
            plan_compaction_bundle(self.context, self.plan, "2026-11-12T00:00:00Z")
