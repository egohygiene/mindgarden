"""Loopback browser parity and defensive authorization checks with synthetic records."""

from contextlib import redirect_stderr
from dataclasses import replace
from http.client import HTTPConnection
from io import StringIO
import json
from pathlib import Path
import sys
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.connector_evidence import connector_evidence
from mindgarden.application.drive_capture import collect
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index, search_payload
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import ExitCode, main
from mindgarden.interfaces.local_web import browser_assets, make_server
from tests import test_v1_retrieval as retrieval_tests
from tests.consultation_fixture import cli
from tests.mapped_drive_fixture import create_fixture, ingest_arguments
from tests.support_v1 import add_knowledge, write_json, write_session


class LocalWebTests(unittest.TestCase):
    def setUp(self):
        retrieval_tests.RetrievalTests.setUp(self)

    def start_server(self, *, interface="classic", demo=True, **session_updates):
        if session_updates:
            session = json.loads(self.session_path.read_bytes())
            session.update(session_updates)
            write_json(self.session_path, bind_session_revisions(self.configuration, session))
        self.server = make_server(self.configuration, self.session_path, demo=demo, interface=interface)
        self.addCleanup(self.server.server_close)
        thread = Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.025}, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(self.server.shutdown)

    def request(self, path, status=200, *, method="GET", headers=None, authorize=True):
        request_headers = {"Authorization": "Bearer " + self.server.access_token} if authorize else {}
        request_headers.update(headers or {})
        connection = HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request(method, path, headers=request_headers)
            response = connection.getresponse()
            content = response.read()
            self.assertEqual(response.status, status, content)
            self.assertEqual(response.getheader("Cache-Control"), "no-store")
            self.assertEqual(response.getheader("Cross-Origin-Resource-Policy"), "same-origin")
            self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))
            self.assertNotIn(str(self.root).encode(), content)
            self.assertNotIn(b"unreviewed-unique-marker", content)
            if content and response.getheader("Content-Type").startswith("application/json"):
                return json.loads(content)
            return content
        finally:
            connection.close()

    def test_bearer_origin_methods_and_allowlisted_static_assets(self):
        self.start_server()
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        self.assertIn(b"<!doctype html>", self.request("/", authorize=False))
        self.assertEqual(self.request("/garden.css", method="HEAD", authorize=False), b"")
        for path in ("/garden.json", "/%2e%2e/garden.json", "/web/index.html", "/.git/config"):
            with self.subTest(path=path):
                self.request(path, 404, authorize=False)
        self.assertEqual(self.request("/api/garden", 403, authorize=False)["error"]["code"], "WEB_ACCESS")
        for headers in ({"Host": "example.invalid"}, {"Origin": "https://example.invalid"},
                        {"Sec-Fetch-Site": "cross-site"}, {"Sec-Fetch-Site": "same-site"}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request("/api/garden", 403, headers=headers)["error"]["code"], "WEB_ORIGIN")
        for method in ("POST", "PUT", "DELETE", "OPTIONS"):
            with self.subTest(method=method):
                self.assertEqual(self.request("/api/garden", 405, method=method)["error"]["code"], "WEB_METHOD")

    def studio_bundle(self):
        browser_files = self.root / "browser-assets"
        studio = browser_files / "studio"
        files = {
            "garden.css": b"/* Classic reader */",
            "garden-icon.svg": b"<svg></svg>",
            "studio/index.html": b"<!doctype html><title>Example Studio</title>",
            "studio/.vite/license.md": b"Notices for the compiled fixture",
            "studio/assets/index-01eA23f4.js": b"/* Studio entry */",
            "studio/assets/_view-81f92b03.js": b"/* Studio chunk */",
            "studio/assets/index-6789ab01.css": b"/* Studio styles */",
            "studio/assets/cover-0239abdf.webp": b"Synthetic fixture placeholder",
            "studio/assets/orphan-abc112de.js": b"Undeclared asset",
        }
        for relative, content in files.items():
            path = browser_files / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        manifest = {
            "index.html": {
                "file": "assets/index-01eA23f4.js", "isEntry": True,
                "css": ["assets/index-6789ab01.css"], "assets": ["assets/cover-0239abdf.webp"],
            },
            "_view.js": {"file": "assets/_view-81f92b03.js"},
        }
        write_json(studio / ".vite/manifest.json", manifest)
        return browser_files, manifest

    def test_studio_uses_manifest_routes_and_existing_api_authority(self):
        browser_files, _ = self.studio_bundle()
        with patch("mindgarden.interfaces.local_web.ASSETS", browser_files):
            self.start_server(interface="studio")
            self.assertIn(b"Example Studio", self.request("/", authorize=False))
            for path in ("/assets/index-01eA23f4.js", "/assets/_view-81f92b03.js", "/assets/index-6789ab01.css",
                         "/assets/cover-0239abdf.webp", "/garden-icon.svg"):
                with self.subTest(path=path):
                    self.request(path, authorize=False)
            for path in ("/assets/orphan-abc112de.js", "/studio/.vite/manifest.json", "/studio/.vite/license.md",
                         "/.vite/license.md", "/assets/../garden.css",
                         "/assets/%2e%2e/garden.css", "/studio/assets/index-01eA23f4.js", "/garden.css"):
                with self.subTest(path=path):
                    self.request(path, 404, authorize=False)
            self.request("/api/garden", 403, authorize=False)
            self.assertEqual(self.request("/api/garden")["title"], "Willow Garden")

    def test_studio_missing_build_reports_setup_without_initializing_demo(self):
        workspace = self.root / "new-demo"
        output = StringIO()
        with patch("mindgarden.interfaces.local_web.ASSETS", self.root / "no-studio"), redirect_stderr(output):
            result = main(["visit", "--demo", "--workspace", str(workspace), "--interface", "studio"])
        self.assertEqual(result, ExitCode.CONTRACT)
        self.assertIn("VISIT_STUDIO_UNAVAILABLE", output.getvalue())
        self.assertIn("npm --prefix web run build", output.getvalue())
        self.assertFalse(workspace.exists())

    def test_studio_rejects_manifest_paths_outside_its_bundle(self):
        browser_files, manifest = self.studio_bundle()
        with patch("mindgarden.interfaces.local_web.ASSETS", browser_files):
            for filename in ("../garden.css", "/garden.css", "assets/index.js", "assets/cover-0239abdf.webp.map"):
                with self.subTest(filename=filename):
                    manifest["index.html"]["file"] = filename
                    write_json(browser_files / "studio/.vite/manifest.json", manifest)
                    with self.assertRaisesRegex(ContractError, "VISIT_STUDIO_INVALID"):
                        browser_assets("studio")

    def test_authorized_search_detail_context_graph_and_exact_evidence(self):
        self.start_server()
        garden = self.request("/api/garden")
        self.assertEqual(garden["title"], "Willow Garden")
        self.assertEqual(len(garden["notes"]), 3)
        self.assertEqual(garden["graph"]["edges"][0]["type"], "supports")
        actual_search = self.request("/api/search?q=prompt")
        expected_search = search_payload(QueryContext.load(self.configuration, self.session_path), "prompt")
        self.assertEqual(actual_search, expected_search)
        detail = self.request("/api/note?ref=synthetic-garden/synthetic-prompt")
        note = detail["note"]
        self.assertEqual(note["review"]["state"], "approved")
        self.assertEqual(note["sources"], actual_search["results"][0]["sources"])
        self.assertEqual(detail["links"][0]["to"], "synthetic-garden/second-note")
        second = self.request("/api/note?ref=synthetic-garden/second-note")
        self.assertEqual(second["backlinks"][0]["from"], "synthetic-garden/synthetic-prompt")
        evidence = self.request("/api/evidence?ref=synthetic-garden/synthetic-prompt&citation=0")
        self.assertEqual({key: evidence[key] for key in note["sources"][0]}, note["sources"][0])
        self.assertEqual(digest_bytes(evidence["text"].encode()), evidence["content_sha256"])
        pack = self.request("/api/context?q=prompt")
        entry = next(item for item in pack["included"] if item["reference"] == note["reference"])
        self.assertEqual(entry["sources"], note["sources"])
        self.assertEqual(pack["trust"], "untrusted-evidence")
        self.assertLessEqual(len(pack["included"]), 5)

    def test_denied_records_are_absent_and_requests_remain_bounded(self):
        self.start_server()
        self.assertEqual(self.request("/api/search?q=unreviewed-unique-marker")["results"], [])
        self.assertEqual(self.request("/api/context?q=unreviewed-unique-marker")["included"], [])
        for operation, suffix in (("note", ""), ("evidence", "&citation=0")):
            with self.subTest(operation=operation):
                base = f"/api/{operation}?ref=synthetic-garden/"
                denied = self.request(base + "unreviewed-note" + suffix, 404)
                missing = self.request(base + "missing-note" + suffix, 404)
                self.assertEqual(denied, missing)
        for path in ("/api/search", "/api/search?q=one&q=two", "/api/context?q=%FF",
                     "/api/search?" + urlencode({"q": "x" * 257}), "/api/note?ref=../private",
                     "/api/evidence?ref=synthetic-garden/synthetic-prompt&citation=-1"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path, 400)["error"]["code"], "WEB_QUERY")

    def test_connector_status_is_fictional_and_uses_distinct_visible_citations(self):
        self.start_server()
        self.assertEqual(self.request("/api/connectors", 403, authorize=False)["error"]["code"], "WEB_ACCESS")
        self.assertEqual(self.request("/api/connectors?provider=any", 400)["error"]["code"], "WEB_QUERY")
        self.assertEqual(self.request("/api/connectors"), {
            "google_drive": {"state": "demo", "citation_count": 0},
            "local_vault": {"state": "visible-evidence", "citation_count": 1},
        })

    def test_connector_status_ignores_unknown_and_unverified_provider_markers(self):
        source_files = sorted((self.workspace / ".garden/sources").glob("*.json"))
        for alleged_adapter in ("unknown-provider", "drive-capture"):
            with self.subTest(alleged_adapter=alleged_adapter):
                for path in source_files:
                    source = json.loads(path.read_bytes())
                    source["origin"] = "https://drive.google.com/drive/folders/fictional-canary"
                    if source["kind"] == "captured":
                        source["media_type"] = "application/vnd.mindgarden.drive-capture+zip"
                    source["x-adapter"] = {
                        "id": alleged_adapter if source["kind"] == "normalized" else "drive-capture",
                        "version": "1.0.0",
                        "manifest_version": "1.0.0",
                        "metadata": {
                            "provider": "google-drive-v3", "provider_file_id": "fictional-canary",
                            "captured_scope": local_scope(execution="controlled-import", publication="never-exportable"),
                        },
                    }
                    write_json(path, source)
                write_session(self.session_path, self.configuration)
                self.start_server(demo=False)
                self.assertEqual(self.request("/api/connectors"), {
                    "google_drive": {"state": "setup-required", "citation_count": 0},
                    "local_vault": {"state": "visible-evidence", "citation_count": 1},
                })

    def test_connector_status_replays_synthetic_drive_lineage_within_overview_budget(self):
        fixture = create_fixture(self.root / "drive-provider")
        raw, _ = collect(fixture["binding"], fixture["provider"], fixture["vault"], self.root / "drive-checkpoint.json")
        arguments = ingest_arguments(fixture, raw)
        plan = cli(arguments)
        cli(arguments + ["--apply", "--plan-digest", plan["plan_sha256"]])
        first, second, *_ = plan["inputs"]["normalized_sources"]
        garden = fixture["garden"]
        add_knowledge(garden, "a-overview-first")
        add_knowledge(garden, "b-visible-drive", sources=first["evidence"])
        add_knowledge(garden, "c-visible-drive-duplicate", sources=first["evidence"])
        add_knowledge(garden, "d-hidden-drive", reviewed=False, sources=second["evidence"])
        self.configuration = fixture["configuration"]
        self.session_path = self.root / "drive-session.json"
        session = write_session(self.session_path, self.configuration)
        with patch("mindgarden.application.drive_capture.GoogleDriveProvider", side_effect=AssertionError("Live probe attempted")):
            self.start_server(demo=False, budgets={**session["budgets"], "max_results": 1})
            self.assertEqual(self.request("/api/connectors"), {
                "google_drive": {"state": "setup-required", "citation_count": 0},
                "local_vault": {"state": "no-visible-evidence", "citation_count": 0},
            })
            self.start_server(demo=False, budgets=session["budgets"])
            self.assertEqual(self.request("/api/connectors"), {
                "google_drive": {"state": "captured", "citation_count": 1},
                "local_vault": {"state": "visible-evidence", "citation_count": 1},
            })
        context = QueryContext.load(self.configuration, self.session_path)
        records = build_index(context, projection="evidence")["records"]
        snapshots = context.snapshots()
        garden_id = first["source"]["garden"]
        snapshot = snapshots[garden_id]
        source = snapshot.records[first["source"]["id"]]
        capture_id = source["inputs"][0]["id"]
        provenance_id = source["provenance"][0]["id"]
        for absent in (capture_id, provenance_id):
            with self.subTest(absent=absent):
                incomplete = replace(snapshot, records={key: value for key, value in snapshot.records.items() if key != absent})
                with patch.object(context, "snapshots", return_value={garden_id: incomplete}):
                    self.assertEqual(connector_evidence(context, records, demo=False)["google_drive"], {
                        "state": "setup-required", "citation_count": 0,
                    })

    def test_scope_changes_and_revocation_fail_closed(self):
        self.start_server()
        self.request("/api/garden")
        configuration = json.loads(self.configuration.read_bytes())
        session = json.loads(self.session_path.read_bytes())
        write_json(self.configuration, {**configuration, "revoked_sessions": [session["id"]]})
        self.assertEqual(self.request("/api/search?q=prompt", 403)["error"]["code"], "SESSION_REVOKED")
        self.assertEqual(self.request("/api/connectors", 403)["error"]["code"], "SESSION_REVOKED")
        write_json(self.configuration, configuration)
        write_json(self.session_path, {**session, "allowed_review_states": ["approved", "unreviewed"]})
        self.assertEqual(self.request("/api/garden", 403)["error"]["code"], "SESSION_STALE")

    def test_disabled_projections_and_session_limits_are_enforced(self):
        self.start_server(projections=["index"], budgets={**self.context.session["budgets"], "max_results": 1})
        overview = self.request("/api/garden")
        self.assertTrue(overview["limited"])
        self.assertEqual(len(overview["notes"]), 1)
        self.assertEqual(overview["graph"], {"nodes": [], "edges": []})
        detail = self.request("/api/note?ref=synthetic-garden/synthetic-prompt")
        self.assertEqual((detail["links"], detail["backlinks"]), ([], []))
        for path in ("/api/search?q=prompt", "/api/context?q=prompt", "/api/connectors",
                     "/api/evidence?ref=synthetic-garden/synthetic-prompt&citation=0"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path, 403)["error"]["code"], "PROJECTION_DENIED")
