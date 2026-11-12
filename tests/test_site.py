"""Public v1 rendering shares selection, provenance and authority with retrieval."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.site_files import read_site
from mindgarden.adapters.quartz import accessible_navigation, canonical_navigation
from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.site import build_site
from mindgarden.domain.contracts import ContractRegistry
from mindgarden.domain.site import literal, verify_site
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.site_fixture import create_fixture
from tests.support_v1 import write_json
from tests import test_v1_contracts as contract_tests


class SiteTests(unittest.TestCase):
    def test_table_of_contents_controls_the_rendered_list(self):
        html = ('<html><body><article><div class="toc"><button class="toc-header" '
                'aria-controls="toc-1" aria-expanded="true">Contents</button>'
                '<ul id="list-0" class="toc-content overflow"><li>Evidence</li></ul>'
                '</div></article></body></html>')
        output = accessible_navigation(html)
        self.assertIn('aria-controls="list-0"', output)
        self.assertNotIn('aria-controls="toc-1"', output)

    def test_native_static_links_keep_canonical_routes_and_url_boundaries(self):
        html = ('<a href="../../notes/other/index?x=1&amp;y=2#evidence">note</a>'
                '<a href="/garden/relationships">graph</a>'
                '<a href="#content">section</a>'
                '<a href="https://elsewhere.example.test/notes/other/index">external</a>'
                '<a href="/outside/index">outside</a>')
        output = canonical_navigation(html, "notes/reviewed-prompt/index.html", "/garden/")
        self.assertIn('href="/garden/notes/other/?x=1&amp;y=2#evidence"', output)
        self.assertIn('href="/garden/relationships.html"', output)
        self.assertIn('href="#content"', output)
        self.assertIn('href="https://elsewhere.example.test/notes/other/index"', output)
        self.assertIn('href="/outside/index"', output)

    def setUp(self):
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root)
        self.context = self.fixture["context"]
        self.profile = self.fixture["profile"]

    def projection(self):
        return build_site(self.context, self.profile, profile_path=self.fixture["profile_path"])

    def test_public_content_has_exact_evidence_and_only_selected_typed_links(self):
        before = garden_fingerprint(self.fixture["workspace"])
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            projection = self.projection()
            plan = projection.plan(self.context, self.fixture["export"])
            self.assertTrue(projection.apply(self.context, self.fixture["export"], plan["plan_sha256"]))
            self.assertFalse(projection.apply(self.context, self.fixture["export"], plan["plan_sha256"]))
        files = read_site(self.fixture["export"] / "garden")
        verify_site(files)
        note = files["notes/reviewed-prompt/index.md"].decode()
        self.assertIn("supports: [[notes/reviewed-reference/index|reviewed-reference]]", note)
        self.assertIn(self.fixture["evidence"][0]["source"]["revision"], note)
        self.assertIn("lines:1-1", note)
        for canary in ("unreviewed-body-canary", "hidden-garden-canary", "hidden-root-canary", "private-review-rationale-canary", str(self.root)):
            self.assertNotIn(canary.encode(), b"".join(files.values()))
        self.assertEqual(before, garden_fingerprint(self.fixture["workspace"]))
        self.assertEqual(len(projection.manifest["routes"]), 3)

    def test_projection_and_plan_match_reference_schemas(self):
        projection = self.projection()
        contract_tests.V1ContractTests.setUpClass(); reference = contract_tests.V1ContractTests()
        for name, document in (("site-adapter", projection.settings), ("site-manifest", projection.manifest),
                                ("site-plan", projection.plan(self.context, self.fixture["export"]))):
            with self.subTest(contract=name):
                self.assertEqual(ContractRegistry().errors(document, name), [])
                self.assertEqual(list(reference.validator(name).iter_errors(document)), [])

    def test_empty_selection_is_useful_and_contains_no_omitted_counts(self):
        self.profile["inputs"] = []
        write_json(self.fixture["profile_path"], self.profile)
        projection = self.projection()
        self.assertEqual(projection.manifest["routes"], [])
        self.assertIn(b"No reviewed notes have been selected", projection.files["index.md"])
        self.assertNotIn(b"reviewed-prompt", b"".join(projection.files.values()))

    def test_unsafe_body_markup_and_fences_remain_literal_content(self):
        value = '<script>window.canary = true</script>\n```\n![tracking](https://example.test/pixel)\n'
        quoted = literal(value)
        self.assertTrue(quoted.startswith("````text\n"))
        self.assertTrue(quoted.endswith("````\n"))
        self.assertIn(value.rstrip(), quoted)

    def test_stale_profile_digest_and_existing_corruption_never_overwrite(self):
        projection = self.projection()
        plan = projection.plan(self.context, self.fixture["export"])
        with self.assertRaisesRegex(ContractError, "SITE_PLAN_STALE"):
            projection.apply(self.context, self.fixture["export"], "0" * 64)
        self.assertEqual(list(self.fixture["export"].iterdir()), [])
        projection.apply(self.context, self.fixture["export"], plan["plan_sha256"])
        page = self.fixture["export"] / "garden/index.md"; page.write_text("Unowned modified output")
        with self.assertRaisesRegex(ContractError, "SITE_INTEGRITY"):
            projection.apply(self.context, self.fixture["export"], plan["plan_sha256"])
        self.assertEqual(page.read_text(), "Unowned modified output")
        self.profile["x-site"]["title"] = "Changed reviewed title"
        write_json(self.fixture["profile_path"], self.profile)
        with self.assertRaisesRegex(ContractError, "SITE_PLAN_STALE"):
            projection.apply(self.context, self.fixture["export"], plan["plan_sha256"])

    def test_unsupported_adapter_scope_and_canonical_output_are_denied(self):
        profile = deepcopy(self.profile); profile["x-site"]["repository"] = "https://unreviewed.example.test/renderer.git"
        with self.assertRaisesRegex(ContractError, "SITE_PROFILE"):
            build_site(self.context, profile)
        with self.assertRaisesRegex(ContractError, "FEDERATION_OUTPUT"):
            self.projection().plan(self.context, self.fixture["workspace"] / ".garden")
        external = self.root / "external-cache"; external.mkdir()
        cache = self.fixture["workspace"] / ".cache"; cache.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ContractError, "SITE_ENGINE"):
            self.projection().plan(self.context, self.fixture["export"], operation="build", engine_directory=self.fixture["engine"])
        self.context.session["request_scope"]["visibility"] = "personal"
        with self.assertRaisesRegex(ContractError, "FEDERATION_SCOPE"):
            self.projection()

    def test_build_uses_pinned_adapter_once_and_checks_existing_outputs_offline(self):
        projection = self.projection()
        files = {"index.html": b"<html>Reviewed garden</html>"}
        files.update({route["path"]: b"<html>Exact evidence</html>" for route in projection.manifest["routes"]})
        plan = projection.plan(self.context, self.fixture["export"], operation="build", engine_directory=self.fixture["engine"])
        with patch("mindgarden.adapters.quartz.render_public_site", return_value=files) as renderer:
            self.assertTrue(projection.apply(self.context, self.fixture["export"], plan["plan_sha256"], operation="build", engine_directory=self.fixture["engine"]))
            self.assertFalse(projection.apply(self.context, self.fixture["export"], plan["plan_sha256"], operation="build", engine_directory=self.fixture["engine"]))
        self.assertEqual(renderer.call_count, 1)
        manifest = verify_site(read_site(self.fixture["export"] / "garden"))
        self.assertEqual(manifest["renderer"]["commit"], projection.settings["commit"])

    def test_cli_plan_apply_and_verify_use_the_normal_commands(self):
        shared = ["--repository-root", str(self.fixture["workspace"]), "--profile", str(self.fixture["profile_path"]),
                  "--local-config", str(self.fixture["configuration"]), "--scope", str(self.fixture["session_path"]),
                  "--output-directory", str(self.fixture["export"])]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["publish", "project", *shared, "--plan"]), 0)
        plan = json.loads(output.getvalue())
        self.assertEqual(list(self.fixture["export"].iterdir()), [])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["publish", "project", *shared, "--apply", "--plan-digest", plan["plan_sha256"]]), 0)
            self.assertEqual(main(["publish", "verify", *shared]), 0)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["site", "build", "--repository-root", str(self.fixture["workspace"])]), 3)
        self.assertIn("SCOPE_REQUIRED", errors.getvalue())

    def test_offline_demo_matches_committed_proof_and_preserves_occupied_workspaces(self):
        specification = importlib.util.spec_from_file_location("synthetic_site_demo", Path(__file__).parents[1] / "scripts/site_demo.py")
        demo = importlib.util.module_from_spec(specification); specification.loader.exec_module(demo)
        report = demo.run_demo(self.root / "demo")
        self.assertEqual(report, json.loads((Path(__file__).parent / "fixtures/site/expected-proof.json").read_text()))
        occupied = self.root / "human-workspace"; occupied.mkdir()
        marker = occupied / "human.txt"; marker.write_text("Keep this synthetic file.\n")
        with self.assertRaisesRegex(ValueError, "new or empty"):
            demo.run_demo(occupied)
        self.assertEqual(marker.read_text(), "Keep this synthetic file.\n")


if __name__ == "__main__":
    unittest.main()
