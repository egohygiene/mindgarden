"""Bounded source-only extraction, explicit review and interrupted-batch recovery."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.extraction_producer import RecordedExtractionProducer
from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.extraction import produce_batch
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index, graph_payload, search_payload
from mindgarden.domain.contracts import ContractRegistry, canonical_json
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.extraction_fixture import initialize
from tests.support_v1 import TIME, write_json, write_session
from tests import test_source_adapters as fixtures


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        fixtures.SourceAdapterTests.setUp(self)
        self.context, self.request, self.producer, self.responses = initialize(self)
        self.before = garden_fingerprint(self.workspace)
        self.originals = self.vault.export_bundle()

    def produce(self, **kwargs):
        return produce_batch(self.context, self.request, self.producer, **kwargs)

    def test_proposals_preserve_ambiguity_polarity_speaker_and_conflict_without_review(
        self,
    ):
        with (
            patch("socket.socket", side_effect=AssertionError("Network")),
            patch("subprocess.run", side_effect=AssertionError("Source executed")),
        ):
            batch = self.produce()
        self.assertEqual(batch["status"], "partial")
        self.assertIn("success-empty", [r["status"] for r in batch["records"]])
        proposal = batch["proposal"]
        self.assertIsNone(proposal["review_authority"])
        self.assertEqual(ContractRegistry().errors(proposal, "curation-plan"), [])
        outputs = [c["output"] for c in proposal["candidates"]]
        self.assertTrue(
            all(
                o["review"]["state"] == "unreviewed" and o["status"] == "proposed"
                for o in outputs
            )
        )
        self.assertFalse(any(o["title"] == "Alex" for o in outputs))
        self.assertFalse(
            any(e["type"] == "guarantees" for o in outputs for e in o["synapses"])
        )
        assistant = next(
            o
            for o in outputs
            if o["title"] == "Exact evidence may support explicit uncertainty."
        )
        self.assertEqual(assistant["attribution"], "assistant-suggestion")
        negative = next(
            o
            for o in outputs
            if o["title"] == "Daily review does not improve accuracy."
        )
        self.assertIn("negative", negative["body"])
        self.assertTrue(negative["contradictions"])
        self.assertIn("No independent verification.", negative["uncertainty"])
        self.assertEqual(self.before, garden_fingerprint(self.workspace))
        self.assertEqual(self.originals, self.vault.export_bundle())

    def test_interruption_resumes_completed_units_without_provider_replay(self):
        saved = []

        def interrupt(checkpoint):
            saved.append(deepcopy(checkpoint))
            if len(saved) == 2:
                raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            self.produce(on_checkpoint=interrupt)
        self.assertEqual(len(self.producer.calls), 2)
        resumed = self.produce(previous=saved[-1])
        self.assertEqual(len(self.producer.calls), len(self.request["sources"]))
        self.assertEqual(resumed["new_calls"], len(self.request["sources"]) - 2)
        no_replay = self.produce(previous=resumed)
        self.assertEqual(no_replay["new_calls"], 0)
        self.assertEqual(no_replay["proposal"], resumed["proposal"])
        self.assertEqual(no_replay["plan_sha256"], resumed["plan_sha256"])

    def test_empty_failed_partial_unsupported_and_invalid_results_stay_distinct(self):
        request = deepcopy(self.request)
        request["sources"] = request["sources"][:1]

        class Producer:
            execution = "offline"
            descriptor = request["producer"]

            def extract(self, evidence):
                if isinstance(self.output, Exception):
                    raise self.output
                return deepcopy(self.output)

        provider = Producer()
        for output, expected in [
            (
                {
                    "schema": "mindgarden.extraction-output/v1",
                    **self.responses["inert"],
                },
                "success-empty",
            ),
            (
                {
                    "schema": "mindgarden.extraction-output/v1",
                    "status": "unsupported",
                    "diagnostics": ["unsupported-format"],
                    "entities": [],
                    "assertions": [],
                },
                "unsupported",
            ),
            (RuntimeError("PRIVATE_CANARY"), "failed"),
            ({"broken": "PRIVATE_CANARY"}, "invalid"),
        ]:
            provider.output = output
            result = produce_batch(self.context, request, provider)
            self.assertEqual(result["records"][0]["status"], expected)
            self.assertIsNone(result["proposal"])
            self.assertNotIn("PRIVATE_CANARY", json.dumps(result))
        provider.output = {
            "schema": "mindgarden.extraction-output/v1",
            **self.responses["assistant"],
        }
        provider.output["entities"][0]["quote"] = "unobserved quote"
        self.assertEqual(
            produce_batch(self.context, request, provider)["records"][0]["status"],
            "invalid",
        )

    def test_changed_config_revocation_and_ungranted_evidence_reject_before_calls(self):
        batch = self.produce(max_new_units=1)
        request = deepcopy(self.request)
        request["limits"]["max_input_bytes"] = 1
        with self.assertRaisesRegex(ContractError, "EXTRACTION_BUDGET"):
            produce_batch(self.context, request, self.producer)
        request = deepcopy(self.request)
        request["producer"]["prompt_revision"] = "0" * 64
        provider = RecordedExtractionProducer(request["producer"], {})
        with self.assertRaisesRegex(ContractError, "EXTRACTION_RESUME"):
            produce_batch(self.context, request, provider, previous=batch)
        request = deepcopy(self.request)
        request["sources"][0]["source"]["revision"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ContractError, "SOURCE_GRANT"):
            produce_batch(self.context, request, self.producer)
        config = json.loads(self.configuration.read_text())
        config["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.configuration, config)
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            self.produce(previous=batch)

    def test_explicit_review_produces_exact_source_search_and_typed_graph_without_original_changes(
        self,
    ):
        batch = self.produce()
        proposal = deepcopy(batch["proposal"])
        review = {
            "state": "approved",
            "reviewers": ["synthetic-reviewer"],
            "reviewed_at": TIME,
            "rationale": "Authored synthetic human approval of source-grounded proposals, not a truth claim.",
        }
        proposal["review_authority"] = {"kind": "human", "id": "synthetic-reviewer"}
        for candidate in proposal["candidates"]:
            output = candidate["output"]
            output.update(review=review, status="active")
            for item in output["claims"] + output["synapses"]:
                item["review"] = review
        path = self.root / "reviewed.json"
        write_json(path, proposal)
        plan = build_curation_plan(self.bindings, path)
        apply_curation(plan, plan.digest, self.bindings)
        self.assertFalse(apply_curation(plan, plan.digest, self.bindings))
        session = self.root / "reviewed-session.json"
        write_session(session, self.configuration)
        context = QueryContext.load(self.configuration, session)
        results = search_payload(context, "Daily review")
        self.assertTrue(results["results"])
        source_set = {canonical_json(e) for e in self.request["sources"]}
        self.assertTrue(
            all(
                canonical_json(e) in source_set
                for r in results["results"]
                for e in r["sources"]
            )
        )
        self.assertTrue(graph_payload(context)["edges"])
        self.assertEqual(
            build_index(context),
            build_index(QueryContext.load(self.configuration, session)),
        )
        self.assertEqual(self.originals, self.vault.export_bundle())

    def test_cli_recorded_producer_creates_private_non_overwriting_resume_bundle(self):
        batch = self.produce()
        recording = {
            "producer": self.request["producer"],
            "outputs": {
                item["input_sha256"]: {
                    "schema": "mindgarden.extraction-output/v1",
                    **self.responses[
                        "assistant"
                        if item["origin"]["speaker"] == "assistant"
                        else "page"
                        if "Report A:" in item["text"]
                        else "inert"
                        if "inert-bookmarklet" in item["text"]
                        else "bookmark"
                    ],
                }
                for item in self.producer.calls
            },
        }
        path = self.root / "request.json"
        write_json(path, self.request)
        recorded = self.root / "recorded.json"
        write_json(recorded, recording)
        output = self.root / "private-proposals"
        arguments = [
            "extraction",
            "--local-config",
            str(self.configuration),
            "--scope",
            str(self.context.session_path),
            "--input",
            str(path),
            "--recorded-output",
            str(recorded),
            "--output-directory",
            str(output),
        ]

        def run(args):
            with redirect_stdout(io.StringIO()) as capture:
                self.assertEqual(main(args), 0)
            return json.loads(capture.getvalue())

        preview = run(arguments)
        self.assertEqual(preview["batch"]["proposal"], batch["proposal"])
        run([*arguments, "--apply", "--plan-digest", preview["plan_sha256"]])
        self.assertEqual((output / "curation.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.before, garden_fingerprint(self.workspace))
        run([*arguments, "--apply", "--plan-digest", preview["plan_sha256"]])
