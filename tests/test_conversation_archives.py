"""Current archive contracts, overlapping evidence, hostile packages and curation."""

from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.conversation_archive import ConversationArchiveAdapter
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import render_context, search_payload
from mindgarden.application.storage import content_resolver
from mindgarden.domain.contracts import canonical_json, digest_bytes, strict_json
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.validation import ContractError
from tests.archive_fixture import package_bytes, package_members
from tests.support_v1 import write_json, write_session
from tests import test_source_adapters as source_tests


class ConversationArchiveTests(unittest.TestCase):
    def setUp(self):
        source_tests.SourceAdapterTests.setUp(self)
        self.input = self.root / "synthetic-archive.zip"
        self.metadata.update(source_id="synthetic-archive", title="Synthetic conversation archive",
                             origin="urn:synthetic:conversation", media_type="application/zip")

    def plan(self, members=None, **options):
        self.input.write_bytes(package_bytes(members or package_members(), **options))
        return build_ingestion_plan(self.bindings, "synthetic-garden", "synthetic-vault", self.input,
                                    self.metadata, adapter_id="conversation-archive", manifest_version="3.2.3")

    def test_both_contract_versions_and_profiles_have_exact_original_selectors(self):
        adapter = ConversationArchiveAdapter()
        for version in ("3.2.2", "3.2.3"):
            for profile in ("full-source", "summary-journey"):
                with self.subTest(version=version, profile=profile):
                    members = package_members(profile, version)
                    with patch("socket.socket", side_effect=AssertionError("Network attempted")):
                        result = adapter.normalize(package_bytes(members, prefix="synthetic-unit/"),
                                                   {"manifest_version": version})
                    self.assertEqual(result.metadata["spec_version"], version)
                    self.assertEqual(result.metadata["producer_validation"], "incomplete")
                    self.assertEqual(result.metadata["full_producer_conformance"], "not-claimed")
                    if profile == "full-source":
                        unit = next(item for item in result.units if item.identity.endswith(":message:message-prompt"))
                        self.assertEqual(unit.metadata["speaker"], "assistant")
                        self.assertEqual(unit.metadata["source_message_id"], "synthetic-native-2")
                        self.assertEqual(unit.locators, ("json:/content/0/text",))
                        self.assertEqual(result.metadata["primary_view"]["ordering_basis"], "source-order")
                        self.assertEqual(len(result.metadata["branches"]), 2)
                        asset = next(item for item in result.units if ":asset:" in item.identity)
                        self.assertEqual(asset.content, members["assets/attachment.txt"])
                    else:
                        unit = next(item for item in result.units if item.identity.endswith(":record:journey-001"))
                        self.assertTrue(unit.metadata["summary_derived"])
                        self.assertIsNone(unit.metadata["speaker"])
                        self.assertIsNone(unit.metadata["timestamp"])
                        selector = unit.metadata["original_selector"]
                        self.assertEqual(unit.content, members["JOURNEY.md"][selector["byte_start"]:selector["byte_end"]])

    def test_repeated_and_overlapping_exports_do_not_duplicate_unchanged_evidence(self):
        first = self.plan()
        apply_ingestion(first, first.digest, self.bindings, "synthetic-vault")
        self.assertFalse(apply_ingestion(first, first.digest, self.bindings, "synthetic-vault"))
        second = self.plan(package_members(revision=2))
        self.assertEqual([item["source"] for item in first.inputs["normalized_sources"]],
                         [item["source"] for item in second.inputs["normalized_sources"]])
        apply_ingestion(second, second.digest, self.bindings, "synthetic-vault")
        snapshot = inspect_garden(self.workspace, content_resolver=content_resolver(self.bindings)).require_valid()
        normalized = [item for item in snapshot.records.values()
                      if item["schema"] == "mindgarden.source/v1" and item["kind"] == "normalized"]
        self.assertEqual(len(normalized), len(first.inputs["normalized_sources"]))
        self.assertEqual(len([item for item in snapshot.records.values()
                              if item["schema"] == "mindgarden.source/v1" and item["kind"] == "captured"]), 2)

    def test_primary_and_fallback_packagers_preserve_same_evidence(self):
        ordinary = self.plan()
        fallback = self.plan(package_members(fallback=True))
        self.assertEqual(ordinary.inputs["normalized_sources"], fallback.inputs["normalized_sources"])
        capture = next(strict_json(content) for path, content in fallback.files.items()
                       if path.startswith("sources/capture-"))
        history = capture["x-adapter"]["metadata"]["delivery"]["attempts"]
        self.assertEqual([item["archive_created"] for item in history], [False, True])

    def test_archive_candidate_becomes_reviewed_prompt_with_exact_search_and_context_evidence(self):
        source_plan = self.plan()
        with patch("subprocess.run", side_effect=AssertionError("Transcript instruction executed")):
            apply_ingestion(source_plan, source_plan.digest, self.bindings, "synthetic-vault")
        source = next(item for item in source_plan.inputs["normalized_sources"]
                      if item["metadata"].get("message_id") == "message-prompt")
        proposal = json.loads((Path(__file__).parent / "fixtures/conversation-archives/authored-plan.json").read_text())
        self.assertEqual(proposal["candidates"][0]["sources"], source["evidence"])
        path = self.root / "archive-curation.json"; write_json(path, proposal)
        plan = build_curation_plan(self.bindings, path)
        apply_curation(plan, plan.digest, self.bindings)
        session = self.root / "session.json"; write_session(session, self.configuration)
        context = QueryContext.load(self.configuration, session)
        results = search_payload(context, "evidence")
        self.assertEqual(results["results"][0]["reference"]["id"], "reviewed-prompt")
        self.assertEqual(results["results"][0]["sources"], source["evidence"])
        profile = json.loads((self.workspace / ".garden/context-packs/default.json").read_text())
        pack = strict_json(render_context(context, profile, "json"))
        self.assertEqual(pack["included"][0]["sources"], source["evidence"])
        self.assertFalse((self.root / "synthetic-malicious-command").exists())

    def test_malformed_controls_relationships_and_missing_assets_fail_before_writes(self):
        def mutate(name, field, value):
            members = package_members()
            data = strict_json(members[name]); data[field] = value
            members[name] = canonical_json(data)
            return members

        cases = [mutate("ARCHIVE-MANIFEST.json", "spec_version", "2.0.1"),
                 mutate("ARCHIVE-MANIFEST.json", "spec_version", "3.2.2"),
                 mutate("ARCHIVE-MANIFEST.json", "transcript_preserved", False),
                 mutate("ARCHIVE-MANIFEST.json", "compression", {}),
                 mutate("VALIDATION.json", "overall", "fail")]
        missing = package_members(); del missing["assets/attachment.txt"]; cases.append(missing)
        duplicate = package_members(); duplicate["VALIDATION.json"] = b'{"schema_version":"2.0","schema_version":"2.0"}'
        cases.append(duplicate)
        dangling = package_members(); data = strict_json(dangling["CONVERSATION.json"])
        data["messages"][1]["parent_ids"] = ["not-observed"]
        dangling["CONVERSATION.json"] = canonical_json(data); cases.append(dangling)
        for members in cases:
            with self.subTest(case=digest_bytes(package_bytes(members))):
                with self.assertRaises(ContractError):
                    self.plan(members)
        self.assertEqual(self.vault.audit()["objects"], [])

    def test_hostile_zip_members_and_inventory_mismatches_fail_safely(self):
        adapter = ConversationArchiveAdapter()
        for bad_name in ("../escape.txt", "/absolute.txt", "a\\b.txt", "AUX.txt", "a/../b.txt"):
            members = package_members(); members[bad_name] = b"hostile"
            with self.subTest(name=bad_name), self.assertRaisesRegex(ContractError, "ARCHIVE_PATH"):
                adapter.normalize(package_bytes(members), {})
        for additions in ({"README.MD": b"collision"}, {"unexpected.txt": b"unlisted"}):
            members = package_members()
            content = package_bytes(members)
            with ZipFile(BytesIO(content)) as original:
                copied = {name: original.read(name) for name in original.namelist()}
            copied.update(additions)
            with self.assertRaises(ContractError):
                adapter.normalize(package_bytes(copied, inventory=False), {})
        output = BytesIO()
        with ZipFile(output, "w") as archive:
            entry = ZipInfo("symlink"); entry.external_attr = 0o120777 << 16
            archive.writestr(entry, "../escape")
        with self.assertRaisesRegex(ContractError, "ARCHIVE_LINK"):
            adapter.normalize(output.getvalue(), {})
        with self.assertRaisesRegex(ContractError, "ARCHIVE_CORRUPTED"):
            adapter.normalize(b"not a zip", {})
        with self.assertRaisesRegex(ContractError, "ARCHIVE_COLLISION"):
            adapter.normalize(package_bytes({"file": b"a", "file/child": b"b"}), {})

    def test_compact_machine_index_cannot_fabricate_messages_or_mismatch_phases(self):
        members = package_members("summary-journey")
        members["CONVERSATION.json"] = package_members()["CONVERSATION.json"]
        with self.assertRaisesRegex(ContractError, "ARCHIVE_PROFILE"):
            self.plan(members)
        members = package_members("summary-journey")
        trail = strict_json(members["SUMMARY-TRAIL.json"])
        trail["checkpoints"][0]["id"] = "journey-unobserved"
        members["SUMMARY-TRAIL.json"] = canonical_json(trail)
        with self.assertRaisesRegex(ContractError, "ARCHIVE_TRAIL"):
            self.plan(members)
