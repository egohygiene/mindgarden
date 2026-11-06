"""Synthetic private cleanup; unavailable integrations cannot become publication."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from mindgarden.application.bookmarks import read_metadata, plan_bookmarks, HANDOFF
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.scope import POLICY_REFERENCE
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main


class BookmarkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        fixture = Path(__file__).parent / "fixtures/bookmarks"
        self.source = self.root / "normalized.json"
        self.catalog = self.root / "catalog.json"
        shutil.copyfile(fixture / "normalized.json", self.source)
        shutil.copyfile(fixture / "catalog.json", self.catalog)
        _, self.records = read_metadata(self.source, "personal")
        actions = [
            "keep",
            "merge",
            "move",
            "rename",
            "observed-redirect",
            "defer",
            "private-route",
            "keep",
            "publish-proposal",
            "publish-proposal",
            "omit",
            "quarantine",
        ]
        decisions = [
            {
                "id": r["id"],
                "action": a,
                "rationale": "Authored synthetic review; no inferred endorsement.",
                "new_title": None,
                "new_folders": None,
                "merge_into": None,
                "public_approval": n == 8,
            }
            for n, (r, a) in enumerate(zip(self.records, actions))
        ]
        decisions[1]["merge_into"] = self.records[0]["id"]
        decisions[2]["new_folders"] = ["Reviewed", "Synthetic"]
        decisions[3]["new_title"] = "<Synthetic & renamed>"
        self.request = {
            "schema": "mindgarden.bookmark-review-request/v1",
            "source_sha256": digest_bytes(self.source.read_bytes()),
            "catalog_sha256": digest_bytes(self.catalog.read_bytes()),
            "prior_receipt_sha256": None,
            "policy": POLICY_REFERENCE,
            "review": {
                "state": "approved",
                "reviewers": ["synthetic-reviewer"],
                "reviewed_at": "2026-11-06T00:00:00Z",
                "rationale": "Authored synthetic private cleanup.",
            },
            "review_authority": {"kind": "human", "id": "synthetic-reviewer"},
            "offset": 0,
            "limit": 50,
            "decisions": decisions,
        }

    def plan(self, **kwargs):
        return plan_bookmarks(
            self.source, self.catalog, self.request, classification="personal", **kwargs
        )

    def test_private_plan_rebuild_and_exports_preserve_original_and_never_visit_urls(
        self,
    ):
        before = self.source.read_bytes()
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            preview, files = self.plan()
            self.assertEqual((preview, files), self.plan())
        self.assertEqual(files["captured-normalized.json"], before)
        self.assertEqual(self.source.read_bytes(), before)
        html = files["cleaned-bookmarks.html"].decode()
        self.assertIn("&lt;Synthetic &amp; renamed&gt;", html)
        for denied in (
            "javascript:",
            "service.internal",
            "session=synthetic",
            "/approved",
            "/pending",
        ):
            self.assertNotIn(denied, html)
        self.assertEqual(len(json.loads(files["cleaned-bookmarks.json"])["records"]), 3)
        self.assertFalse(preview["capabilities"]["browser_mutation"])

    def test_public_approval_does_not_invent_an_akashic_packet_or_include_private_metadata(
        self,
    ):
        preview, files = self.plan()
        self.assertEqual(json.loads(files["akashic-handoff-status.json"]), HANDOFF)
        safe = files["akashic-handoff-status.json"].decode()
        for private in (
            "Synthetic private folder",
            "synthetic-profile",
            "example.test",
            self.records[8]["id"],
            str(self.root),
        ):
            self.assertNotIn(private, safe)
        self.assertEqual(
            [
                r["state"]
                for r in preview["decisions"]
                if r["action"] == "publish-proposal"
            ],
            ["deferred", "deferred"],
        )

    def test_resume_matches_full_review_and_changed_receipt_or_source_fails(self):
        original = deepcopy(self.request)
        full = self.plan()[1]
        self.request["limit"] = 3
        self.request["decisions"] = original["decisions"][:3]
        first, files = self.plan()
        prior = json.loads(files["review-receipt.json"])
        sha = digest_bytes(files["review-receipt.json"])
        self.request = deepcopy(original)
        self.request.update(
            offset=3, prior_receipt_sha256=sha, decisions=original["decisions"][3:]
        )
        second, rest = self.plan(previous=prior, previous_sha256=sha)
        self.assertIsNone(second["next_offset"])
        self.assertEqual(rest["cleaned-bookmarks.json"], full["cleaned-bookmarks.json"])
        self.assertEqual(rest["cleaned-bookmarks.html"], full["cleaned-bookmarks.html"])
        with self.assertRaisesRegex(ContractError, "BOOKMARK_STALE"):
            self.plan(previous=prior, previous_sha256="0" * 64)

    def test_ambiguous_identity_and_implicit_duplicates_fail_without_overwrite(self):
        data = json.loads(self.source.read_text())
        data["bookmark_records"][1]["source_guid"] = data["bookmark_records"][0][
            "source_guid"
        ]
        self.source.write_text(json.dumps(data))
        with self.assertRaisesRegex(ContractError, "BOOKMARK_IDENTITY"):
            read_metadata(self.source, "personal")
        shutil.copyfile(
            Path(__file__).parent / "fixtures/bookmarks/normalized.json", self.source
        )
        self.request["decisions"][1]["action"] = "keep"
        with self.assertRaisesRegex(ContractError, "BOOKMARK_DUPLICATE"):
            self.plan()

    def test_restricted_or_unknown_contract_denies_before_capture_access(self):
        with patch.object(
            Path, "read_bytes", side_effect=AssertionError("Source opened")
        ):
            with self.assertRaisesRegex(ContractError, "BOOKMARK_RUNTIME_UNAVAILABLE"):
                plan_bookmarks(self.source, self.catalog, self.request)
        data = json.loads(self.source.read_text())
        data["schema"] = "missing-captured-bundle/v99"
        self.source.write_text(json.dumps(data))
        with self.assertRaisesRegex(ContractError, "BOOKMARK_INCOMPATIBLE"):
            read_metadata(self.source, "personal")

    def test_stale_catalog_and_changed_review_digest_create_no_output(self):
        path = self.root / "request.json"
        path.write_bytes(canonical_json(self.request))
        preview, _ = self.plan()
        self.request["decisions"][0]["rationale"] = "Changed proposal"
        path.write_bytes(canonical_json(self.request))
        destination = self.root / "export"
        args = [
            "bookmarks",
            "--classification",
            "personal",
            "--input",
            str(self.source),
            "--catalog",
            str(self.catalog),
            "--request",
            str(path),
            "--plan-file",
            str(self.root / "private-plan.json"),
            "--apply",
            "--output-directory",
            str(destination),
            "--plan-digest",
            preview["plan_sha256"],
        ]
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(args), 3)
        self.assertFalse(destination.exists())
        self.catalog.write_text("{}")
        with self.assertRaisesRegex(ContractError, "BOOKMARK_CATALOG"):
            self.plan()

    def test_cli_summaries_contain_no_titles_urls_folders_profiles_or_paths(self):
        path = self.root / "request.json"
        path.write_bytes(canonical_json(self.request))
        plan_path = self.root / "private-plan.json"
        args = [
            "bookmarks",
            "--classification",
            "personal",
            "--input",
            str(self.source),
            "--catalog",
            str(self.catalog),
            "--request",
            str(path),
            "--plan-file",
            str(plan_path),
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(args), 0)
        preview = json.loads(plan_path.read_text())
        destination = self.root / "export"
        with redirect_stdout(io.StringIO()) as applied:
            self.assertEqual(
                main(
                    args
                    + [
                        "--apply",
                        "--output-directory",
                        str(destination),
                        "--plan-digest",
                        preview["plan_sha256"],
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    args
                    + [
                        "--apply",
                        "--output-directory",
                        str(destination),
                        "--plan-digest",
                        preview["plan_sha256"],
                    ]
                ),
                0,
            )
        for canary in (
            "example.test",
            "Synthetic private folder",
            "synthetic-profile",
            str(self.root),
            "Synthetic bookmark",
        ):
            self.assertNotIn(canary, output.getvalue() + applied.getvalue())
