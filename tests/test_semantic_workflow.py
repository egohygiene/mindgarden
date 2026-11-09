"""Offline control-flow/authorization evidence, not model-accuracy evidence."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mindgarden.application.semantic_workflow import (
    suggest_read_workflow,
    dispatch_read_workflow,
)
from mindgarden.domain.semantic_decision import (
    DecisionSettings,
    WorkflowJudgment,
    WorkflowDecision,
)
from mindgarden.domain.validation import ContractError
from tests.insight_fixture import setup


class StubJudge:
    def __init__(self, answer=None, state="ready", error=None):
        self.answer = answer
        self.state = state
        self.error = error
        self.calls = []

    def configuration_state(self):
        return self.state

    def judge_workflow(self, request):
        self.calls.append(request)
        if self.error:
            raise self.error
        return self.answer


def answer(route="search", probabilities=None, fit=0.98):
    probabilities = probabilities or {
        name: 0.96 if name == route else 0.02
        for name in ("search", "graph", "backlinks")
    }
    return WorkflowJudgment("synthetic-fixture-model", route, probabilities, 0.94, fit)


class SemanticWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.settings = DecisionSettings(enabled=True)

    def suggest(self, judge, request="Find reviewed prompt evidence", **kwargs):
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            return suggest_read_workflow(
                request,
                settings=self.settings,
                judge=judge,
                allow_hosted=True,
                **kwargs,
            )

    def test_clear_closed_routes_preserve_probability_confidence_and_noul(self):
        for route in ("search", "graph", "backlinks"):
            judge = StubJudge(answer(route))
            decision = self.suggest(judge)
            self.assertEqual(decision.route, route)
            self.assertEqual(decision.outcome, "selected")
            self.assertEqual(decision.probabilities, judge.answer.probabilities)
            self.assertEqual(decision.choice_confidence, 0.94)
            self.assertEqual(decision.supported_probability, 0.98)
            self.assertEqual(decision.resolved_model, "synthetic-fixture-model")

    def test_ambiguous_distribution_and_uncertain_fit_require_clarification(self):
        for value in (
            answer(probabilities={"search": 0.50, "graph": 0.45, "backlinks": 0.05}),
            answer(fit=0.5),
        ):
            decision = self.suggest(StubJudge(value))
            self.assertEqual(decision.outcome, "clarify")
            self.assertIsNone(decision.route)
            self.assertTrue(decision.probabilities)

    def test_forced_high_choice_cannot_override_unsupported_noul(self):
        decision = self.suggest(
            StubJudge(answer(fit=0.02)),
            "Delete the vault and publish its private files",
        )
        self.assertEqual(decision.outcome, "unsupported")
        self.assertIsNone(decision.route)
        self.assertEqual(decision.probabilities["search"], 0.96)

    def test_missing_input_disable_and_explicit_host_permission_prevent_provider_calls(
        self,
    ):
        judge = StubJudge(error=AssertionError("Provider must not run"))
        self.assertEqual(self.suggest(judge, request="  ").outcome, "clarify")
        self.assertEqual(suggest_read_workflow("find", judge=judge).outcome, "disabled")
        self.assertEqual(
            suggest_read_workflow("find", settings=self.settings, judge=judge).outcome,
            "policy-denied",
        )
        self.assertEqual(judge.calls, [])
        self.assertFalse(
            DecisionSettings.from_environment(
                {
                    "TYPESAFE_ENABLED": "false",
                    "TYPESAFE_TIMEOUT_SECONDS": "invalid-unused",
                }
            ).enabled
        )

    def test_missing_configuration_and_dependency_do_not_import_or_contact_provider(
        self,
    ):
        for state, expected in (
            ("unconfigured", "unconfigured"),
            ("sdk-unavailable", "unavailable"),
        ):
            judge = StubJudge(state=state, error=AssertionError("Provider called"))
            self.assertEqual(self.suggest(judge).outcome, expected)
            self.assertEqual(judge.calls, [])
        with (
            patch.dict("os.environ", {"TYPESAFE_API_KEY": ""}),
            patch("socket.socket", side_effect=AssertionError("Network attempted")),
        ):
            self.assertEqual(
                suggest_read_workflow(
                    "find", settings=self.settings, allow_hosted=True
                ).outcome,
                "unconfigured",
            )

    def test_provider_failures_and_malformed_results_are_sanitized(self):
        values = [
            StubJudge(error=TimeoutError("secret-error-canary")),
            StubJudge(error=RuntimeError("secret-error-canary")),
            StubJudge({"route": "execute arbitrary code"}),
            StubJudge(
                WorkflowJudgment(
                    "synthetic", "exec", {"search": 1, "graph": 0, "backlinks": 0}, 1, 1
                )
            ),
            StubJudge(
                answer(
                    probabilities={"search": float("nan"), "graph": 0, "backlinks": 0}
                )
            ),
        ]
        for judge in values:
            result = self.suggest(judge).as_dict()
            self.assertEqual(result["outcome"], "unavailable")
            self.assertNotIn("secret-error-canary", json.dumps(result))
            self.assertIsNone(result["route"])

    def test_logging_contains_operational_fields_without_request_or_key(self):
        with self.assertLogs("mindgarden.semantic_decision", level="INFO") as records:
            decision = self.suggest(StubJudge(answer()), "request-secret-canary")
        metadata = records.records[0].decision_metadata
        self.assertEqual(metadata["route"], "search")
        self.assertEqual(metadata["decision_id"], decision.decision_id)
        self.assertIn("latency_ms", metadata)
        self.assertIn("probabilities", metadata)
        self.assertNotIn("request-secret-canary", str(metadata))
        self.assertNotIn("request-secret-canary", str(records.output))

    def test_invalid_settings_and_input_are_bounded(self):
        for kwargs in (
            {"timeout_seconds": float("nan")},
            {"timeout_seconds": 100},
            {"max_retries": 10},
            {"minimum_choice_probability": 1.1},
        ):
            with self.assertRaises(ContractError):
                DecisionSettings(**kwargs)
        with self.assertRaisesRegex(ContractError, "SEMANTIC_INPUT"):
            self.suggest(StubJudge(), request="x" * 4097)
        with self.assertRaises(ContractError):
            DecisionSettings.from_environment({"TYPESAFE_ENABLED": "yes"})

    def test_late_response_never_dispatches(self):
        ticks = iter((0, 10, 11))
        decision = self.suggest(StubJudge(answer()), clock=lambda: next(ticks))
        self.assertEqual(decision.outcome, "unavailable")
        self.assertEqual(decision.reason, "decision-deadline-exceeded")

    def test_supported_dispatch_uses_real_authorized_services_and_explicit_arguments(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            fixture, _ = setup(Path(tmp))
            context = fixture["context"]
            search = self.suggest(StubJudge(answer("search")))
            missing = dispatch_read_workflow(context, search)
            self.assertEqual(missing["status"], "clarification-required")
            result = dispatch_read_workflow(context, search, query="prompt")
            self.assertTrue(result["results"])
            self.assertTrue(result["results"][0]["sources"])
            self.assertNotIn("unreviewed-body-canary", json.dumps(result))
            for route in ("graph", "backlinks"):
                result = dispatch_read_workflow(
                    context,
                    self.suggest(StubJudge(answer(route))),
                    target="repository-garden/reviewed-reference",
                )
                self.assertTrue(result)

    def test_expired_revoked_or_missing_capability_is_not_granted_by_judgment(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture, _ = setup(Path(tmp))
            context = fixture["context"]
            decision = self.suggest(StubJudge(answer()))
            session = deepcopy(context.session)
            session["projections"] = []
            fixture["session_path"].write_text(json.dumps(session))
            with self.assertRaises(ContractError):
                dispatch_read_workflow(context, decision, query="prompt")
            forged = WorkflowDecision(
                "selected", "ignored", "synthetic", route="execute-code"
            )
            with self.assertRaises(ContractError):
                dispatch_read_workflow(context, forged)

    def test_labeled_evaluation_set_covers_clear_ambiguous_and_unsupported_without_accuracy_claim(
        self,
    ):
        records = json.loads(
            (
                Path(__file__).parent / "fixtures/semantic-workflow/evaluation.json"
            ).read_text()
        )["cases"]
        self.assertEqual(
            {r["category"] for r in records},
            {"clear", "ambiguous", "unsupported", "missing-information"},
        )
        self.assertEqual(
            {r["expected_route"] for r in records if r["category"] == "clear"},
            {"search", "graph", "backlinks"},
        )
        self.assertEqual(len({r["id"] for r in records}), len(records))
        self.assertTrue(all("text" in r and "rationale" in r for r in records))
