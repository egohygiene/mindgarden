"""Reusable synthetic publication adversaries; no real gardens or render service."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timedelta
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.site_files import preview_server, read_site, write_site
from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.site import build_site
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.site import SITE_MARKER, verify_site
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.site_fixture import create_fixture
from tests.support_v1 import write_json

CASES = json.loads((Path(__file__).parent / "fixtures/publication-conformance/cases.json").read_text())


class PublicationConformanceTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root)
        self.context = self.fixture["context"]
        self.profile = self.fixture["profile"]

    def refresh(self):
        session = json.loads(self.fixture["session_path"].read_text())
        write_json(self.fixture["session_path"], bind_session_revisions(self.fixture["configuration"], session))
        self.context = QueryContext.load(self.fixture["configuration"], self.fixture["session_path"])
        index = build_index(self.context)
        self.profile["source_revision"] = index["inputs"][0]["revision"]
        self.profile["inputs"] = [record["reference"] for record in index["records"]]
        write_json(self.fixture["profile_path"], self.profile)

    def projection(self):
        return build_site(self.context, self.profile, profile_path=self.fixture["profile_path"])

    def rendered(self):
        projection = self.projection()
        files = {"index.html": b"<html>Reviewed public selection</html>"}
        files.update({route["path"]: b"<html>Exact reviewed evidence</html>" for route in projection.manifest["routes"]})
        plan = projection.plan(self.context, self.fixture["export"], operation="build", engine_directory=self.fixture["engine"])
        with patch("mindgarden.adapters.quartz.render_public_site", return_value=files):
            projection.apply(self.context, self.fixture["export"], plan["plan_sha256"], operation="build", engine_directory=self.fixture["engine"])
        return self.fixture["export"] / "garden", projection

    def test_leak_surface_matrix_uses_allowlists_before_reading_denied_bodies(self):
        canaries = CASES["canaries"]
        garden = self.fixture["workspace"] / ".garden"
        denied_path = garden / "knowledge/unreviewed.json"
        denied = json.loads(denied_path.read_text())
        denied.update(title=canaries["frontmatter"], tags=[canaries["index"]])
        denied["content"]["path"] = "../" + canaries["body"] + ".md"
        denied["x-attachment"] = {"path": canaries["attachment"], "link": "https://example.test/" + canaries["link"]}
        write_json(denied_path, denied)
        reviewed_path = garden / "knowledge/reviewed-prompt.json"
        reviewed = json.loads(reviewed_path.read_text())
        reviewed["review"]["rationale"] = canaries["metadata"]
        reviewed["x-private-control"] = canaries["metadata"]
        write_json(reviewed_path, reviewed)
        (garden / "sources/attachment.bin").write_bytes(canaries["attachment"].encode())
        self.refresh()
        before = garden_fingerprint(self.fixture["workspace"])
        read = Path.read_bytes
        def guarded(path):
            if path.name in {canaries["body"] + ".md", "attachment.bin", "unreviewed.md"}:
                raise AssertionError("Denied body was read")
            return read(path)
        with patch.object(Path, "read_bytes", guarded), patch("socket.socket", side_effect=AssertionError("Network attempted")):
            projection = self.projection()
        public = b"".join(projection.files.values())
        for value in [*canaries.values(), str(self.root), self.context.scope_digest()]:
            self.assertNotIn(value.encode(), public)
        self.assertEqual(before, garden_fingerprint(self.fixture["workspace"]))
        self.assertIn(b"lines:1-1", projection.files["notes/reviewed-prompt/index.md"])

    def test_engine_sibling_cache_never_overlaps_declared_denied_vault(self):
        for suffix in ("npm", "archive/nested"):
            with self.subTest(suffix=suffix):
                document = json.loads(self.fixture["configuration"].read_text())
                document["vaults"][0]["root"] = str(self.fixture["engine"].parent / suffix)
                write_json(self.fixture["configuration"], document)
                self.context = QueryContext.load(self.fixture["configuration"], self.fixture["session_path"])
                with self.assertRaisesRegex(ContractError, "SITE_ENGINE"):
                    self.projection().plan(self.context, self.fixture["export"], operation="build", engine_directory=self.fixture["engine"])
                self.assertFalse(self.fixture["engine"].parent.exists())

    def test_manifest_unknown_version_duplicate_routes_and_unsafe_paths_fail(self):
        projection = self.projection()
        for change, code in (("version", "SITE_INVALID"), ("duplicate", "SITE_ROUTE"), ("revision", "SITE_ROUTE"), ("route", "SITE_ROUTE")):
            files = deepcopy(projection.files); manifest = deepcopy(projection.manifest)
            if change == "version": manifest["schema"] = "mindgarden.site-manifest/v999"
            if change == "duplicate": manifest["routes"].append(deepcopy(manifest["routes"][0]))
            if change == "revision": manifest["routes"][0]["reference"]["revision"] = None
            if change == "route": manifest["routes"][0]["path"] = "index.html"
            files[SITE_MARKER] = canonical_json(manifest)
            with self.subTest(change=change), self.assertRaisesRegex(ContractError, code): verify_site(files)
        for name in ("../escape", "bad\nname", "bad?name", ".git/private", "a\\b"):
            with self.subTest(name=name), self.assertRaisesRegex(ContractError, "SITE_PATH"):
                verify_site({**projection.files, name: b"denied"})

    def test_missing_incomplete_and_directory_budget_are_not_success(self):
        with self.assertRaisesRegex(ContractError, "SITE_UNAVAILABLE"): read_site(self.root / "missing")
        with self.assertRaisesRegex(ContractError, "SITE_INCOMPLETE"): verify_site({})
        directory = self.root / "many-empty-directories"; directory.mkdir()
        for index in range(5): (directory / str(index)).mkdir()
        with patch("mindgarden.adapters.site_files.MAX_SITE_ENTRIES", 4), self.assertRaisesRegex(ContractError, "SITE_BUDGET"):
            read_site(directory)
        with self.assertRaisesRegex(ContractError, "SITE_OPERATION"):
            self.projection().plan(self.context, self.fixture["export"], operation="unknown")

    def test_preview_rechecks_authority_hashes_and_manifest_membership_per_request(self):
        directory, projection = self.rendered()
        live = {"allowed": True, "calls": 0}
        def check():
            live["calls"] += 1
            if not live["allowed"]: raise ContractError(CASES["canaries"]["error"])
            projection.check_live(self.context)
        server = preview_server(directory, projection.manifest["base_uri"], 0, check_live=check)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True); thread.start()
        try:
            url = "http://127.0.0.1:" + str(server.server_port) + "/garden/"
            with urlopen(url) as response:
                self.assertEqual(response.status, 200); self.assertEqual(response.headers["Cache-Control"], "no-store")
            with urlopen(Request(url, method="HEAD")) as response:
                self.assertEqual(response.status, 200); self.assertEqual(response.read(), b"")
            (directory / "private.txt").write_text(CASES["canaries"]["attachment"])
            for route in ("private.txt?" + CASES["canaries"]["error"], "%2e%2e/private.txt", ".mindgarden-site.json"):
                with self.assertRaises(HTTPError) as error: urlopen(url + route)
                self.assertEqual(error.exception.code, 404)
                self.assertNotIn(b"canary", error.exception.read())
                self.assertEqual(error.exception.headers["Cache-Control"], "no-store")
            (directory / "index.html").write_text(CASES["canaries"]["body"])
            with self.assertRaises(HTTPError) as error: urlopen(url)
            self.assertEqual(error.exception.code, 403); self.assertNotIn(b"canary", error.exception.read())
            (directory / "index.html").write_bytes(b"<html>Reviewed public selection</html>")
            bindings = json.loads(self.fixture["configuration"].read_text())
            bindings["revoked_sessions"] = [self.context.session["id"]]
            write_json(self.fixture["configuration"], bindings)
            with self.assertRaises(HTTPError) as error: urlopen(url)
            self.assertEqual(error.exception.code, 403); self.assertNotIn(b"canary", error.exception.read())
            bindings["revoked_sessions"] = []; write_json(self.fixture["configuration"], bindings)
            self.context.clock = lambda: datetime.fromisoformat(self.context.session["expires_at"].replace("Z", "+00:00")) + timedelta(seconds=1)
            with self.assertRaises(HTTPError) as error: urlopen(url)
            self.assertEqual(error.exception.code, 403)
            self.assertGreaterEqual(live["calls"], 6)
        finally:
            server.shutdown(); thread.join(); server.server_close()

    def test_hardlinked_or_symlinked_output_is_denied_without_modifying_target(self):
        directory, _projection = self.rendered()
        target = self.root / "private-attachment"; target.write_text(CASES["canaries"]["attachment"])
        page = directory / "index.html"; page.unlink(); os.link(target, page)
        with self.assertRaisesRegex(ContractError, "SITE_PATH"): read_site(directory)
        page.unlink(); page.symlink_to(target)
        with self.assertRaisesRegex(ContractError, "SITE_PATH"): read_site(directory)
        self.assertEqual(target.read_text(), CASES["canaries"]["attachment"])

    def test_renderer_cache_symlink_and_log_hardlink_are_denied_before_commands(self):
        from mindgarden.adapters.quartz import render_public_site
        engine = self.fixture["engine"]; engine.parent.mkdir(parents=True)
        private = self.root / "private-log"; private.write_text(CASES["canaries"]["build_log"])
        log = engine.parent / ".mindgarden-renderer.log"; os.link(private, log)
        projection = self.projection()
        with patch("mindgarden.adapters.quartz.require_executable"), patch("mindgarden.adapters.quartz.node_major_version", return_value=24), \
                patch("subprocess.run", side_effect=AssertionError("Renderer command attempted")):
            with self.assertRaisesRegex(ContractError, "SITE_PATH"): render_public_site(projection, engine)
            log.unlink(); (engine.parent / "npm").symlink_to(self.root, target_is_directory=True)
            with self.assertRaisesRegex(ContractError, "PATH_SYMLINK"): render_public_site(projection, engine)
        self.assertEqual(private.read_text(), CASES["canaries"]["build_log"])

    def test_shareable_cli_json_and_text_hide_missing_paths_and_process_logs(self):
        arguments = ["--repository-root", str(self.fixture["workspace"]), "--local-config", str(self.fixture["configuration"]),
                     "--scope", str(self.fixture["session_path"]), "--profile", str(self.root / CASES["canaries"]["error"])]
        for format in ("json", "text"):
            with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(main(["publish", "project", *arguments, "--diagnostic-format", format]), 3)
            self.assertEqual(output.getvalue(), "")
            self.assertNotIn(str(self.root), errors.getvalue()); self.assertNotIn("canary", errors.getvalue())
            if format == "json":
                report = json.loads(errors.getvalue())
                self.assertEqual(report["status"], "incomplete")
                self.assertEqual(report["diagnostics"][0]["code"], "SITE_UNAVAILABLE")
                self.assertEqual(report["diagnostics"][0]["location"], "publication")
        with patch("mindgarden.interfaces.cli.run_publication", side_effect=subprocess.CalledProcessError(1, [CASES["canaries"]["build_log"]])):
            # Handler identity is assigned by parser construction, exercising the
            # same sanitation boundary as a renderer subprocess failure.
            with redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(main(["publish", "project", *arguments, "--diagnostic-format", "json"]), 3)
            self.assertNotIn("canary", errors.getvalue())

    def test_interrupted_creation_rolls_back_only_its_own_files_and_can_retry(self):
        projection = self.projection(); destination = self.fixture["export"] / "garden"
        calls = 0
        def interrupted():
            nonlocal calls
            calls += 1
            if calls == 5: raise ContractError("SESSION_REVOKED: synthetic interrupted operation")
        human = self.fixture["export"] / "human.txt"; human.write_text("Preserve this caller file.\n")
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            write_site(destination, projection.files, check_live=interrupted, verify_inputs=lambda: None)
        self.assertFalse(destination.exists())
        self.assertEqual(human.read_text(), "Preserve this caller file.\n")
        self.assertTrue(write_site(destination, projection.files, check_live=lambda: None, verify_inputs=lambda: None))


if __name__ == "__main__":
    unittest.main()
