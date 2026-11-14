"""Public decision/artifact composition preserves pins and withholds denied data."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.decisions import project_decisions
from mindgarden.domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main

FIXTURES = Path(__file__).parent / "fixtures/decisions"


class DecisionRelationshipTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = read_object(FIXTURES / "relationships-snapshot.json")
        self.commit = self.snapshot["represented_commit"]

    def project(self, **options):
        return project_decisions(
            self.snapshot,
            represented_commit=self.commit,
            include_related=True,
            **options,
        )

    def test_shared_input_projects_deterministically_with_typed_provenance_and_no_body_copy(
        self,
    ):
        expected = read_object(FIXTURES / "expected-relationships.json")
        with (
            patch("socket.socket", side_effect=AssertionError("Network attempted")),
            patch(
                "subprocess.Popen",
                side_effect=AssertionError("Source instructions executed"),
            ),
        ):
            self.assertEqual(self.project(), expected)
            for key in ("entities", "sources", "relationships"):
                self.snapshot["graph"][key].reverse()
            self.assertEqual(self.project(), expected)
        self.assertEqual(ContractRegistry().errors(expected, "adr-projection"), [])
        self.assertEqual(len(expected["nodes"]), 3)
        self.assertEqual(len(expected["artifacts"]), 6)
        self.assertEqual(len(expected["edges"]), 8)
        self.assertTrue(
            all(
                node["narrative"] == "canonical-source-required"
                for node in expected["nodes"]
            )
        )
        self.assertNotIn(b'"body"', canonical_json(expected))
        self.assertTrue(all(edge["provenance"] for edge in expected["edges"]))

    def test_cross_repository_and_terminal_history_keep_distinct_owner_revisions(self):
        result = self.project()
        inherited = next(
            node for node in result["nodes"] if node["decision_scope"] == "organization"
        )
        self.assertEqual(inherited["repository"], "egohygiene/hygiene")
        self.assertEqual(inherited["represented_commit"], "c" * 40)
        self.assertIn("/blob/" + "c" * 40 + "/", inherited["source"])
        self.assertEqual(inherited["authority_scope"], "organization-scope-reference")
        self.assertEqual(result["represented_commit"], self.commit)
        old = next(node for node in result["nodes"] if node["status"] == "superseded")
        self.assertTrue(result["backlinks"][old["id"]])
        self.assertNotIn(
            old["source"], [item["reference"] for item in result["context"]]
        )
        self.assertEqual(inherited["review"], "upstream-human-disposition")
        self.assertEqual(result["authority"], "upstream-assertions-only")

    def test_provider_observation_and_immutable_commit_pin_are_not_conflated(self):
        result = self.project()
        issue = next(item for item in result["artifacts"] if item["kind"] == "issue")
        commit = next(item for item in result["artifacts"] if item["kind"] == "commit")
        self.assertIsNone(issue["provenance"][0]["revision"])
        self.assertEqual(issue["observed_in_commit"], self.commit)
        self.assertEqual(commit["provenance"][0]["revision"], "b" * 40)
        self.assertEqual(commit["provenance"][0]["freshness"], "not_applicable")
        self.assertIn("/commit/" + "b" * 40, commit["source"])
        inferred = next(
            item for item in result["context"] if item.get("assertion") == "inferred"
        )
        self.assertTrue(inferred["untrusted"])
        self.assertEqual(inferred["reason"], "related-to-selected-decision")
        self.assertEqual(inferred["relationship"], "tracks")
        self.assertTrue(inferred["decision"])

    def test_denied_and_unavailable_artifacts_do_not_change_public_metadata_or_counts(
        self,
    ):
        baseline = self.project()
        original = deepcopy(self.snapshot)
        issue = next(
            item for item in original["graph"]["entities"] if item["kind"] == "issue"
        )
        source = next(
            item
            for item in original["graph"]["sources"]
            if item["id"] == issue["provenance"][0]
        )
        decision = baseline["nodes"][-1]["id"]
        for state in (
            {"visibility": "private"},
            {"visibility": "unknown"},
            {"freshness": "stale"},
            {"freshness": "unknown"},
            {"kind": "unsupported_claim"},
        ):
            self.snapshot = deepcopy(original)
            denied = {
                **issue,
                **state,
                "id": "DENIED-ARTIFACT-CANARY",
                "title": "DENIED-TITLE-CANARY",
                "provenance": ["source:denied"],
            }
            self.snapshot["graph"]["entities"].append(denied)
            self.snapshot["graph"]["sources"].append({**source, "id": "source:denied"})
            self.snapshot["graph"]["relationships"].append(
                {
                    "type": "tracks",
                    "source": decision,
                    "target": denied["id"],
                    "assertion": "authoritative",
                    "freshness": "current",
                    "direction": "directed",
                    "provenance": denied["provenance"],
                }
            )
            self.snapshot["coverage"]["private_count_canary"] = 8675309
            with self.subTest(state=state):
                self.assertEqual(self.project(), baseline)
                self.assertNotIn(b"CANARY", canonical_json(self.project()))

    def test_credential_urls_and_wrong_source_revisions_are_withheld(self):
        baseline = deepcopy(self.snapshot)
        for kind in ("issue", "commit"):
            self.snapshot = deepcopy(baseline)
            artifact = next(
                item
                for item in self.snapshot["graph"]["entities"]
                if item["kind"] == kind
            )
            source = next(
                item
                for item in self.snapshot["graph"]["sources"]
                if item["id"] == artifact["provenance"][0]
            )
            if kind == "issue":
                source["url"] += "?token=PRIVATE-CREDENTIAL-CANARY"
                artifact["canonical_url"] = source["url"]
            else:
                source["revision"] = "d" * 40
            result = self.project()
            self.assertNotIn(
                artifact["id"], [item["id"] for item in result["artifacts"]]
            )
            self.assertNotIn(b"CANARY", canonical_json(result))

    def test_proposal_selection_is_explicit_and_does_not_create_approval(self):
        for item in self.snapshot["graph"]["entities"]:
            if (
                item["kind"] == "architecture_decision"
                and item["state"]["value"] == "accepted"
            ):
                item["state"]["value"] = "proposed"
                item["attributes"]["approval"] = None
        self.assertEqual(self.project()["context"], [])
        selected = self.project(include_proposed=True)
        self.assertTrue(selected["context"])
        self.assertTrue(all(item["untrusted"] for item in selected["context"]))
        self.assertTrue(
            all(
                node["approval"] is None
                for node in selected["nodes"]
                if node["status"] == "proposed"
            )
        )

    def test_unknown_versions_duplicate_evidence_and_budget_overflow_fail_closed(self):
        original = deepcopy(self.snapshot)
        for version in (None, "1.0.0-future"):
            self.snapshot["contract_version"] = version
            with self.assertRaisesRegex(ContractError, "DECISIONS_INPUT"):
                self.project()
        self.snapshot = deepcopy(original)
        self.snapshot["graph"]["sources"].append(
            deepcopy(self.snapshot["graph"]["sources"][0])
        )
        with self.assertRaisesRegex(ContractError, "DECISIONS_INPUT"):
            self.project()
        self.snapshot = original
        with self.assertRaisesRegex(ContractError, "DECISIONS_BUDGET"):
            self.project(max_bytes=1)

    def test_related_cli_is_digest_bound_and_output_is_portable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.json"
            path.write_bytes(canonical_json(self.snapshot))
            args = [
                "decisions",
                "--input",
                str(path),
                "--input-sha256",
                digest_bytes(path.read_bytes()),
                "--represented-commit",
                self.commit,
                "--include-related",
            ]
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(args), 0)
            self.assertEqual(json.loads(output.getvalue()), self.project())
            self.assertNotIn(directory, output.getvalue())
            path.write_bytes(canonical_json({**self.snapshot, "changed": True}))
            with (
                redirect_stdout(io.StringIO()) as output,
                redirect_stderr(io.StringIO()) as error,
            ):
                self.assertEqual(main(args), 3)
                self.assertEqual(output.getvalue(), "")
                self.assertIn("DECISIONS_STALE", error.getvalue())
