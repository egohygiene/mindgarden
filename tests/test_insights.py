"""Synthetic review, privacy, lifecycle, provenance and immutable handoff cases."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from mindgarden.application.insights import plan_insights, candidate_revision
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.insight_fixture import setup
from tests.support_v1 import write_json


class InsightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.fixture, self.request = setup(self.root)
        self.context = self.fixture["context"]

    def canonical_bytes(self):
        return {
            str(p.relative_to(self.fixture["workspace"])): p.read_bytes()
            for p in self.fixture["workspace"].rglob("*")
            if p.is_file()
        }

    def test_single_exact_claim_provenance_rights_and_offline_determinism(self):
        before = self.canonical_bytes()
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            preview, files = plan_insights(self.context, self.request)
        self.assertEqual((preview, files), plan_insights(self.context, self.request))
        projection = preview["projection"]
        self.assertFalse(projection["canonical"])
        self.assertEqual(projection["scope"]["visibility"], "public")
        sources = projection["candidates"][0]["sources"]
        self.assertEqual(
            {s["reference"]["id"] for s in sources},
            {"reviewed-prompt", "reviewed-claim"},
        )
        self.assertTrue(
            all(s["evidence"][0]["locator"] == "lines:1-1" for s in sources)
        )
        self.assertIn(
            "source-uncertainty", projection["candidates"][0]["qualification_reasons"]
        )
        self.assertEqual(before, self.canonical_bytes())
        self.assertNotIn(str(self.root), canonical_json(projection).decode())

    def test_series_duplicate_aliases_and_input_order(self):
        first = self.request["candidates"][0]
        alias = {**deepcopy(first), "id": "z-duplicate"}
        second = {
            **deepcopy(first),
            "id": "second-insight",
            "objective": "A second teaching objective.",
        }
        self.request["candidates"] += [alias, second, deepcopy(first)]
        self.request["series"] = [
            {
                "id": "source-series",
                "title": "Source series",
                "candidates": ["second-insight", "evidence-insight"],
                "review": first["review"],
            }
        ]
        preview, files = plan_insights(self.context, self.request)
        self.assertEqual(len(preview["projection"]["candidates"]), 2)
        self.assertEqual(len(preview["projection"]["duplicates"]), 2)
        self.request["candidates"].reverse()
        self.assertEqual(files, plan_insights(self.context, self.request)[1])
        self.assertEqual(
            preview["projection"]["series"][0]["candidates"],
            ["second-insight", "evidence-insight"],
        )

    def test_rejection_supersession_and_failed_renderer_are_projection_only(self):
        before = self.canonical_bytes()
        old = deepcopy(self.request["candidates"][0])
        old["id"] = "old-insight"
        old["lifecycle"] = "superseded"
        rejected = deepcopy(old)
        rejected["id"] = "rejected-insight"
        rejected["lifecycle"] = "rejected"
        rejected["review"]["state"] = "rejected"
        self.request["candidates"][0]["supersedes"] = ["old-insight"]
        self.request["candidates"] += [old, rejected]
        self.request["artifact_events"] = [self.event("failed")]
        preview, _ = plan_insights(self.context, self.request)
        self.assertEqual(
            {e["reason"] for e in preview["excluded"]}, {"superseded", "rejected"}
        )
        self.assertEqual(
            preview["projection"]["candidates"][0]["artifact_events"][0]["state"],
            "failed",
        )
        self.assertEqual(before, self.canonical_bytes())

    def event(self, state):
        candidate = self.request["candidates"][0]
        return {
            "schema": "mindgarden.insight-artifact-event/v1",
            "id": "artifact-event",
            "candidate": candidate["id"],
            "candidate_revision": candidate_revision(candidate),
            "state": state,
            "review": deepcopy(candidate["review"]),
            "artifacts": []
            if state in {"failed", "rejected"}
            else [
                {
                    "uri": "https://synthetic.example.test/figure.png",
                    "sha256": "a" * 64,
                    "media_type": "image/png",
                    "role": "image",
                }
            ],
            "rationale": "Authored synthetic downstream feedback, not a verified remote fetch.",
        }

    def test_published_feedback_is_version_bound_and_noncanonical(self):
        before = self.canonical_bytes()
        self.request["candidates"][0]["lifecycle"] = "published"
        with self.assertRaisesRegex(ContractError, "INSIGHT_EVENT"):
            plan_insights(self.context, self.request)
        self.request["artifact_events"] = [self.event("published")]
        p, _ = plan_insights(self.context, self.request)
        self.assertEqual(
            p["projection"]["artifact_verification"], "declared-not-fetched"
        )
        self.assertEqual(before, self.canonical_bytes())
        self.request["candidates"][0]["caption"] += " changed"
        with self.assertRaisesRegex(ContractError, "INSIGHT_EVENT"):
            plan_insights(self.context, self.request)

    def test_privacy_unreviewed_and_missing_public_derivation_fail_without_canaries(
        self,
    ):
        for record_id in ("unreviewed", "private-record-canary"):
            request = deepcopy(self.request)
            request["candidates"][0]["claims"][0]["references"][0]["id"] = record_id
            with self.assertRaises(ContractError) as error:
                plan_insights(self.context, request)
            self.assertNotIn(record_id, str(error.exception))
        session = deepcopy(self.context.session)
        session["request_scope"]["visibility"] = "personal"
        session["request_scope"]["publication"] = "never-exportable"
        write_json(self.fixture["session_path"], session)
        context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        with self.assertRaisesRegex(ContractError, "INSIGHT_SCOPE"):
            plan_insights(context, self.request)

    def test_rights_uncertainty_authority_and_allowlist_fail_closed(self):
        mutations = [
            lambda c: c["rights"].update(status="unknown"),
            lambda c: c["claims"][0].update(certainty="supported"),
            lambda c: c["review"].update(reviewers=["untrusted-proposer"]),
        ]
        for mutate in mutations:
            request = deepcopy(self.request)
            mutate(request["candidates"][0])
            with self.assertRaises(ContractError):
                plan_insights(self.context, request)
        manifest = self.fixture["workspace"] / "garden/garden.json"
        if not manifest.exists():
            manifest = next(self.fixture["workspace"].rglob("garden.json"))
        document = json.loads(manifest.read_text())
        document["publication"]["allow"]["topics"] = []
        write_json(manifest, document)
        session = bind_session_revisions(
            self.fixture["configuration"],
            json.loads(self.fixture["session_path"].read_text()),
        )
        write_json(self.fixture["session_path"], session)
        context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        with self.assertRaises(ContractError):
            plan_insights(context, self.request)

    def test_cli_apply_retry_and_changed_authored_plan_fail_stale(self):
        path = self.root / "plan.json"
        write_json(path, self.request)
        argv = [
            "insights",
            "--local-config",
            str(self.fixture["configuration"]),
            "--scope",
            str(self.fixture["session_path"]),
            "--input",
            str(path),
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(argv), 0)
        digest = json.loads(output.getvalue())["plan_sha256"]
        apply = argv + [
            "--apply",
            "--plan-digest",
            digest,
            "--output-directory",
            str(self.root / "handoff"),
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(apply), 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "created")
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(apply), 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "verified-no-op")
        self.request["candidates"][0]["alt_text"] += " changed"
        write_json(path, self.request)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertNotEqual(main(apply), 0)

    def test_budget_and_conflicting_candidate_versions_fail(self):
        small = deepcopy(self.request)
        small["max_bytes"] = 512
        with self.assertRaisesRegex(ContractError, "INSIGHT_BUDGET"):
            plan_insights(self.context, small)
        self.request["candidates"] += [
            {**deepcopy(self.request["candidates"][0]), "caption": "Conflicting text."}
        ]
        with self.assertRaisesRegex(ContractError, "INSIGHT_IDENTITY"):
            plan_insights(self.context, self.request)

    def test_committed_authoring_plan_and_projection_golden(self):
        root = Path(__file__).parent / "fixtures/insights"
        self.assertEqual(
            self.request, json.loads((root / "authored-plan.json").read_text())
        )
        preview, files = plan_insights(self.context, self.request)
        proof = {
            "schema": "mindgarden.insight-proof/v1",
            "files": {name: digest_bytes(body) for name, body in files.items()},
            "total_bytes": preview["total_bytes"],
            "candidates": len(preview["projection"]["candidates"]),
            "canonical": False,
            "network": "not-used",
            "renderer": "not-used",
        }
        self.assertEqual(proof, json.loads((root / "expected-proof.json").read_text()))
