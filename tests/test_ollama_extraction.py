"""Offline wire checks are separate from any measured model accuracy."""

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from mindgarden.adapters.ollama_extraction import (
    chat_request,
    output_schema,
    parse_reply,
)
from mindgarden.domain.validation import ContractError


class OllamaExtractionTests(unittest.TestCase):
    def test_schema_is_self_contained_and_request_is_bounded_without_calls(self):
        with patch("socket.socket", side_effect=AssertionError("Network")):
            payload = chat_request(
                {"text": "Synthetic input"}, {"model": "explicit-test-model"}
            )
        self.assertEqual(payload["model"], "explicit-test-model")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"]["temperature"], 0)
        self.assertNotIn("$ref", json.dumps(output_schema()))
        self.assertNotIn("tools", payload)

    def test_complete_typed_output_required_and_actual_model_preserved(self):
        empty = {
            "schema": "mindgarden.extraction-output/v1",
            "status": "success",
            "entities": [],
            "assertions": [],
            "diagnostics": [],
        }
        reply = {
            "model": "observed-model",
            "done": True,
            "message": {"role": "assistant", "content": json.dumps(empty)},
        }
        result = parse_reply(reply)
        self.assertEqual(result["model_used"], "observed-model")
        self.assertEqual(result["output"], empty)
        for bad in (
            {**reply, "done": False},
            {**reply, "message": {"role": "assistant", "content": "{}"}},
            {},
        ):
            with self.assertRaises(ContractError):
                parse_reply(bad)
