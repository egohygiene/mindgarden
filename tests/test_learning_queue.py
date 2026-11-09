"""A bounded due view composes the exact reviewed deck and private grade history."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.learning import plan_learning, review_queue
from mindgarden.domain.contracts import ContractRegistry
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import learning_fixture as fixture
from tests.support_v1 import write_json


class LearningQueueTests(unittest.TestCase):
    def setUp(self):
        fixture.setup(self)

    def test_due_view_is_bounded_provenance_bound_and_keeps_complete_round_trip(self):
        complete, all_files = plan_learning(self.context, self.request, self.history)
        preview, files = plan_learning(
            self.context, self.request, self.history, due_only=True, review_limit=1
        )
        queue = json.loads(files["study-queue.json"])
        self.assertEqual(ContractRegistry().errors(queue, "learning-review-queue"), [])
        self.assertEqual(
            (queue["total_due"], queue["remaining_due"], len(queue["items"])), (2, 1, 1)
        )
        (selected,) = queue["items"]
        entry = next(
            i
            for i in complete["projection"]["items"]
            if i["output"]["id"] == selected["item"]
        )
        self.assertEqual(selected["item_revision"], entry["revision"])
        self.assertTrue(entry["sources"])
        self.assertIn(entry["output"]["title"].encode(), files["study.html"])
        self.assertIn(b"1 later due cards remain", files["study.html"])
        self.assertEqual(
            files["learning-projection.json"], all_files["learning-projection.json"]
        )
        self.assertEqual(
            preview,
            plan_learning(
                self.context, self.request, self.history, due_only=True, review_limit=1
            )[0],
        )
        second = plan_learning(
            self.context,
            self.request,
            self.history,
            due_only=True,
            review_limit=1,
            review_offset=1,
        )[0]["study_selection"]
        self.assertNotEqual(second["items"][0]["item"], selected["item"])
        self.assertEqual(second["remaining_due"], 0)

    def test_grading_exact_revision_removes_only_that_card_until_due_again(self):
        initial = plan_learning(
            self.context, self.request, self.history, due_only=True
        )[0]
        card = initial["study_selection"]["items"][0]
        history = deepcopy(self.history)
        history["events"].append(
            {
                "schema": "mindgarden.learning-review-event/v1",
                "id": "due-review-one",
                "item": card["item"],
                "item_revision": card["item_revision"],
                "reviewed_at": self.request["as_of"],
                "reviewed_by": "synthetic-reviewer",
                "grade": "good",
                "scheduler": {"id": "fixed-intervals", "version": "1.0.0"},
                "previous_event": None,
            }
        )
        revised = plan_learning(self.context, self.request, history, due_only=True)[0]
        self.assertEqual(len(revised["study_selection"]["items"]), 1)
        self.assertNotIn(
            card["item"], [i["item"] for i in revised["study_selection"]["items"]]
        )
        old = deepcopy(history)
        old["events"][0]["item_revision"] = "sha256:" + "0" * 64
        stale = plan_learning(self.context, self.request, old, due_only=True)[0]
        self.assertEqual(stale["study_selection"]["total_due"], 2)
        self.assertTrue(stale["projection"]["historical_events"])

    def test_suspended_cards_and_summaries_do_not_enter_due_queue(self):
        for candidate in self.request["candidates"]:
            if candidate["output"]["schema"] == "mindgarden.learning-card/v1":
                candidate["output"]["lifecycle"] = "suspended"
        preview, files = plan_learning(
            self.context, self.request, self.history, due_only=True
        )
        self.assertEqual(preview["study_selection"]["items"], [])
        self.assertIn(b"No due learning cards", files["study.html"])
        self.assertEqual(len(preview["projection"]["items"]), 3)

    def test_invalid_queue_policy_fails_before_source_selection(self):
        for selection in (
            {"review_limit": 1},
            {"due_only": True, "review_limit": 0},
            {"due_only": True, "review_limit": 101},
            {"due_only": True, "review_offset": -1},
            {"due_only": True, "review_offset": True},
        ):
            with (
                self.subTest(selection=selection),
                patch(
                    "mindgarden.application.learning.selection_view",
                    side_effect=AssertionError("Body opened"),
                ),
            ):
                with self.assertRaisesRegex(ContractError, "LEARNING_SELECTION"):
                    plan_learning(self.context, self.request, self.history, **selection)

    def test_queue_order_uses_time_instants_before_pagination(self):
        projection = plan_learning(self.context, self.request, self.history)[0][
            "projection"
        ]
        first, second = projection["schedules"]
        first.update(due=True, due_at="2026-11-05T23:30:00Z")
        second.update(due=True, due_at="2026-11-06T01:00:00+02:00")
        queue = review_queue(projection, offset=0, limit=1)
        self.assertEqual(queue["items"][0]["item"], second["item"])

    def test_cli_selected_digest_apply_and_complete_json_import_round_trip(self):
        path = self.root / "learning.json"
        write_json(path, self.request)
        output = self.root / "due-export"
        args = [
            "learning",
            "--local-config",
            str(self.configuration),
            "--scope",
            str(self.session_path),
            "--input",
            str(path),
            "--due-only",
            "--review-limit",
            "1",
        ]

        def run(arguments, expected=0):
            with (
                patch(
                    "mindgarden.application.learning.QueryContext.load",
                    return_value=self.context,
                ),
                redirect_stdout(io.StringIO()) as out,
                redirect_stderr(io.StringIO()) as error,
            ):
                self.assertEqual(main(arguments), expected, error.getvalue())
            return json.loads(out.getvalue()) if expected == 0 else None

        preview = run(args)
        default = plan_learning(self.context, self.request, self.history)[0]
        run(
            [
                *args,
                "--apply",
                "--output-directory",
                str(output),
                "--plan-digest",
                default["plan_sha256"],
            ],
            3,
        )
        self.assertFalse(output.exists())
        before = {
            p: p.read_bytes()
            for p in (self.workspace / ".garden").rglob("*")
            if p.is_file()
        }
        run(
            [
                *args,
                "--apply",
                "--output-directory",
                str(output),
                "--plan-digest",
                preview["plan_sha256"],
            ]
        )
        imported = run(
            [
                "learning",
                "--local-config",
                str(self.configuration),
                "--scope",
                str(self.session_path),
                "--import-projection",
                str(output / "learning-projection.json"),
                "--due-only",
                "--review-limit",
                "1",
            ]
        )
        self.assertEqual(imported["projection"], preview["projection"])
        self.assertEqual(imported["study_selection"], preview["study_selection"])
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)

    def test_revoked_authority_cannot_render_a_due_view(self):
        document = json.loads(self.configuration.read_bytes())
        document["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.configuration, document)
        with patch(
            "mindgarden.application.learning.render_learning",
            side_effect=AssertionError("Denied body rendered"),
        ):
            with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
                plan_learning(self.context, self.request, self.history, due_only=True)

    def test_due_export_cannot_write_into_source_vault(self):
        path = self.root / "learning.json"
        write_json(path, self.request)
        preview = plan_learning(
            self.context, self.request, self.history, due_only=True
        )[0]
        destination = (
            Path(self.context.bindings.document["vaults"][0]["root"]) / "study-copy"
        )
        with (
            patch(
                "mindgarden.application.learning.QueryContext.load",
                return_value=self.context,
            ),
            redirect_stderr(io.StringIO()) as error,
        ):
            code = main(
                [
                    "learning",
                    "--local-config",
                    str(self.configuration),
                    "--scope",
                    str(self.session_path),
                    "--input",
                    str(path),
                    "--due-only",
                    "--apply",
                    "--output-directory",
                    str(destination),
                    "--plan-digest",
                    preview["plan_sha256"],
                ]
            )
        self.assertEqual(code, 3)
        self.assertIn("FEDERATION_OUTPUT", error.getvalue())
        self.assertFalse(destination.exists())
