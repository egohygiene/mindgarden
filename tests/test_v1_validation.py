"""General v1 validation, compatibility and negative evidence fixtures."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.lifecycle import apply_migration, build_migration_plan
from mindgarden.domain.contracts import ContractRegistry, strict_json
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.validation import ContractError, validate_repository
from mindgarden.interfaces.cli import main
from tests.support_v1 import FIXTURES, add_knowledge, create_garden, reference, write_json
from tests.test_v1_contracts import apply_mutation


class RuntimeContractTests(unittest.TestCase):
    def test_runtime_matches_schema_golden_and_adversarial_fixtures(self):
        registry = ContractRegistry()
        for path in FIXTURES.glob("*.json"):
            value = json.loads(path.read_text())
            with self.subTest(path=path.name):
                self.assertEqual(registry.errors(value, value["schema"]), [])
        cases = json.loads((FIXTURES.parent / "invalid/cases.json").read_text())["cases"]
        for case in cases:
            value = json.loads((FIXTURES / case["base"]).read_text())
            for mutation in case["mutations"]:
                apply_mutation(value, mutation)
            with self.subTest(case=case["id"]):
                self.assertTrue(registry.errors(value, case["contract"]))

    def test_json_is_strict_and_does_not_echo_source_data(self):
        for value in ('{"private":1,"private":2}', '{"value":NaN}', '{"value":1e999}',
                      '{"value":"\\ud800"}'):
            with self.subTest(value=value), self.assertRaises(ContractError) as caught:
                strict_json(value)
            self.assertNotIn("private", str(caught.exception))

    def test_unknown_schema_vocabulary_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            write_json(path / "common.schema.json", {
                "$id": "urn:synthetic:unsupported", "unevaluatedProperties": False})
            with self.assertRaisesRegex(ContractError, "CONTRACT_UNSUPPORTED"):
                ContractRegistry(path)


class V1ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.garden = create_garden(self.root)

    def codes(self):
        return {item.code for item in inspect_garden(self.root).diagnostics}

    def test_initialized_v1_validates_through_normal_cli_and_json(self):
        self.assertEqual(validate_repository(self.root), 0)
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["validate", "--repository-root", str(self.root), "--format", "json"]), 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "valid")
        self.assertNotIn(str(self.root), output.getvalue())

    def test_migration_validates_and_reciprocal_related_links_are_not_duplicated(self):
        other = self.root / "migration"
        shutil.copytree(Path(__file__).parent / "fixtures/public-garden", other)
        plan = build_migration_plan(other, ["software-engineering"], [])
        apply_migration(other, plan)
        self.assertEqual(validate_repository(other), 3)
        self.assertEqual(inspect_garden(other).diagnostics, [])
        synapses = [json.loads(path.read_text()) for path in (other / ".garden/synapses").glob("*.json")]
        self.assertEqual(len(synapses), 1)

    def test_duplicate_identity_and_dangling_claim_are_actionable(self):
        record = add_knowledge(self.root)
        write_json(self.garden / "knowledge/duplicate.json", record)
        self.assertIn("IDENTITY_DUPLICATE", self.codes())
        (self.garden / "knowledge/duplicate.json").unlink()
        record["claims"] = [reference("synthetic-garden", "missing-claim")]
        write_json(self.garden / "knowledge/synthetic-prompt.json", record)
        self.assertIn("REFERENCE_DANGLING", self.codes())

    def test_modified_bytes_and_provenance_are_rejected(self):
        record = add_knowledge(self.root)
        (self.garden / record["content"]["path"]).write_text("Changed synthetic content.\n")
        self.assertIn("CONTENT_HASH", self.codes())
        self.assertIn("PROVENANCE_HASH", self.codes())

    def test_traversal_symlinks_and_overlapping_roots_are_rejected(self):
        record = add_knowledge(self.root)
        record["content"]["path"] = "../outside.md"
        write_json(self.garden / "knowledge/synthetic-prompt.json", record)
        self.assertTrue(self.codes() & {"PATH_UNSAFE", "SCHEMA_PATTERN"})
        (self.garden / "link").symlink_to(self.root)
        self.assertIn("PATH_SYMLINK", self.codes())
        (self.garden / "link").unlink()
        manifest = json.loads((self.garden / "garden.json").read_text())
        manifest["roots"]["generated"] = ["knowledge/generated"]
        write_json(self.garden / "garden.json", manifest)
        self.assertIn("ROOT_OVERLAP", self.codes())

    def test_public_eligibility_requires_review_and_public_visibility(self):
        record = add_knowledge(self.root, reviewed=False)
        record["publication"] = "eligible"
        write_json(self.garden / "knowledge/synthetic-prompt.json", record)
        self.assertTrue(self.codes())
        manifest = json.loads((self.garden / "garden.json").read_text())
        manifest["visibility"] = "public"
        write_json(self.garden / "garden.json", manifest)
        record = add_knowledge(self.root)
        self.assertIn("PUBLIC_PRIVATE_CONTENT", self.codes())

    def test_unavailable_cross_garden_is_incomplete_not_valid(self):
        record = add_knowledge(self.root)
        record["supersedes"] = [reference("other-garden", "other-note")]
        write_json(self.garden / "knowledge/synthetic-prompt.json", record)
        report = inspect_garden(self.root).report()
        self.assertEqual(report["status"], "incomplete")
        self.assertEqual(report["diagnostics"][0]["code"], "REFERENCE_UNAVAILABLE")

    def test_supersession_cycle_and_ambiguous_manifest_fail(self):
        first = add_knowledge(self.root, "first")
        second = add_knowledge(self.root, "second")
        first["supersedes"] = [reference("synthetic-garden", "second")]
        second["supersedes"] = [reference("synthetic-garden", "first")]
        write_json(self.garden / "knowledge/first.json", first)
        write_json(self.garden / "knowledge/second.json", second)
        self.assertIn("SUPERSESSION_CYCLE", self.codes())
        (self.garden / "garden.yaml").write_text("schema: mindgarden.garden/v0\n")
        with self.assertRaisesRegex(ContractError, "MANIFEST_AMBIGUOUS"):
            validate_repository(self.root)

    def test_active_link_and_path_fixtures_fail_without_echoing_content(self):
        cases = json.loads((Path(__file__).parent / "fixtures/v1-validation/cases.json").read_text())
        for item in cases["links"]:
            with self.subTest(link=item["target"]):
                add_knowledge(self.root, body="[Synthetic evidence](" + item["target"] + ")\n")
                report = inspect_garden(self.root).report()
                self.assertIn(item["code"], {value["code"] for value in report["diagnostics"]})
                self.assertNotIn("synthetic-private-marker", json.dumps(report))
                self.assertNotIn("synthetic-password", json.dumps(report))
        for value in cases["paths"]:
            record = add_knowledge(self.root)
            record["content"]["path"] = value
            write_json(self.garden / "knowledge/synthetic-prompt.json", record)
            self.assertTrue(self.codes() & {"PATH_UNSAFE", "SCHEMA_PATTERN"})

    def test_public_links_cannot_expose_private_knowledge(self):
        add_knowledge(self.root, "private-note")
        add_knowledge(self.root, "public-note", body="[Reference](private-note.md)\n", visibility="public")
        self.assertIn("PUBLIC_PRIVATE_LINK", self.codes())

    def test_transformation_metadata_tampering_invalidates_its_pinned_reference(self):
        add_knowledge(self.root)
        path = self.garden / "provenance/provenance-synthetic-prompt.json"
        record = json.loads(path.read_text())
        record["transformations"][0]["parameters"] = {"changed": True}
        write_json(path, record)
        self.assertIn("REFERENCE_REVISION", self.codes())

    def test_binary_knowledge_and_oversized_metadata_fail_safely(self):
        record = add_knowledge(self.root)
        (self.garden / record["content"]["path"]).write_bytes(b"\xff")
        self.assertTrue(self.codes())
        path = self.garden / "knowledge/oversized.json"
        path.write_text(" " * 2_000_001)
        self.assertIn("RECORD_OVERSIZED", self.codes())
