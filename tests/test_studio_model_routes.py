"""The model lab is an explicit fictional visit with a closed HTTP boundary."""

from contextlib import closing, redirect_stderr
from http.client import HTTPConnection
from io import StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.domain.contracts import canonical_json, read_object
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import ExitCode, main
from mindgarden.interfaces.local_web import make_server
from mindgarden.interfaces.visit_demo import prepare_demo


class StudioModelRoutesTests(unittest.TestCase):
    def setUp(self):
        workspace = TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.workspace = Path(workspace.name).resolve()
        self.config, self.scope = prepare_demo(self.workspace, assistant=True)
        self.lab = Mock(spec=["snapshot", "check", "preview", "run", "install_preview", "install"])

    def launch(self, assistant="providers"):
        with (
            patch("mindgarden.interfaces.local_web.browser_assets", return_value={}),
            patch("mindgarden.application.model_lab.ModelLab", return_value=self.lab) as construct,
        ):
            self.server = make_server(self.config, self.scope, demo=True, interface="studio", assistant=assistant)
            if assistant == "providers":
                construct.assert_called_once_with()
            else:
                construct.assert_not_called()
        self.addCleanup(self.server.server_close)
        worker = Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.025}, daemon=True)
        worker.start()
        self.addCleanup(worker.join, 5)
        self.addCleanup(self.server.shutdown)

    def request(self, path, *, payload=None, status=200, headers=None, authorized=True):
        method = "GET" if payload is None else "POST"
        default_headers = {}
        if authorized:
            default_headers["Authorization"] = "Bearer " + self.server.access_token
        if method == "POST":
            default_headers.update({"Origin": self.server.origin, "Content-Type": "application/json"})
        default_headers.update(headers or {})
        content = canonical_json(payload) if payload is not None else None
        with closing(HTTPConnection(*self.server.server_address, timeout=15)) as connection:
            connection.request(method, path, content, default_headers)
            response = connection.getresponse()
            raw = response.read()
            self.assertEqual(response.status, status, raw)
            self.assertEqual(response.getheader("Cache-Control"), "no-store")
            self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))
            self.assertNotIn(str(self.workspace).encode(), raw)
            self.assertNotIn(b"private-canary", raw)
            return json.loads(raw)

    def error(self, path, code, status, **arguments):
        self.assertEqual(self.request(path, status=status, **arguments)["error"]["code"], code)

    def test_model_mode_is_denied_outside_explicit_demo_studio_before_setup(self):
        for arguments in (["--demo", "--workspace", "fictional"],
                          ["--local-config", "bindings.json", "--scope", "scope.json", "--interface", "studio"]):
            with (
                self.subTest(arguments=arguments),
                patch("mindgarden.interfaces.local_web.browser_assets") as assets,
                patch("mindgarden.interfaces.visit_demo.prepare_demo") as prepare,
                patch("mindgarden.interfaces.local_web.serve_garden") as serve,
                redirect_stderr(StringIO()) as diagnostics,
            ):
                status = main(["visit", *arguments, "--assistant", "providers"])
                self.assertEqual(status, ExitCode.CONTRACT)
                self.assertIn("--assistant providers with --demo --interface studio", diagnostics.getvalue())
                assets.assert_not_called()
                prepare.assert_not_called()
                serve.assert_not_called()
        with self.assertRaisesRegex(ContractError, "VISIT_ASSISTANT"):
            make_server(self.config, self.scope, demo=False, interface="studio", assistant="providers")

    def test_explicit_provider_launch_retains_prepared_fictional_scope(self):
        with (
            patch("mindgarden.interfaces.local_web.browser_assets") as assets,
            patch("mindgarden.interfaces.visit_demo.prepare_demo", return_value=(self.config, self.scope)) as prepare,
            patch("mindgarden.interfaces.local_web.serve_garden", return_value=0) as serve,
        ):
            result = main(["visit", "--demo", "--workspace", str(self.workspace), "--interface", "studio",
                           "--assistant", "providers"])
            self.assertEqual(result, ExitCode.SUCCESS)
            assets.assert_called_once_with("studio")
            prepare.assert_called_once_with(self.workspace, assistant=True)
            serve.assert_called_once_with(self.config, self.scope, port=0, demo=True,
                                          interface="studio", assistant="providers")

    def test_fixture_mode_does_not_instantiate_or_expose_lab(self):
        self.launch("fixture")
        self.assertFalse(self.request("/api/garden")["capabilities"]["models"])
        self.error("/api/models", "WEB_NOT_FOUND", 404)
        self.error("/api/models/check", "WEB_METHOD", 405, payload={"provider": "ollama"})
        self.assertEqual(self.lab.mock_calls, [])

    def test_cached_status_and_actions_are_bounded_to_exact_synthetic_fields(self):
        self.launch()
        capabilities = self.request("/api/garden")["capabilities"]
        for capability in ("assistant", "booklet", "models"):
            self.assertTrue(capabilities[capability])
        self.lab.snapshot.return_value = {"providers": []}
        self.assertEqual(self.request("/api/models"), {"providers": []})
        self.lab.snapshot.assert_called_once_with()
        self.lab.check.assert_not_called()
        self.lab.run.assert_not_called()

        model = {"provider": "ollama", "model": "tiny-fixture"}
        download = {"model": "tiny-fixture"}
        digest = "a" * 64
        self.error("/api/models/install", "MODEL_INVALID", 400, payload=download)
        self.error("/api/models/install/preview", "MODEL_INVALID", 400, payload={**download, "preview_sha256": digest})
        self.lab.install.assert_not_called()
        self.lab.install_preview.assert_not_called()
        for route, operation, payload in (
            ("check", "check", {"provider": "ollama"}),
            ("preview", "preview", model),
            ("run", "run", {**model, "preview_sha256": digest}),
            ("install/preview", "install_preview", download),
            ("install", "install", {**download, "preview_sha256": digest}),
        ):
            with self.subTest(operation=operation):
                action = getattr(self.lab, operation)
                action.return_value = {"confirmed": operation}
                path = "/api/models/" + route
                self.error(path, "MODEL_INVALID", 400, payload={**payload, "question": "private-canary"})
                action.assert_not_called()
                self.assertEqual(self.request(path, payload=payload), {"confirmed": operation})
                action.assert_called_once_with(payload)

        preview = self.request("/api/assistant/preview", payload={
            "lens": "garden", "question": "accessibility", "focus": "synthetic-garden/mock-career",
        })
        self.assertEqual(preview["provider"], "fixture")
        self.assertEqual(preview["records"][0]["reference"]["id"], "mock-career")
        booklet = self.request("/api/booklet/preview", payload={"month": "2026-01"})
        self.assertEqual(booklet["totals"][0]["net_movement"], "2259.76")

    def test_models_endpoints_keep_the_existing_browser_authority_and_errors_opaque(self):
        self.launch()
        path = "/api/models/check"
        payload = {"provider": "gemini"}
        self.error("/api/models", "WEB_ACCESS", 403, authorized=False)
        self.error("/api/models", "WEB_ORIGIN", 403, headers={"Sec-Fetch-Site": "cross-site"})
        self.error(path, "WEB_ACCESS", 403, payload=payload, authorized=False)
        for headers in ({"Host": "other.invalid"}, {"Origin": "https://other.invalid"}, {"Origin": ""}):
            self.error(path, "WEB_ORIGIN", 403, payload=payload, headers=headers)
        self.error(path + "?question=private-canary", "WEB_METHOD", 405, payload=payload)
        self.error(path, "MODEL_INVALID", 400, payload={"provider": ["gemini"]})
        self.error(path, "MODEL_INVALID", 400, payload={**payload, "api_key": "private-canary"})
        self.lab.check.assert_not_called()
        for status, code in ((409, "MODEL_BUSY"), (409, "MODEL_REVIEW"), (429, "MODEL_QUOTA"),
                             (503, "MODEL_NOT_CONFIGURED"), (503, "MODEL_UNAVAILABLE"), (503, "WEB_UNAVAILABLE")):
            self.lab.check.side_effect = ContractError(f"{code}: private-canary")
            self.error(path, code, status, payload=payload)

    def test_changed_view_prevents_dispatch_and_revocation_discards_returned_data(self):
        self.launch()
        payload = {"provider": "codex"}
        garden = Path(read_object(self.config)["gardens"][0]["root"])
        changed = garden / ".garden/knowledge/mock-career.json"
        original = changed.read_bytes()
        changed.write_bytes(canonical_json({**read_object(changed), "title": "Changed visible title"}))
        self.error("/api/models", "SESSION_REVISION", 409)
        self.error("/api/models/check", "SESSION_REVISION", 409, payload=payload)
        self.lab.snapshot.assert_not_called()
        self.lab.check.assert_not_called()
        changed.write_bytes(original)

        def revoke(_selection):
            config = read_object(self.config)
            config["revoked_sessions"] = [read_object(self.scope)["id"]]
            self.config.write_bytes(canonical_json(config))
            return {"result": "private-canary"}

        self.lab.check.side_effect = revoke
        self.error("/api/models/check", "SESSION_REVOKED", 403, payload=payload)
        self.lab.check.assert_called_once_with(payload)
        self.error("/api/models", "SESSION_REVOKED", 403)
        self.lab.snapshot.assert_not_called()
