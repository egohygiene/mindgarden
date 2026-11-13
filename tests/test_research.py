"""Read-only caller boundary, cumulative limits and live authority without models."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.query import QueryContext
from mindgarden.application.research import research
from mindgarden.domain.contracts import ContractRegistry, canonical_json
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.research_fixture import create_fixture, request_for
from tests.support_v1 import write_json


class ResearchTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fixture = create_fixture(Path(temporary.name))
        self.context = self.fixture["context"]
        self.request = request_for(self.context, [self.fixture["citation"]])

    def test_two_distinguishable_caller_plans_and_provider_removal_keep_exact_citations(
        self,
    ):
        original = Path.read_bytes

        def guard(path):
            if path.name == "private-draft.md":
                raise AssertionError("Denied body read")
            return original(path)

        with (
            patch.object(Path, "read_bytes", guard),
            patch("socket.socket", side_effect=AssertionError("Network")),
            patch("subprocess.run", side_effect=AssertionError("Execution")),
        ):
            outputs = [
                research(
                    self.context,
                    request_for(
                        self.context, [self.fixture["citation"]], planner=planner
                    ),
                )
                for planner in ("search-first", "graph-first")
            ]
            direct = deepcopy(self.request)
            direct["steps"] = direct["steps"][:1]
            direct["planner"]["id"] = "provider-removed-direct-search"
            self.assertTrue(research(self.context, direct)["observations"])
        self.assertNotEqual(
            [v["operation"] for v in outputs[0]["observations"]],
            [v["operation"] for v in outputs[1]["observations"]],
        )
        for result in outputs:
            self.assertEqual(ContractRegistry().errors(result, "research-result"), [])
            self.assertEqual(result["scope"]["publication"], "never-exportable")
            self.assertEqual(result["usage"]["model_calls"], 0)
            self.assertEqual(result["interpretations"], [])
            text = canonical_json(result)
            self.assertNotIn(b"DENIED-DRAFT-CANARY", text)
            self.assertNotIn(str(self.fixture["root"]).encode(), text)
            self.assertIn(
                b"publish secrets", text
            )  # Retained as untrusted source data.
            evidence = next(
                v["payload"]
                for v in result["observations"]
                if v["operation"] == "source-evidence"
            )
            self.assertEqual(evidence["source"], self.fixture["citation"]["source"])
            self.assertEqual(evidence["source_review"]["state"], "unreviewed")

    def test_invalid_later_tool_cannot_cause_earlier_body_reads(self):
        cases = []
        bad = deepcopy(self.request)
        bad["steps"].append({"operation": "shell", "command": "execute"})
        cases.append(bad)
        bad = deepcopy(self.request)
        bad["allowed_tools"] = ["search"]
        cases.append(bad)
        bad = deepcopy(self.request)
        bad["steps"][0]["gardens"][0]["revision"] = "sha256:" + "0" * 64
        cases.append(bad)
        bad = deepcopy(self.request)
        bad["sources"][0]["source"]["revision"] = None
        cases.append(bad)
        for request in cases:
            with (
                self.subTest(),
                patch.object(
                    QueryContext, "snapshots", side_effect=AssertionError("Body read")
                ),
                self.assertRaises(ContractError),
            ):
                research(self.context, request)

    def test_source_grants_and_projection_denials_precede_all_body_reads(self):
        for field in ("source_grants", "projections"):
            session = json.loads(self.fixture["session_path"].read_bytes())
            saved = deepcopy(session)
            if field == "source_grants":
                session.pop(field)
            else:
                session[field] = ["index"]
            write_json(self.fixture["session_path"], session)
            context = QueryContext.load(
                self.fixture["configuration"], self.fixture["session_path"]
            )
            with (
                patch.object(
                    QueryContext, "snapshots", side_effect=AssertionError("Body read")
                ),
                self.assertRaises(ContractError),
            ):
                research(context, self.request)
            write_json(self.fixture["session_path"], saved)

    def test_cumulative_step_result_byte_and_time_limits_fail_without_partial_output(
        self,
    ):
        for name, value in (
            ("max_steps", 1),
            ("max_results", 1),
            ("max_bytes", 400),
            ("max_elapsed_ms", 1),
        ):
            request = deepcopy(self.request)
            request["budgets"][name] = value
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ContractError, "RESEARCH_BUDGET"),
            ):
                research(
                    self.context,
                    request,
                    monotonic=iter([0, 1, 2, 3, 4]).__next__
                    if name == "max_elapsed_ms"
                    else lambda: 0,
                )

    def test_live_revocation_between_steps_and_interruption_return_no_result(self):
        from mindgarden.application import research as module

        original = module.query_local

        def revoke(*args):
            result = original(*args)
            config = json.loads(self.fixture["configuration"].read_bytes())
            config["revoked_sessions"].append(self.context.session["id"])
            write_json(self.fixture["configuration"], config)
            return result

        with (
            patch.object(module, "query_local", revoke),
            self.assertRaisesRegex(ContractError, "SESSION_REVOKED"),
        ):
            research(self.context, self.request)

    def test_request_expiry_and_stale_selected_revision_fail_before_bodies(self):
        context = QueryContext.load(
            self.fixture["configuration"],
            self.fixture["session_path"],
            clock=lambda: datetime(2098, 2, 1, tzinfo=timezone.utc),
        )
        with (
            patch.object(
                QueryContext, "snapshots", side_effect=AssertionError("Body read")
            ),
            self.assertRaisesRegex(ContractError, "SESSION_EXPIRED"),
        ):
            research(context, self.request)
        for step in self.request["steps"]:
            if "gardens" in step:
                step["gardens"][0]["revision"] = "sha256:" + "0" * 64
        self.request["gardens"][0]["revision"] = "sha256:" + "0" * 64
        with (
            patch.object(
                QueryContext, "snapshots", side_effect=AssertionError("Body read")
            ),
            self.assertRaisesRegex(ContractError, "SESSION_REVISION"),
        ):
            research(self.context, self.request)

    def test_complete_metadata_counts_against_byte_ceiling_and_no_hit_is_qualified(
        self,
    ):
        self.request["steps"] = self.request["steps"][:1]
        self.request["steps"][0]["query"] = "no-such-synthetic-query"
        result = research(self.context, self.request)
        self.assertEqual(result["status"], "insufficient-evidence")
        self.assertEqual(result["usage"]["results"], 0)
        self.request["budgets"]["max_bytes"] = len(canonical_json(result)) - 1
        with self.assertRaisesRegex(ContractError, "RESEARCH_BUDGET"):
            research(self.context, self.request)

    def test_stale_request_and_unknown_tool_cli_errors_are_shareable(self):
        request_path = self.fixture["root"] / "research.json"
        self.request["steps"].append({"operation": "run-private-secret-command"})
        write_json(request_path, self.request)
        with (
            redirect_stdout(io.StringIO()) as stdout,
            redirect_stderr(io.StringIO()) as stderr,
        ):
            result = main(
                [
                    "research",
                    "--input",
                    str(request_path),
                    "--local-config",
                    str(self.fixture["configuration"]),
                    "--scope",
                    str(self.fixture["session_path"]),
                    "--diagnostic-format",
                    "json",
                ]
            )
        self.assertEqual(result, 3)
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn(str(request_path), stderr.getvalue())
        self.assertNotIn("run-private-secret", stderr.getvalue())
        with self.assertRaisesRegex(ContractError, "RESEARCH_STALE"):
            research(
                self.context,
                request_for(self.context),
                verify_request=lambda: (_ for _ in ()).throw(
                    ContractError("RESEARCH_STALE: private-input")
                ),
            )

    def test_cli_success_does_not_create_traces_or_mutate_sources(self):
        request_path = self.fixture["root"] / "research.json"
        write_json(request_path, self.request)
        before = {
            p.relative_to(self.fixture["root"]): p.read_bytes()
            for p in self.fixture["root"].rglob("*")
            if p.is_file()
        }
        with redirect_stdout(io.StringIO()) as stdout:
            result = main(
                [
                    "research",
                    "--input",
                    str(request_path),
                    "--local-config",
                    str(self.fixture["configuration"]),
                    "--scope",
                    str(self.fixture["session_path"]),
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(stdout.getvalue())["usage"]["model_calls"], 0)
        after = {
            p.relative_to(self.fixture["root"]): p.read_bytes()
            for p in self.fixture["root"].rglob("*")
            if p.is_file()
        }
        self.assertEqual(before, after)

    def test_interrupted_second_step_cli_exposes_no_partial_observations_or_private_error(
        self,
    ):
        from mindgarden.application import research as module

        original = module.query_local
        calls = []

        def interrupted(*args):
            calls.append(True)
            if len(calls) == 2:
                raise OSError("sensitive-private-provider-failure")
            return original(*args)

        path = self.fixture["root"] / "interrupted.json"
        write_json(path, self.request)
        with (
            patch.object(module, "query_local", interrupted),
            redirect_stdout(io.StringIO()) as stdout,
            redirect_stderr(io.StringIO()) as stderr,
        ):
            status = main(
                [
                    "research",
                    "--input",
                    str(path),
                    "--local-config",
                    str(self.fixture["configuration"]),
                    "--scope",
                    str(self.fixture["session_path"]),
                    "--diagnostic-format",
                    "json",
                ]
            )
        self.assertEqual(len(calls), 2)
        self.assertEqual(status, 3)
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn("sensitive-private", stderr.getvalue())

    def test_session_serialized_ceiling_applies_to_new_result(self):
        session = json.loads(self.fixture["session_path"].read_bytes())
        session["budgets"]["max_output_bytes"] = 400
        write_json(self.fixture["session_path"], session)
        context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        with self.assertRaisesRegex(ContractError, "QUERY_BUDGET"):
            research(context, self.request)
