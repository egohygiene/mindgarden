"""Review gates, exact provenance, private history and deterministic schedule/export."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from mindgarden.application.learning import plan_learning
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.domain.learning import FixedIntervals
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.validation import ContractError
from mindgarden.domain.scope import local_scope
from mindgarden.interfaces.cli import main
from tests import learning_fixture as fixture
from tests.support_v1 import write_json, write_session


class LearningTests(unittest.TestCase):
    def setUp(self):
        fixture.setup(self)

    def event(self, revision, **changes):
        return {
            "schema": "mindgarden.learning-review-event/v1",
            "id": "review-one",
            "item": "source-card",
            "item_revision": revision,
            "reviewed_at": "2026-11-05T00:00:00Z",
            "reviewed_by": "synthetic-reviewer",
            "grade": "good",
            "scheduler": {"id": "fixed-intervals", "version": "1.0.0"},
            "previous_event": None,
            **changes,
        }

    def test_fact_cloze_summary_exact_evidence_and_deterministic_private_exports(self):
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            preview, files = plan_learning(self.context, self.request, self.history)
        self.assertEqual(
            (preview, files), plan_learning(self.context, self.request, self.history)
        )
        projection = preview["projection"]
        self.assertEqual(
            ContractRegistry().errors(projection, "learning-projection"), []
        )
        self.assertEqual(len(projection["schedules"]), 2)
        self.assertTrue(all(e["sources"][0]["evidence"] for e in projection["items"]))
        self.assertEqual(projection["scope"]["visibility"], "personal")
        self.assertNotIn(str(self.root), canonical_json(preview).decode())
        self.assertIn(b"<summary>Reveal answer</summary>", files["study.html"])
        self.assertNotIn(b"{{c1::", files["study.html"])
        self.assertEqual(
            json.loads(files["learning-review-history.json"])["publication"],
            "never-exportable",
        )

    def test_review_history_chain_and_explicit_scheduler_upgrade(self):
        preview, _ = plan_learning(self.context, self.request, self.history)
        entry = next(
            i
            for i in preview["projection"]["items"]
            if i["output"]["id"] == "source-card"
        )
        self.history["events"] = [self.event(entry["revision"])]
        before = canonical_json(self.history)
        current = plan_learning(self.context, self.request, self.history)[0][
            "projection"
        ]
        schedule = next(s for s in current["schedules"] if s["item"] == "source-card")
        self.assertEqual(schedule["due_at"], "2026-11-08T00:00:00Z")
        self.request["scheduler"]["version"] = "2.0.0"
        upgraded = next(
            s
            for s in plan_learning(self.context, self.request, self.history)[0][
                "projection"
            ]["schedules"]
            if s["item"] == "source-card"
        )
        self.assertEqual(upgraded["reason"], "explicit-scheduler-upgrade")
        self.assertEqual(upgraded["due_at"], "2026-11-07T00:00:00Z")
        self.assertEqual(before, canonical_json(self.history))
        self.history["events"][0]["previous_event"] = "missing"
        with self.assertRaisesRegex(ContractError, "LEARNING_HISTORY"):
            plan_learning(self.context, self.request, self.history)

    def test_edit_reject_suspend_and_prior_version_history_never_modify_sources(self):
        before = {p: p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()}
        preview, _ = plan_learning(self.context, self.request, self.history)
        entry = next(
            i
            for i in preview["projection"]["items"]
            if i["output"]["id"] == "source-card"
        )
        self.history["events"] = [self.event(entry["revision"])]
        self.request["candidates"][0]["output"]["prompt"] = "Edited recall prompt."
        self.request["candidates"][1]["output"]["lifecycle"] = "suspended"
        self.request["candidates"][2]["output"]["lifecycle"] = "rejected"
        self.request["candidates"][2]["output"]["review"]["state"] = "rejected"
        result, files = plan_learning(self.context, self.request, self.history)
        self.assertEqual(len(result["projection"]["schedules"]), 1)
        self.assertEqual(
            result["projection"]["historical_events"][0]["state"],
            "historical-item-revision",
        )
        self.assertNotIn(b"Portable reviewed knowledge", files["study.html"])
        self.assertEqual(
            before,
            {p: p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()},
        )

    def test_declared_contradictions_require_qualified_answer_and_keep_uncertainty(
        self,
    ):
        path = self.workspace / ".garden/claims/learning-claim.json"
        claim = json.loads(path.read_text())
        claim["evidence"].append(
            {
                **claim["evidence"][0],
                "relationship": "contradicts",
                "rationale": "Explicit synthetic conflicting evidence.",
            }
        )
        write_json(path, claim)
        session = write_session(self.session_path, self.configuration)
        session["budgets"]["max_context_bytes"] = 131072
        write_json(self.session_path, session)
        self.context = QueryContext.load(
            self.configuration, self.session_path, clock=fixture.CLOCK
        )
        index = build_index(self.context)
        self.request["candidates"][0]["references"] = [
            next(
                r["reference"] for r in index["records"] if r["id"] == "learning-claim"
            )
        ]
        with self.assertRaisesRegex(ContractError, "LEARNING_QUALIFICATION"):
            plan_learning(self.context, self.request)
        self.request["candidates"][0]["output"]["answer"]["certainty"] = "qualified"
        preview, files = plan_learning(self.context, self.request)
        self.assertIn(
            "contradictory-source",
            preview["projection"]["items"][-1]["qualification_reasons"],
        )
        self.assertIn(b"contradictory-source", files["study.md"])

    def test_unknown_denied_stale_and_public_history_fail_without_source_disclosure(
        self,
    ):
        original = deepcopy(self.request)
        self.request["candidates"][0]["references"][0]["id"] = "denied-canary"
        with self.assertRaisesRegex(ContractError, "SELECTION_UNAVAILABLE") as error:
            plan_learning(self.context, self.request)
        self.assertNotIn("denied-canary", str(error.exception))
        self.request = deepcopy(original)
        self.request["scope"] = local_scope("public", publication="publishable")
        with self.assertRaisesRegex(ContractError, "LEARNING_PRIVATE"):
            plan_learning(self.context, self.request)
        self.request = deepcopy(original)
        self.request["candidates"][0]["references"][0]["revision"] = (
            "sha256:" + "0" * 64
        )
        with self.assertRaisesRegex(ContractError, "SELECTION_UNAVAILABLE"):
            plan_learning(self.context, self.request)

    def test_empty_authored_mode_and_replaceable_scheduler_require_no_model(self):
        self.request["candidates"] = []
        result, files = plan_learning(self.context, self.request)
        self.assertEqual(result["projection"]["items"], [])
        self.assertIn(b"No approved learning items", files["study.html"])
        self.request["scheduler"]["id"] = "unavailable"
        with self.assertRaisesRegex(ContractError, "LEARNING_SCHEDULER"):
            plan_learning(self.context, self.request)
        result, _ = plan_learning(
            self.context,
            self.request,
            schedulers={("unavailable", "1.0.0"): FixedIntervals((2, 4))},
        )
        self.assertEqual(result["projection"]["schedules"], [])

    def test_cli_plan_apply_replay_and_import_roundtrip(self):
        path = self.root / "learning-plan.json"
        path.write_bytes(canonical_json(self.request))
        out = self.root / "study-export"
        args = [
            "learning",
            "--local-config",
            str(self.configuration),
            "--scope",
            str(self.session_path),
            "--input",
            str(path),
        ]
        with (
            patch(
                "mindgarden.application.learning.QueryContext.load",
                return_value=self.context,
            ),
            redirect_stdout(io.StringIO()) as preview,
        ):
            self.assertEqual(main(args), 0)
        digest = json.loads(preview.getvalue())["plan_sha256"]
        with (
            patch(
                "mindgarden.application.learning.QueryContext.load",
                return_value=self.context,
            ),
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(
                main(
                    args
                    + [
                        "--apply",
                        "--output-directory",
                        str(out),
                        "--plan-digest",
                        digest,
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    args
                    + [
                        "--apply",
                        "--output-directory",
                        str(out),
                        "--plan-digest",
                        digest,
                    ]
                ),
                0,
            )
        imported = [
            "learning",
            "--local-config",
            str(self.configuration),
            "--scope",
            str(self.session_path),
            "--import-projection",
            str(out / "learning-projection.json"),
        ]
        with (
            patch(
                "mindgarden.application.learning.QueryContext.load",
                return_value=self.context,
            ),
            redirect_stdout(io.StringIO()) as roundtrip,
        ):
            self.assertEqual(main(imported), 0)
        self.assertEqual(
            json.loads(roundtrip.getvalue())["projection"],
            json.loads((out / "learning-projection.json").read_text()),
        )
        self.request["candidates"][0]["output"]["prompt"] = "Changed after preview"
        path.write_bytes(canonical_json(self.request))
        with (
            patch(
                "mindgarden.application.learning.QueryContext.load",
                return_value=self.context,
            ),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(
                main(
                    args
                    + [
                        "--apply",
                        "--output-directory",
                        str(self.root / "stale"),
                        "--plan-digest",
                        digest,
                    ]
                ),
                3,
            )
        self.assertFalse((self.root / "stale").exists())

    def test_unreviewed_proposals_and_unsafe_markup_do_not_gain_authority(self):
        candidate = self.request["candidates"][0]["output"]
        candidate["review"] = {
            "state": "unreviewed",
            "reviewers": [],
            "reviewed_at": None,
            "rationale": None,
        }
        with self.assertRaisesRegex(ContractError, "LEARNING_REVIEW"):
            plan_learning(self.context, self.request)
        candidate["lifecycle"] = "proposed"
        result, files = plan_learning(self.context, self.request)
        self.assertNotIn(b"What happens to the original", files["study.html"])
        self.request["candidates"][1]["output"]["title"] = (
            "<script>fixture()</script> ![image](https://example.test/track)"
        )
        _, files = plan_learning(self.context, self.request)
        self.assertNotIn(b"<script>", files["study.html"])
        self.assertIn(b"&lt;script&gt;", files["study.html"])
        self.assertNotIn(b"![image]", files["study.md"])

    def test_new_source_revision_invalidates_old_grading_even_when_card_text_is_unchanged(
        self,
    ):
        from mindgarden.application.ingestion import apply_ingestion
        from tests import test_source_adapters as source_tests

        before, _ = plan_learning(self.context, self.request)
        original = next(
            i
            for i in before["projection"]["items"]
            if i["output"]["id"] == "source-card"
        )
        self.history["events"] = [self.event(original["revision"])]
        original_objects = deepcopy(self.vault.audit()["objects"])
        self.input.write_text(
            "Original sources stay immutable.\nA newly captured synthetic revision adds scope clarification.\n"
        )
        ingestion = source_tests.SourceAdapterTests.plan(self)
        apply_ingestion(ingestion, ingestion.digest, self.bindings, "synthetic-vault")
        path = self.workspace / ".garden/claims/learning-claim.json"
        claim = json.loads(path.read_text())
        claim["evidence"][0]["target"] = ingestion.inputs["normalized_sources"][0][
            "evidence"
        ][0]
        write_json(path, claim)
        session = write_session(self.session_path, self.configuration)
        session["budgets"]["max_context_bytes"] = 131072
        write_json(self.session_path, session)
        self.context = QueryContext.load(
            self.configuration, self.session_path, clock=fixture.CLOCK
        )
        current = next(
            r
            for r in build_index(self.context)["records"]
            if r["id"] == "learning-claim"
        )
        self.request["candidates"][0]["references"] = [current["reference"]]
        after, _ = plan_learning(self.context, self.request, self.history)
        changed = next(
            i
            for i in after["projection"]["items"]
            if i["output"]["id"] == "source-card"
        )
        self.assertEqual(changed["output"], original["output"])
        self.assertNotEqual(changed["revision"], original["revision"])
        self.assertEqual(
            after["projection"]["historical_events"][0]["state"],
            "historical-item-revision",
        )
        self.assertTrue(
            all(o in self.vault.audit()["objects"] for o in original_objects)
        )

    def test_review_event_can_refresh_imported_projection_without_reapproving_derived_schedules(
        self,
    ):
        projection, _ = plan_learning(self.context, self.request)
        path = self.root / "import.json"
        path.write_bytes(canonical_json(projection["projection"]))
        card = next(
            i
            for i in projection["projection"]["items"]
            if i["output"]["id"] == "source-card"
        )
        event = self.root / "review-event.json"
        event.write_bytes(canonical_json(self.event(card["revision"])))
        args = [
            "learning",
            "--local-config",
            str(self.configuration),
            "--scope",
            str(self.session_path),
            "--import-projection",
            str(path),
            "--review-event",
            str(event),
        ]
        with (
            patch(
                "mindgarden.application.learning.QueryContext.load",
                return_value=self.context,
            ),
            redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(main(args), 0)
        result = json.loads(output.getvalue())["projection"]
        schedule = next(s for s in result["schedules"] if s["item"] == "source-card")
        self.assertEqual(schedule["last_event"], "review-one")
        self.assertEqual(json.loads(path.read_text()), projection["projection"])

    def test_budget_and_unauthorized_history_are_rejected_without_partial_export(self):
        self.request["max_bytes"] = 512
        with self.assertRaisesRegex(ContractError, "LEARNING_BUDGET"):
            plan_learning(self.context, self.request)
        self.request["max_bytes"] = 131072
        self.history["events"] = [
            self.event("sha256:" + "0" * 64, item="denied-review-canary")
        ]
        with self.assertRaisesRegex(ContractError, "LEARNING_HISTORY") as error:
            plan_learning(self.context, self.request, self.history)
        self.assertNotIn("denied-review-canary", str(error.exception))

    def test_committed_authored_plan_and_projection_golden_are_reproducible(self):
        root = Path(__file__).parent / "fixtures/learning"
        self.assertEqual(
            self.request, json.loads((root / "authored-plan.json").read_text())
        )
        preview, files = plan_learning(self.context, self.request)
        proof = {
            "schema": "mindgarden.synthetic-learning-proof/v1",
            "items": [
                {
                    "id": i["output"]["id"],
                    "revision": i["revision"],
                    "sources": i["sources"],
                }
                for i in preview["projection"]["items"]
            ],
            "schedules": preview["projection"]["schedules"],
            "files": {name: digest_bytes(content) for name, content in files.items()},
            "total_bytes": preview["total_bytes"],
            "model": "unused",
            "review_history": "private",
        }
        self.assertEqual(proof, json.loads((root / "expected-proof.json").read_text()))
