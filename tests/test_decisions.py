"""Public ADR projection denies unknown/private evidence before generated metadata."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from mindgarden.application.decisions import project_decisions
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.validation import ContractError


class DecisionProjectionTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads(
            (Path(__file__).parent / "fixtures/decisions/snapshot.json").read_text()
        )
        self.commit = self.snapshot["represented_commit"]

    def project(self, **options):
        return project_decisions(
            self.snapshot, represented_commit=self.commit, **options
        )

    def test_rebuild_is_deterministic_with_exact_canonical_source_and_no_body_copy(
        self,
    ):
        result = self.project()
        self.assertEqual(canonical_json(result), canonical_json(self.project()))
        self.assertEqual(len(result["context"]), 1)
        self.assertIn(self.commit, result["nodes"][0]["source"])
        self.assertEqual(result["nodes"][0]["narrative"], "canonical-source-required")
        self.assertEqual(result["nodes"][0]["implementation_status"], "verified")

    def test_denied_titles_ids_counts_links_and_context_are_absent(self):
        original = self.project()
        private = deepcopy(self.snapshot["graph"]["entities"][0])
        private.update(
            kind="architecture_decision",
            visibility="private",
            id="denied-canary",
            title="secret-canary",
        )
        self.snapshot["graph"]["entities"].append(private)
        self.snapshot["graph"]["relationships"].append(
            {
                "source": "denied-canary",
                "target": original["nodes"][0]["id"],
                "type": "related_to",
            }
        )
        result = self.project()
        self.assertEqual(original, result)
        self.assertNotIn(b"canary", canonical_json(result))

    def test_proposed_and_terminal_history_do_not_become_accepted_context(self):
        item = next(
            e
            for e in self.snapshot["graph"]["entities"]
            if e["kind"] == "architecture_decision"
        )
        item["state"]["value"] = "proposed"
        item["attributes"]["approval"] = None
        self.assertEqual(self.project()["context"], [])
        self.assertEqual(
            self.project(include_proposed=True)["context"][0]["status"], "proposed"
        )
        item["state"]["value"] = "superseded"
        self.assertEqual(self.project()["nodes"], [])  # absent human disposition
        item["attributes"]["approval"] = {
            "by": "synthetic-reviewer",
            "date": "2026-08-25",
            "evidence": "https://example.test/review/2",
        }
        self.assertEqual(self.project()["nodes"][0]["status"], "superseded")
        self.assertEqual(self.project()["context"], [])

    def test_private_stale_unavailable_invalid_and_tiny_budget_fail_closed(self):
        with self.assertRaisesRegex(ContractError, "DECISIONS_BUDGET"):
            self.project(max_bytes=1)
        for mutate in (
            lambda x: x.update(visibility="private"),
            lambda x: x.update(represented_commit="b" * 40),
            lambda x: x.pop("graph"),
        ):
            saved = deepcopy(self.snapshot)
            mutate(self.snapshot)
            with self.assertRaisesRegex(ContractError, "DECISIONS_INPUT"):
                self.project()
            self.snapshot = saved
        self.snapshot["graph"]["sources"][0]["visibility"] = "private"
        self.assertEqual(self.project()["nodes"], [])

    def test_lineage_and_inference_are_preserved_only_between_authorized_nodes(self):
        first = next(
            e
            for e in self.snapshot["graph"]["entities"]
            if e["kind"] == "architecture_decision"
        )
        second = deepcopy(first)
        second.update(id="second-decision", key="ADR-0008")
        self.snapshot["graph"]["entities"].append(second)
        self.snapshot["graph"]["relationships"].append(
            {
                "source": second["id"],
                "target": first["id"],
                "type": "depends_on",
                "assertion": "inferred",
                "freshness": "current",
                "provenance": first["provenance"],
            }
        )
        result = self.project()
        self.assertEqual(result["edges"][0]["assertion"], "inferred")
        self.assertEqual(result["backlinks"][first["id"]][0]["type"], "depends-on")

    def test_cli_requires_exact_input_digest(self):
        from contextlib import redirect_stdout, redirect_stderr
        import io
        from mindgarden.domain.contracts import digest_bytes
        from mindgarden.interfaces.cli import main

        path = Path(__file__).parent / "fixtures/decisions/snapshot.json"
        args = [
            "decisions",
            "--input",
            str(path),
            "--input-sha256",
            digest_bytes(path.read_bytes()),
            "--represented-commit",
            self.commit,
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(args), 0)
        self.assertEqual(json.loads(output.getvalue()), self.project())
        args[4] = "0" * 64
        with redirect_stderr(io.StringIO()) as diagnostic:
            self.assertEqual(main(args), 3)
        self.assertIn("DECISIONS_STALE", diagnostic.getvalue())
