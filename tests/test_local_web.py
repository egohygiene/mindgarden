"""Loopback browser parity and defensive authorization checks with synthetic records."""

from http.client import HTTPConnection
import json
from pathlib import Path
import sys
from threading import Thread
import unittest
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import search_payload
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import digest_bytes
from mindgarden.interfaces.local_web import make_server
from tests import test_v1_retrieval as retrieval_tests
from tests.support_v1 import write_json


class LocalWebTests(unittest.TestCase):
    def setUp(self):
        retrieval_tests.RetrievalTests.setUp(self)

    def start_server(self, **session_updates):
        if session_updates:
            session = json.loads(self.session_path.read_bytes())
            session.update(session_updates)
            write_json(self.session_path, bind_session_revisions(self.configuration, session))
        self.server = make_server(self.configuration, self.session_path, demo=True)
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

    def test_scope_changes_and_revocation_fail_closed(self):
        self.start_server()
        self.request("/api/garden")
        configuration = json.loads(self.configuration.read_bytes())
        session = json.loads(self.session_path.read_bytes())
        write_json(self.configuration, {**configuration, "revoked_sessions": [session["id"]]})
        self.assertEqual(self.request("/api/search?q=prompt", 403)["error"]["code"], "SESSION_REVOKED")
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
        for path in ("/api/search?q=prompt", "/api/context?q=prompt",
                     "/api/evidence?ref=synthetic-garden/synthetic-prompt&citation=0"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path, 403)["error"]["code"], "PROJECTION_DENIED")
