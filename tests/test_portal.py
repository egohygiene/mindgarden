"""Pinned local portal composition, preservation and recovery contracts."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.portal import build_portal
from mindgarden.adapters.site_files import read_site
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.portal import PORTAL_MARKER
from mindgarden.domain.site import SITE_MARKER
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.portal_fixture import create_portal_fixture
from tests.support_v1 import write_json
from tests import test_v1_contracts as contract_tests


class PortalTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_portal_fixture(self.root)
        self.request = self.fixture["request"]

    def sibling_bytes(self):
        return {path.relative_to(self.fixture["portal"]).as_posix(): path.read_bytes()
                for surface in ("intelligence", "decisions", "history")
                for path in (self.fixture["portal"] / surface).rglob("*") if path.is_file()}

    def test_plan_apply_repeat_check_preserve_siblings_and_expose_only_portable_owned_paths(self):
        before = self.sibling_bytes()
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            composition = build_portal(self.request); plan = composition.plan()
            self.assertFalse((self.fixture["portal"] / "garden").exists())
            self.assertTrue(composition.apply(plan["plan_sha256"]))
            self.assertFalse(composition.apply(plan["plan_sha256"]))
            self.assertEqual(composition.verify(), composition.manifest)
        self.assertEqual(self.sibling_bytes(), before)
        self.assertEqual(read_site(self.fixture["portal"] / "garden"), self.fixture["files"])
        public = canonical_json(composition.manifest)
        self.assertNotIn(str(self.root).encode(), public)
        self.assertTrue(all(item["path"].startswith("garden/") for item in composition.manifest["owned"]))
        self.assertEqual(composition.manifest["site"]["manifest_sha256"], self.request["source"]["expected_manifest_sha256"])

    def test_request_plan_and_manifest_match_official_and_runtime_schemas(self):
        composition = build_portal(self.request)
        contract_tests.V1ContractTests.setUpClass(); reference = contract_tests.V1ContractTests()
        for name, value in (("portal-request", self.request), ("portal-plan", composition.plan()), ("portal-manifest", composition.manifest)):
            with self.subTest(name=name):
                self.assertEqual(ContractRegistry().errors(value, name), [])
                self.assertEqual(list(reference.validator(name).iter_errors(value)), [])

    def test_actual_manifest_pin_is_required_even_if_represented_revision_is_unchanged(self):
        request = deepcopy(self.request); request["source"]["expected_manifest_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "PORTAL_STALE"): build_portal(request)
        composition = build_portal(self.request); plan = composition.plan()
        path = self.fixture["source"] / "index.html"; path.write_text("Tampered supplied artifact")
        with self.assertRaisesRegex(ContractError, "PORTAL_STALE"): composition.apply(plan["plan_sha256"])
        self.assertFalse((self.fixture["portal"] / "garden").exists())

    def test_changed_control_or_destination_invalidates_plan_before_writes(self):
        path = self.root / "request.json"; write_json(path, self.request)
        composition = build_portal(self.request, request_path=path); plan = composition.plan()
        request = deepcopy(self.request); request["portal"]["mount"] = "other"
        write_json(path, request)
        with self.assertRaisesRegex(ContractError, "PORTAL_STALE"): composition.apply(plan["plan_sha256"])
        write_json(path, self.request)
        second = self.root / "second-portal"; second.mkdir()
        request = deepcopy(self.request); request["portal"]["directory"] = str(second)
        with self.assertRaisesRegex(ContractError, "PORTAL_STALE"): build_portal(request).apply(plan["plan_sha256"])
        self.assertEqual(list(second.iterdir()), [])

    def test_routes_paths_missing_outputs_symlinks_and_existing_caller_content_fail_closed(self):
        for base, mount in (("https://example.test/wrong/", "garden"), ("https://localhost/", "garden"), ("https://example.test/", "../escape")):
            request = deepcopy(self.request); request["portal"].update(base_uri=base, mount=mount)
            with self.subTest(base=base, mount=mount), self.assertRaises(ContractError): build_portal(request)
        request = deepcopy(self.request); request["portal"]["directory"] = str(self.root / "missing")
        with self.assertRaisesRegex(ContractError, "PORTAL_OUTPUT"): build_portal(request)
        target = self.fixture["portal"] / "garden"; target.mkdir(); marker = target / "human.txt"; marker.write_text("Keep caller content")
        composition = build_portal(self.request)
        with self.assertRaisesRegex(ContractError, "SITE_OUTPUT_CONFLICT"): composition.apply(composition.plan()["plan_sha256"])
        self.assertEqual(marker.read_text(), "Keep caller content")
        marker.unlink(); target.rmdir(); target.symlink_to(self.fixture["source"], target_is_directory=True)
        with self.assertRaisesRegex(ContractError, "PATH_SYMLINK"): build_portal(self.request)

    def test_receipt_failure_retains_complete_site_and_retry_finishes_without_touching_siblings(self):
        composition = build_portal(self.request); digest = composition.plan()["plan_sha256"]
        before = self.sibling_bytes()
        with patch("mindgarden.application.portal.create_receipt", side_effect=OSError("Synthetic receipt failure")):
            with self.assertRaises(OSError): composition.apply(digest)
        self.assertEqual(read_site(self.fixture["portal"] / "garden"), self.fixture["files"])
        with self.assertRaisesRegex(ContractError, "PORTAL_INCOMPLETE"): composition.verify()
        self.assertTrue(composition.apply(digest)); self.assertFalse(composition.apply(digest))
        self.assertEqual(before, self.sibling_bytes())

    def test_conflicting_receipt_is_retained_and_prevents_copy(self):
        receipt = self.fixture["portal"] / PORTAL_MARKER; receipt.write_text("Caller-owned receipt")
        composition = build_portal(self.request)
        with self.assertRaisesRegex(ContractError, "PORTAL_CONFLICT"): composition.apply(composition.plan()["plan_sha256"])
        self.assertEqual(receipt.read_text(), "Caller-owned receipt")
        self.assertFalse((self.fixture["portal"] / "garden").exists())

    def test_relocated_source_and_clean_portal_rebuild_identical_public_manifest(self):
        first = build_portal(self.request)
        moved = self.root / "relocated-public-site"; shutil.copytree(self.fixture["source"], moved)
        portal = self.root / "clean-portal"; portal.mkdir()
        request = deepcopy(self.request); request["source"]["directory"] = str(moved); request["portal"]["directory"] = str(portal)
        second = build_portal(request)
        self.assertEqual(first.manifest, second.manifest)
        self.assertNotEqual(first.plan()["plan_sha256"], second.plan()["plan_sha256"])

    def test_project_paths_subdomains_and_non_pages_hosts_use_explicit_canonical_routes(self):
        for index, base in enumerate(("https://example.test/project/garden/", "https://notes.example.test/garden/", "https://static.example.test/docs/garden/")):
            with self.subTest(base=base):
                fixture = create_portal_fixture(self.root / str(index), base_uri=base)
                composition = build_portal(fixture["request"])
                self.assertEqual(composition.manifest["site"]["base_uri"], base)

    def test_clean_synthetic_proof_matches_golden_and_retains_occupied_workspace(self):
        specification = importlib.util.spec_from_file_location("synthetic_portal_demo", Path(__file__).parents[1] / "scripts/portal_demo.py")
        demo = importlib.util.module_from_spec(specification); specification.loader.exec_module(demo)
        report = demo.run_demo(self.root / "proof")
        expected = json.loads((Path(__file__).parent / "fixtures/portal-composition-expected.json").read_text())
        self.assertEqual(report, expected)
        with self.assertRaisesRegex(ValueError, "new or empty"): demo.run_demo(self.root / "proof")

    def test_cli_preview_apply_repeat_and_check_are_local_and_do_not_deploy(self):
        request = self.root / "request.json"; write_json(request, self.request)
        arguments = ["site", "compose", "--input", str(request)]
        with redirect_stdout(io.StringIO()) as output: self.assertEqual(main([*arguments, "--plan"]), 0)
        plan = json.loads(output.getvalue())
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([*arguments, "--apply", "--plan-digest", plan["plan_sha256"]]), 0)
            self.assertTrue(json.loads(output.getvalue())["applied"])
        with redirect_stdout(io.StringIO()): self.assertEqual(main([*arguments, "--check"]), 0)
        with redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["site", "compose", "--input", str(self.root / "private-path-canary"), "--diagnostic-format", "json"]), 3)
        self.assertNotIn("canary", errors.getvalue()); self.assertNotIn(str(self.root), errors.getvalue())


if __name__ == "__main__":
    unittest.main()
