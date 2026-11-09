"""Explicit targeted builds retain canonical dependency, review and apply guards."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.dependency_builds import (
    plan_build,
    reconcile_build,
    render_records,
)
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import dependency_fixture as fixture
from tests.support_v1 import write_json


class SelectedBuildTests(unittest.TestCase):
    def setUp(self):
        fixture.setup(self)

    def test_only_selected_renderers_run_and_fingerprints_match_complete_build(self):
        complete = plan_build(self.context, self.request)
        calls = []

        def render(records, profile):
            calls.append([r["id"] for r in records])
            return render_records(records, profile)

        selected = plan_build(
            self.context, self.request, output_ids=["agent-context"], renderer=render
        )
        self.assertEqual(calls, [["work-claim"]])
        self.assertEqual(
            set(selected.files), {"agent-context.json", "projection-dependencies.json"}
        )
        self.assertEqual(
            selected.manifest["projections"],
            [p for p in complete.manifest["projections"] if p["id"] == "agent-context"],
        )
        self.assertEqual(selected.document()["selected_outputs"], ["agent-context"])
        self.assertNotEqual(
            selected.document()["plan_sha256"], complete.document()["plan_sha256"]
        )
        self.assertNotIn("selected_outputs", complete.document())

    def test_missed_event_reconciliation_drives_only_affected_builds(self):
        before = plan_build(self.context, self.request)
        fixture.update(self)
        current = plan_build(self.context, self.request)
        affected = [
            item["id"]
            for item in reconcile_build(current, before.manifest)["outputs"]
            if item["state"] == "stale"
        ]
        self.assertEqual(affected, ["agent-context", "professional-profile"])
        selected = plan_build(self.context, self.request, output_ids=affected)
        self.assertEqual(
            {p["id"] for p in selected.manifest["projections"]}, set(affected)
        )
        self.assertNotIn("unrelated-view.json", selected.files)
        self.assertEqual(
            current.files["unrelated-view.json"], before.files["unrelated-view.json"]
        )
        self.assertEqual(
            selected.files["agent-context.json"], current.files["agent-context.json"]
        )
        again = plan_build(
            self.context, self.request, output_ids=list(reversed(affected))
        )
        self.assertEqual(selected.document(), again.document())

    def test_invalid_selection_denies_before_authorized_index_or_renderer_access(self):
        for selection in (
            [],
            ["missing-private-canary"],
            ["agent-context", "agent-context"],
            "agent-context",
            [1],
        ):
            with (
                self.subTest(selection=selection),
                patch(
                    "mindgarden.application.dependency_builds.build_index",
                    side_effect=AssertionError("Index opened"),
                ),
            ):
                with self.assertRaisesRegex(ContractError, "BUILD_SELECTION") as error:
                    plan_build(self.context, self.request, output_ids=selection)
                self.assertNotIn("missing-private-canary", str(error.exception))

    def test_selected_cli_apply_is_digest_bound_repeatable_and_does_not_mutate_sources(
        self,
    ):
        path = self.root / "request.json"
        write_json(path, self.request)
        output = self.root / "targeted"
        args = [
            "build-projections",
            "--local-config",
            str(self.configuration),
            "--scope",
            str(self.session_path),
            "--input",
            str(path),
            "--select-output",
            "agent-context",
        ]
        source_bytes = {
            p: p.read_bytes()
            for p in (self.workspace / ".garden").rglob("*")
            if p.is_file()
        }
        with redirect_stdout(io.StringIO()) as preview:
            self.assertEqual(main(args), 0)
        digest = json.loads(preview.getvalue())["plan_sha256"]
        full_digest = plan_build(self.context, self.request).document()["plan_sha256"]
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                main(
                    [
                        *args,
                        "--apply",
                        "--output-directory",
                        str(output),
                        "--plan-digest",
                        full_digest,
                    ]
                ),
                3,
            )
        self.assertFalse(output.exists())
        with redirect_stdout(io.StringIO()):
            apply = [
                *args,
                "--apply",
                "--output-directory",
                str(output),
                "--plan-digest",
                digest,
            ]
            self.assertEqual(main(apply), 0)
            self.assertEqual(main(apply), 0)
        self.assertEqual(
            {p.name for p in output.iterdir()},
            {
                "agent-context.json",
                "projection-dependencies.json",
                ".mindgarden-generated.json",
            },
        )
        for p, content in source_bytes.items():
            self.assertEqual(p.read_bytes(), content)

    def test_selection_binds_complete_request_and_does_not_bypass_revocation(self):
        selected = plan_build(self.context, self.request, output_ids=["agent-context"])
        self.request["outputs"][2]["version"] = "1.1.0"
        self.assertNotEqual(
            selected.document()["plan_sha256"],
            plan_build(
                self.context, self.request, output_ids=["agent-context"]
            ).document()["plan_sha256"],
        )
        document = json.loads(self.configuration.read_bytes())
        document["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.configuration, document)
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            plan_build(self.context, self.request, output_ids=["agent-context"])
