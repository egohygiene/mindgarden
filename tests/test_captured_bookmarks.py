"""Verified bundle → private cleanup → reviewed cross-source knowledge, offline."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bookmarks import HANDOFF, plan_bookmarks, read_metadata
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.garden import evidence_bytes
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_bookmarks as fixtures
from tests.bookmark_capture_fixture import bundle_members, package


class CapturedBookmarkTests(unittest.TestCase):
    def setUp(self):
        fixtures.BookmarkTests.setUp(self)
        old_ids = [r["id"] for r in self.records]
        self.members = bundle_members()
        self.source.write_bytes(package(self.members))
        self.source.rename(self.root / "bookmarks.zip")
        self.source = self.root / "bookmarks.zip"
        _, self.records = read_metadata(
            self.source, "personal", input_format="captured-source-bundle"
        )
        remap = dict(zip(old_ids, (r["id"] for r in self.records)))
        self.request["source_sha256"] = digest_bytes(self.source.read_bytes())
        for decision in self.request["decisions"]:
            decision["id"] = remap[decision["id"]]
            if decision["merge_into"]:
                decision["merge_into"] = remap[decision["merge_into"]]

    def plan(self, **kwargs):
        return plan_bookmarks(
            self.source,
            self.catalog,
            self.request,
            classification="personal",
            input_format="captured-source-bundle",
            **kwargs,
        )

    def test_verified_members_exact_evidence_and_inert_metadata_only_cleanup(self):
        captured = self.source.read_bytes()
        with (
            patch("socket.socket", side_effect=AssertionError("Network")),
            patch("subprocess.run", side_effect=AssertionError("Execution")),
        ):
            preview, files = self.plan()
            self.assertEqual((preview, files), self.plan())
        self.assertEqual(files["captured-source.zip"], captured)
        self.assertEqual(self.source.read_bytes(), captured)
        self.assertTrue(preview["capabilities"]["source_bundle"])
        self.assertTrue(preview["capabilities"]["member_checksums"])
        self.assertFalse(preview["capabilities"]["producer_authentication"])
        for record in self.records:
            self.assertEqual(record["page_content"], "not-captured")
            evidence = record["evidence"]
            content = self.members[evidence["original_selector"]["member"]]
            self.assertEqual(digest_bytes(content), evidence["sha256"])
            self.assertEqual(
                evidence_bytes(content, "json:/url").decode(), record["url"]
            )
        self.assertNotIn(b"javascript:", files["cleaned-bookmarks.html"])
        self.assertEqual(json.loads(files["akashic-handoff-status.json"]), HANDOFF)
        self.assertTrue(all("evidence" in d for d in preview["decisions"]))

    def test_later_observation_keeps_identity_but_invalidates_old_approval(self):
        before, _ = self.plan()
        members = deepcopy(self.members)
        manifest = json.loads(members["CAPTURED-SOURCE.json"])
        manifest.update(
            captured_at="2026-11-07T00:00:00Z",
            previous_bundle_sha256=self.request["source_sha256"],
        )
        members["capture/bookmarks.json"] += b"\n"
        raw = next(
            a for a in manifest["artifacts"] if a["path"] == "capture/bookmarks.json"
        )
        raw.update(
            sha256=digest_bytes(members[raw["path"]]),
            size_bytes=len(members[raw["path"]]),
        )
        members["CAPTURED-SOURCE.json"] = canonical_json(manifest)
        self.source.write_bytes(package(members))
        _, records = read_metadata(
            self.source, "personal", input_format="captured-source-bundle"
        )
        self.assertEqual([r["id"] for r in records], [r["id"] for r in self.records])
        self.assertEqual(
            [r["evidence"]["sha256"] for r in records],
            [r["evidence"]["sha256"] for r in self.records],
        )
        self.assertNotEqual(
            records[0]["evidence"]["raw_members"],
            self.records[0]["evidence"]["raw_members"],
        )
        with self.assertRaisesRegex(ContractError, "BOOKMARK_STALE"):
            self.plan()
        self.request["source_sha256"] = digest_bytes(self.source.read_bytes())
        after, _ = self.plan()
        self.assertNotEqual(before["plan_sha256"], after["plan_sha256"])

    def test_corruption_wrong_kind_missing_evidence_and_format_spoof_fail_closed(self):
        for kind in ("corrupt", "kind", "locator", "record"):
            members = deepcopy(self.members)
            manifest = json.loads(members["CAPTURED-SOURCE.json"])
            if kind == "corrupt":
                members["capture/bookmarks.json"] = b"Synthetic changed raw bytes"
            if kind == "kind":
                manifest["source_type"] = "reference-collection"
            if kind == "locator":
                manifest["units"][0]["locators"] = ["json:/title"]
            if kind == "record":
                member = manifest["units"][0]["member"]
                value = json.loads(members[member])
                value["record_type"] = "not-bookmark"
                members[member] = canonical_json(value)
                artifact = next(a for a in manifest["artifacts"] if a["path"] == member)
                artifact.update(
                    sha256=digest_bytes(members[member]),
                    size_bytes=len(members[member]),
                )
            members["CAPTURED-SOURCE.json"] = canonical_json(manifest)
            self.source.write_bytes(package(members))
            with self.subTest(kind=kind), self.assertRaises(ContractError):
                read_metadata(
                    self.source, "personal", input_format="captured-source-bundle"
                )
        self.source.write_bytes(
            canonical_json(
                {"schema": "mindcap.captured-source-bundle/v1", "bookmark_records": []}
            )
        )
        with self.assertRaisesRegex(ContractError, "BOOKMARK_INCOMPATIBLE"):
            read_metadata(self.source, "personal")

    def test_partial_capture_is_never_reported_as_complete_review(self):
        members = deepcopy(self.members)
        manifest = json.loads(members["CAPTURED-SOURCE.json"])
        manifest.update(status="partial", warnings=["CAPTURE_WARNINGS_PRESENT"])
        members["CAPTURED-SOURCE.json"] = canonical_json(manifest)
        self.source.write_bytes(package(members))
        self.request["source_sha256"] = digest_bytes(self.source.read_bytes())
        preview, files = self.plan()
        self.assertEqual(preview["capture"]["status"], "partial")
        self.assertIsNone(preview["next_offset"])
        self.assertFalse(json.loads(files["cleaned-bookmarks.json"])["complete_review"])

    def test_cli_private_apply_replay_stale_refusal_and_redacted_summaries(self):
        request = self.root / "request.json"
        request.write_bytes(canonical_json(self.request))
        output = self.root / "reviewed-export"
        args = [
            "bookmarks",
            "--input-format",
            "captured-source-bundle",
            "--classification",
            "personal",
            "--input",
            str(self.source),
            "--catalog",
            str(self.catalog),
            "--request",
            str(request),
            "--plan-file",
            str(self.root / "review.json"),
        ]
        with redirect_stdout(io.StringIO()) as summary:
            self.assertEqual(main(args), 0)
            plan = json.loads((self.root / "review.json").read_bytes())
            apply = [
                *args,
                "--apply",
                "--output-directory",
                str(output),
                "--plan-digest",
                plan["plan_sha256"],
            ]
            self.assertEqual(main(apply), 0)
            self.assertEqual(main(apply), 0)
        self.assertEqual(
            (output / "captured-source.zip").read_bytes(), self.source.read_bytes()
        )
        self.assertEqual((output / "captured-source.zip").stat().st_mode & 0o777, 0o600)
        for canary in (
            "example.test",
            "Synthetic private folder",
            "synthetic-profile",
            str(self.root),
        ):
            self.assertNotIn(canary, summary.getvalue())
        self.source.write_bytes(self.source.read_bytes() + b"Synthetic trailing change")
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                main(
                    [*apply, "--output-directory", str(self.root / "should-not-exist")]
                ),
                3,
            )
        self.assertFalse((self.root / "should-not-exist").exists())

    def test_restricted_policy_denies_before_input_access(self):
        with patch.object(Path, "open", side_effect=AssertionError("Source accessed")):
            with self.assertRaisesRegex(ContractError, "BOOKMARK_RUNTIME_UNAVAILABLE"):
                read_metadata(
                    self.source, "restricted", input_format="captured-source-bundle"
                )

    def test_authored_bookmark_and_conversation_link_requires_explicit_review(self):
        from mindgarden.application.curation import apply_curation, build_curation_plan
        from mindgarden.application.extraction import produce_batch
        from mindgarden.application.query import QueryContext
        from mindgarden.application.retrieval import build_index, graph_payload
        from tests import extraction_fixture, test_source_adapters
        from tests.support_v1 import TIME, write_json, write_session

        test = test_source_adapters.SourceAdapterTests()
        test.setUp()
        self.addCleanup(test.doCleanups)
        records = json.loads(
            (Path(__file__).parent / "fixtures/bookmarks/normalized.json").read_bytes()
        )["bookmark_records"][:2]
        records[0].update(
            title="Synthetic evidence guide", url="https://example.test/evidence"
        )
        records[1].update(
            title="inert-bookmarklet", url="javascript:synthetic_do_not_execute()"
        )
        context, request, producer, _ = extraction_fixture.initialize(
            test, bookmark_bytes=package(bundle_members(records))
        )
        with patch("socket.socket", side_effect=AssertionError("Network")):
            batch = produce_batch(context, request, producer)
        proposal = deepcopy(batch["proposal"])
        self.assertIsNone(proposal["review_authority"])
        outputs = [c["output"] for c in proposal["candidates"]]
        bookmark = next(o for o in outputs if o["title"] == "Synthetic evidence guide")
        conversation = next(
            o
            for o in outputs
            if o["title"] == "Exact evidence may support explicit uncertainty."
        )
        self.assertEqual(bookmark["review"]["state"], "unreviewed")
        self.assertEqual(graph_payload(context)["edges"], [])
        review = {
            "state": "approved",
            "reviewers": ["synthetic-reviewer"],
            "reviewed_at": TIME,
            "rationale": "Authored synthetic source-grounded review; saved link is not endorsement.",
        }
        bookmark["synapses"].append(
            {
                "id": "bookmark-conversation-reference",
                "type": "references",
                "target": {"garden": "synthetic-garden", "id": conversation["id"]},
                "directed": True,
                "review": review,
                "rationale": "Reviewed topical connection, not a claim about the uncaptured page.",
            }
        )
        proposal["review_authority"] = {"kind": "human", "id": "synthetic-reviewer"}
        for output in outputs:
            output.update(review=review, status="active")
            for item in output["claims"] + output["synapses"]:
                item["review"] = review
        path = test.root / "reviewed-bookmarks.json"
        write_json(path, proposal)
        original_vault = test.vault.export_bundle()
        plan = build_curation_plan(test.bindings, path)
        apply_curation(plan, plan.digest, test.bindings)
        session = test.root / "reviewed-session.json"
        write_session(session, test.configuration)
        reviewed = QueryContext.load(test.configuration, session)
        graph = graph_payload(reviewed)
        self.assertTrue(
            any(
                e["type"] == "references"
                and e["source"] == "synthetic-garden/" + bookmark["id"]
                and e["target"] == "synthetic-garden/" + conversation["id"]
                for e in graph["edges"]
            )
        )
        self.assertEqual(
            build_index(reviewed),
            build_index(QueryContext.load(test.configuration, session)),
        )
        self.assertEqual(test.vault.export_bundle(), original_vault)
