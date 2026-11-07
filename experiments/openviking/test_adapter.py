"""Producer boundary tests; these never emulate a successful native service."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from experiments.corpus import create_corpus
from experiments.openviking.adapter import prepare_handoff, resolve_bound_leaf
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.validation import ContractError
from tests.support_v1 import write_json


class OpenVikingProducerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.corpus = create_corpus(self.root / "corpus", 2)
        self.context = self.corpus["context"]
        self.references = [
            r["reference"]
            for r in self.corpus["index"]["records"]
            if r["id"] in {"reviewed-prompt", "reviewed-claim"}
        ]

    def test_exact_selected_provenance_and_untrusted_leaf_binding(self):
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            plan, files = prepare_handoff(self.context, self.references)
            self.assertEqual(
                (plan, files),
                prepare_handoff(self.context, list(reversed(self.references))),
            )
            self.assertEqual(len(plan["entries"]), 4)
            for entry in plan["entries"]:
                result = resolve_bound_leaf(
                    self.context, plan, entry["proposed_uri"], files[entry["filename"]]
                )
                self.assertEqual(result["reference"], entry["reference"])
                self.assertTrue(result["sources"][0]["content_sha256"])
        self.assertFalse(plan["live_ingestion_verified"])
        self.assertFalse(plan["session_memory"])
        self.assertNotIn(str(self.root), canonical_json(plan).decode())
        with self.assertRaisesRegex(ContractError, "OPENVIKING_UNBOUND"):
            resolve_bound_leaf(
                self.context,
                plan,
                plan["entries"][0]["proposed_uri"],
                b"provider rewrite with invented claim",
            )
        with self.assertRaisesRegex(ContractError, "OPENVIKING_UNBOUND"):
            resolve_bound_leaf(
                self.context,
                plan,
                "viking://resources/unbound/.abstract.md",
                b"compressed summary",
            )

    def test_denied_scope_unknown_mapping_memory_and_budget_fail_closed(self):
        with self.assertRaises(ContractError):
            prepare_handoff(self.corpus["personal_context"], self.references)
        with self.assertRaisesRegex(ContractError, "OPENVIKING_MEMORY_UNAVAILABLE"):
            prepare_handoff(self.context, self.references, session_memory=True)
        with self.assertRaisesRegex(ContractError, "OPENVIKING_BUDGET"):
            prepare_handoff(self.context, self.references, max_bytes=512)
        refs = deepcopy(self.references)
        refs[0]["id"] = "denied-financial-canary"
        with self.assertRaises(ContractError) as error:
            prepare_handoff(self.context, refs)
        self.assertNotIn("denied-financial-canary", str(error.exception))
        plan, files = prepare_handoff(self.context, self.references)
        plan["entries"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "OPENVIKING_STALE"):
            resolve_bound_leaf(
                self.context,
                plan,
                plan["entries"][0]["proposed_uri"],
                files[plan["entries"][0]["filename"]],
            )

    def test_producer_export_restore_relocation_rebuild_and_removal(self):
        plan, files = prepare_handoff(self.context, self.references)
        original = {
            p: p.read_bytes()
            for fixture in self.corpus["gardens"]
            for p in fixture["workspace"].rglob("*")
            if p.is_file()
        }
        export = self.root / "owned-export"
        export.mkdir()
        for name, body in files.items():
            (export / name).write_bytes(body)
        restored = self.root / "owned-restored"
        shutil.copytree(export, restored)
        self.assertEqual({p.name: p.read_bytes() for p in restored.iterdir()}, files)
        document = json.loads(self.corpus["configuration"].read_text())
        for binding in document["gardens"]:
            if binding["id"].startswith("public-"):
                destination = self.root / ("relocated-" + binding["id"])
                shutil.copytree(binding["root"], destination)
                binding["root"] = str(destination)
        relocated = self.root / "relocated-bindings.json"
        write_json(relocated, document)
        context = QueryContext.load(relocated, self.corpus["session"])
        self.assertEqual((plan, files), prepare_handoff(context, self.references))
        shutil.rmtree(export)
        shutil.rmtree(restored)
        self.assertEqual(original, {p: p.read_bytes() for p in original})
        self.assertEqual(build_index(context), self.corpus["index"])

    def test_committed_producer_golden(self):
        plan, files = prepare_handoff(self.context, self.references)
        proof = {
            "schema": "mindgarden.openviking-producer-proof/v1",
            "selected_records": len(plan["entries"]),
            "files": {n: digest_bytes(b) for n, b in files.items()},
            "total_bytes": sum(map(len, files.values())),
            "scope": "public",
            "native_ingestion_verified": False,
            "session_memory": False,
        }
        expected = json.loads(
            (Path(__file__).with_name("expected-producer.json")).read_text()
        )
        self.assertEqual(proof, expected)


if __name__ == "__main__":
    unittest.main()
