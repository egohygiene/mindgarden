"""Real agent context consumers retain exact, selective dependency freshness."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.dependency_builds import plan_build, reconcile_build
from mindgarden.application.retrieval import render_context
from mindgarden.domain.contracts import canonical_json, read_object
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import dependency_fixture as fixture


def context_consumers(request):
    request = deepcopy(request)
    for output in request["outputs"]:
        if output["id"] == "professional-profile":
            continue
        profile = read_object(
            Path(__file__).parent / "fixtures/dependency-builds/context-profile.json"
        )
        profile["id"] = output["id"]
        profile["include"] = [
            {"garden": key.split("/")[0], "id": key.split("/")[1], "revision": None}
            for key in output["records"]
        ]
        output.update(
            renderer="context-pack/v1",
            output_schema="mindgarden.context/v1",
            context_profile=profile,
            context_format="json",
        )
    return request


class ContextDependencyTests(unittest.TestCase):
    def setUp(self):
        fixture.setup(self)
        self.request = context_consumers(self.request)

    def test_real_context_has_exact_evidence_and_no_ambient_record_metadata(self):
        plan = plan_build(self.context, self.request)
        payload = json.loads(plan.files["agent-context.json"])
        self.assertEqual(payload["schema"], "mindgarden.context/v1")
        self.assertEqual(
            [item["reference"]["id"] for item in payload["included"]], ["work-claim"]
        )
        self.assertTrue(payload["included"][0]["sources"])
        self.assertEqual(payload["inputs"][0]["kind"], "reviewed-record")
        self.assertEqual(payload["inputs"][0]["id"], "work-claim")
        self.assertNotIn(b"unrelated-procedure", plan.files["agent-context.json"])
        self.assertEqual(
            plan.document(), plan_build(self.context, self.request).document()
        )
        output = self.request["outputs"][1]
        output["context_format"] = "markdown"
        markdown = plan_build(self.context, self.request).files["agent-context.md"]
        self.assertIn(b"untrusted evidence", markdown)
        self.assertIn(b"work-claim", markdown)

    def test_missed_update_changes_only_affected_context_and_selected_renderer(self):
        before = plan_build(self.context, self.request)
        fixture.update(self)
        self.request = context_consumers(self.request)
        after = plan_build(self.context, self.request)
        states = {
            item["id"]: item["state"]
            for item in reconcile_build(after, before.manifest)["outputs"]
        }
        self.assertEqual(
            states,
            {
                "professional-profile": "stale",
                "agent-context": "stale",
                "unrelated-view": "current",
            },
        )
        self.assertEqual(
            before.files["unrelated-view.json"], after.files["unrelated-view.json"]
        )
        self.assertNotEqual(
            before.files["agent-context.json"], after.files["agent-context.json"]
        )
        calls = []

        def tracked(context, profile, format, **kwargs):
            calls.append(profile["id"])
            return render_context(context, profile, format, **kwargs)

        with patch(
            "mindgarden.application.dependency_builds.render_context",
            side_effect=tracked,
        ):
            selected = plan_build(
                self.context, self.request, output_ids=["agent-context"]
            )
        self.assertEqual(calls, ["agent-context"])
        self.assertEqual(
            selected.files["agent-context.json"], after.files["agent-context.json"]
        )

    def test_denied_or_outside_profile_selectors_fail_without_disclosure(self):
        original = deepcopy(self.request)
        for key in ("denied-garden/PRIVATE-CANARY", "synthetic-garden/missing"):
            self.request = deepcopy(original)
            self.request["outputs"][1]["records"] = [key]
            with self.assertRaisesRegex(ContractError, "BUILD_INPUT") as caught:
                plan_build(self.context, self.request)
            self.assertNotIn("PRIVATE-CANARY", str(caught.exception))
        self.request = deepcopy(original)
        self.request["outputs"][1]["context_profile"]["include"] = [
            {
                "garden": "synthetic-garden",
                "id": "unrelated-procedure",
                "revision": None,
            }
        ]
        with self.assertRaisesRegex(ContractError, "CONTEXT_SELECTION"):
            plan_build(self.context, self.request)

    def test_schema_requires_matching_consumer_profile_format_and_output_contract(self):
        for field in ("context_profile", "context_format"):
            request = deepcopy(self.request)
            del request["outputs"][1][field]
            with self.assertRaisesRegex(ContractError, "BUILD_REQUEST"):
                plan_build(self.context, request)
        request = deepcopy(self.request)
        request["outputs"][1]["output_schema"] = "mindgarden.reviewed-record-view/v1"
        with self.assertRaisesRegex(ContractError, "BUILD_REQUEST"):
            plan_build(self.context, request)

    def test_cli_reviewed_context_apply_replay_and_stale_digest_preserve_prior_bundle(
        self,
    ):
        request_path = self.root / "context-build.json"
        request_path.write_bytes(canonical_json(self.request))
        output = self.root / "contexts"
        arguments = [
            "build-projections",
            "--local-config",
            str(self.configuration),
            "--scope",
            str(self.session_path),
            "--input",
            str(request_path),
            "--select-output",
            "agent-context",
        ]
        with redirect_stdout(io.StringIO()) as preview:
            self.assertEqual(main(arguments), 0)
        digest = json.loads(preview.getvalue())["plan_sha256"]
        apply = arguments + [
            "--apply",
            "--output-directory",
            str(output),
            "--plan-digest",
            digest,
        ]
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(apply), 0)
            self.assertEqual(main(apply), 0)
        original = {path.name: path.read_bytes() for path in output.iterdir()}
        fixture.update(self)
        self.request = context_consumers(self.request)
        request_path.write_bytes(canonical_json(self.request))
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(apply), 3)
        self.assertEqual(
            original, {path.name: path.read_bytes() for path in output.iterdir()}
        )
