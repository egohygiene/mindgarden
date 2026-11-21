"""Replay recorded synthetic Ollama output without a live model."""

from io import BytesIO
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from .evaluate import evaluate
from mindgarden.domain.contracts import canonical_json, digest_bytes


class EvaluationTests(unittest.TestCase):
    def test_observed_schema_valid_reply_is_reported_as_rejected_and_opt_in_for_output(self):
        receipt = json.loads((Path(__file__).resolve().parents[2] / "tests/fixtures/extraction/observed-ollama.json").read_text())
        observed = receipt["observation"]
        output = observed["output"]
        reply = {
            "model": observed["model_used"],
            "done": True,
            "message": {"role": "assistant", "content": json.dumps(output)},
        }
        with patch("experiments.ollama_extraction.evaluate.build_opener") as opener:
            opener.return_value.open.side_effect = lambda *_args, **_kwargs: BytesIO(canonical_json(reply))
            default_report = evaluate(observed["model_requested"], "http://127.0.0.1:11434", True)
            explicit_report = evaluate(
                observed["model_requested"], "http://127.0.0.1:11434", True, include_output=True,
            )
        self.assertEqual(default_report, {key: value for key, value in observed.items() if key != "output"})
        self.assertEqual(explicit_report, observed)
        self.assertEqual(explicit_report["output_sha256"], digest_bytes(canonical_json(output)))
        self.assertEqual(explicit_report["structure"], "passed")
        self.assertEqual(explicit_report["proposal_validation"], "rejected")
