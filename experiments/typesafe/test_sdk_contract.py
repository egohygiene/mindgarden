"""Real official-SDK parsing/transport tests; no credentials or model accuracy."""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import httpx2
from mindgarden.adapters.typesafe_decisions import TypeSafeWorkflowJudge
from mindgarden.application.semantic_workflow import suggest_read_workflow
from mindgarden.domain.semantic_decision import DecisionSettings


class SDKContractTests(unittest.TestCase):
    def setUp(self):
        self.settings = DecisionSettings(enabled=True)

    def payload(self):
        return {
            "model": "synthetic-wire-model",
            "answers": {
                "workflow": {
                    "type": "choice",
                    "choice": "search",
                    "probabilities": {"search": 0.96, "graph": 0.02, "backlinks": 0.02},
                    "confidence": 0.94,
                },
                "fits_supported": {"type": "noul", "noul": 0.98},
            },
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }

    def test_real_sdk_serializes_typed_questions_and_preserves_documented_fields(self):
        requests = []

        def handle(request):
            requests.append(request)
            return httpx2.Response(200, json=self.payload())

        judge = TypeSafeWorkflowJudge(
            self.settings,
            api_key="synthetic-not-a-secret",
            transport=httpx2.MockTransport(handle),
        )
        result = suggest_read_workflow(
            "Find reviewed synthetic procedures",
            settings=self.settings,
            judge=judge,
            allow_hosted=True,
        )
        self.assertEqual(result.outcome, "selected")
        self.assertEqual(result.route, "search")
        self.assertEqual(result.resolved_model, "synthetic-wire-model")
        self.assertEqual(result.choice_confidence, 0.94)
        self.assertEqual(result.supported_probability, 0.98)
        body = json.loads(requests[0].content)
        self.assertEqual(body["model"], "jev-latest")
        self.assertEqual(body["questions"]["workflow"]["type"], "choice")
        self.assertEqual(
            set(body["questions"]["workflow"]["criteria"]),
            {"search", "graph", "backlinks"},
        )
        self.assertEqual(body["questions"]["fits_supported"]["type"], "noul")
        self.assertNotIn("synthetic-not-a-secret", json.dumps(body))
        self.assertEqual(requests[0].url.host, "api.typesafe.ai")

    def test_real_sdk_retries_are_bounded_and_do_not_leak_error_payload(self):
        calls = []

        def fail(request):
            calls.append(True)
            return httpx2.Response(
                503, json={"error": {"message": "provider-secret-error-canary"}}
            )

        judge = TypeSafeWorkflowJudge(
            self.settings,
            api_key="synthetic-not-a-secret",
            transport=httpx2.MockTransport(fail),
        )
        result = suggest_read_workflow(
            "Find notes", settings=self.settings, judge=judge, allow_hosted=True
        )
        self.assertEqual(result.outcome, "unavailable")
        self.assertEqual(len(calls), 1)
        self.assertNotIn("provider-secret-error-canary", json.dumps(result.as_dict()))
        settings = DecisionSettings(enabled=True, max_retries=1)
        judge = TypeSafeWorkflowJudge(
            settings,
            api_key="synthetic-not-a-secret",
            transport=httpx2.MockTransport(fail),
        )
        suggest_read_workflow(
            "Find notes", settings=settings, judge=judge, allow_hosted=True
        )
        self.assertEqual(len(calls), 3)

    def test_missing_wrong_or_unsupported_answers_do_not_select_a_handler(self):
        for mutate in (
            lambda p: p["answers"].pop("fits_supported"),
            lambda p: p["answers"]["workflow"].update(choice="execute-code"),
        ):
            value = self.payload()
            mutate(value)
            judge = TypeSafeWorkflowJudge(
                self.settings,
                api_key="synthetic-not-a-secret",
                transport=httpx2.MockTransport(
                    lambda request: httpx2.Response(200, json=value)
                ),
            )
            result = suggest_read_workflow(
                "Find notes", settings=self.settings, judge=judge, allow_hosted=True
            )
            self.assertEqual(result.outcome, "unavailable")
            self.assertIsNone(result.route)


if __name__ == "__main__":
    unittest.main()
