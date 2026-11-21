"""Prove the explicit ChatGPT profile is usable only in the fictional Models lab."""

from contextlib import closing, redirect_stderr
from http.client import HTTPConnection
from io import StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from time import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.chatgpt_credentials import ChatGPTCredentials, ChatGPTStore
from mindgarden.application.model_lab import PROMPT
from mindgarden.interfaces.cli import ExitCode, main
from mindgarden.interfaces.local_web import make_server
from mindgarden.interfaces.visit_demo import prepare_demo


class StudioChatGPTVisitTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.state = self.root / "consent"

    def test_cli_passes_profile_only_to_the_explicit_providers_demo(self):
        workspace = self.root / "garden-demo"
        base = ["visit", "--demo", "--interface", "studio", "--workspace", str(workspace),
                "--chatgpt-state-directory", str(self.state)]
        config, scope = self.root / "demo-config.json", self.root / "session.json"
        with (
            patch("mindgarden.interfaces.local_web.browser_assets") as assets,
            patch("mindgarden.interfaces.visit_demo.prepare_demo", return_value=(config, scope)) as prepare,
            patch("mindgarden.interfaces.local_web.serve_garden", return_value=0) as serve,
            redirect_stderr(StringIO()),
        ):
            self.assertEqual(main([*base, "--assistant", "fixture"]), ExitCode.CONTRACT)
            self.assertEqual(main(["visit", "--local-config", str(config), "--scope", str(scope),
                                   "--chatgpt-state-directory", str(self.state)]), ExitCode.CONTRACT)
            assets.assert_not_called()
            prepare.assert_not_called()
            serve.assert_not_called()
            self.assertEqual(main([*base, "--assistant", "providers"]), ExitCode.SUCCESS)
            serve.assert_called_once_with(config, scope, port=0, demo=True, interface="studio",
                                          assistant="providers", chatgpt_state_directory=self.state)

    def test_checked_profile_runs_exact_fixture_and_disconnect_clears_cached_catalog(self):
        store = ChatGPTStore(self.state)
        store.save(ChatGPTCredentials(
            issuer="https://auth.openai.com",
            subject="synthetic-studio-subject",
            client_id="oaiapp_studio_fixture",
            scopes=("chatgpt.tokens.use.direct", "resource.invoke"),
            access_token="fixture-secret-access",
            refresh_token="fixture-secret-renewal",
            id_token="fixture-secret-identity",
            expires_at=int(time()) + 3_600,
        ))
        endpoint = Mock()
        endpoint.models.return_value = {"models": [
            {"visibility": "list", "slug": "studio-plan-fixture", "display_name": "Studio fixture"},
        ]}
        endpoint.infer.return_value = "Reviewed fictional result [S1]."
        config, scope = prepare_demo(self.root / "visit", assistant=True)
        with (
            patch("mindgarden.interfaces.local_web.browser_assets", return_value={}),
            patch("mindgarden.adapters.studio_chatgpt._ChatGPTEndpoint", return_value=endpoint),
            make_server(config, scope, demo=True, interface="studio", assistant="providers",
                        chatgpt_state_directory=self.state) as server,
        ):
            worker = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
            worker.start()
            try:
                def request(path, payload=None, status=200):
                    headers = {"Authorization": "Bearer " + server.access_token}
                    body = None
                    if payload is not None:
                        headers.update({"Origin": server.origin, "Content-Type": "application/json"})
                        body = json.dumps(payload)
                    with closing(HTTPConnection(*server.server_address, timeout=15)) as http:
                        http.request("GET" if payload is None else "POST", path, body, headers)
                        reply = http.getresponse()
                        raw = reply.read()
                        self.assertEqual(reply.status, status, raw)
                        self.assertEqual(reply.getheader("Cache-Control"), "no-store")
                        self.assertNotIn(b"fixture-secret", raw)
                        self.assertNotIn(b"synthetic-studio-subject", raw)
                        self.assertNotIn(str(self.state).encode(), raw)
                        return json.loads(raw)

                snapshot = request("/api/models")
                self.assertEqual([item["id"] for item in snapshot["providers"]], ["chatgpt", "codex", "gemini", "ollama"])
                self.assertEqual(snapshot["providers"][0]["status"], "unchecked")
                endpoint.models.assert_not_called()
                checked = request("/api/models/check", {"provider": "chatgpt"})
                self.assertEqual(checked["providers"][0]["models"], [{"id": "studio-plan-fixture", "label": "Studio fixture"}])
                choice = {"provider": "chatgpt", "model": "studio-plan-fixture"}
                preview = request("/api/models/preview", choice)
                self.assertEqual(preview["prompt"], PROMPT)
                self.assertEqual(preview["disclosure"], "cloud")
                endpoint.infer.assert_not_called()
                result = request("/api/models/run", {**choice, "preview_sha256": preview["preview_sha256"]})
                self.assertEqual(result, {**choice, "text": endpoint.infer.return_value})
                endpoint.infer.assert_called_once_with("fixture-secret-access", choice["model"], PROMPT)

                preview = request("/api/models/preview", choice)
                store.clear()
                error = request("/api/models/run", {**choice, "preview_sha256": preview["preview_sha256"]}, status=401)
                self.assertEqual(error["error"]["code"], "MODEL_REAUTH")
                catalog = request("/api/models")["providers"][0]
                self.assertFalse(catalog["can_run"])
                self.assertEqual(catalog["models"], [])
                endpoint.infer.assert_called_once()
            finally:
                server.shutdown()
                worker.join(timeout=5)

    def test_browser_sign_in_actions_require_an_exact_authorized_loopback_request(self):
        config, scope = prepare_demo(self.root / "visit", assistant=True)
        login = Mock()
        login.snapshot.return_value = {"status": "idle"}
        login.start.return_value = {"status": "opening"}
        login.cancel.return_value = {"status": "cancelled"}
        login.disconnect.return_value = {"status": "signed-out", "remote_revocation": "confirmed"}
        with (
            patch("mindgarden.interfaces.local_web.browser_assets", return_value={}),
            patch("mindgarden.interfaces.studio_chatgpt_login.StudioChatGPTLogin", return_value=login) as build_login,
            make_server(config, scope, demo=True, interface="studio", assistant="providers",
                        chatgpt_state_directory=self.state) as server,
        ):
            build_login.assert_called_once_with(self.state)
            login.assert_not_called()
            worker = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
            worker.start()
            try:
                def request(path, body=None, *, origin=server.origin, authorized=True, status=200):
                    headers = {"Authorization": "Bearer " + server.access_token} if authorized else {}
                    if body is not None:
                        headers.update({"Origin": origin, "Content-Type": "application/json"})
                    with closing(HTTPConnection(*server.server_address, timeout=15)) as http:
                        http.request("GET" if body is None else "POST", "/api/models/chatgpt/" + path, body, headers)
                        reply = http.getresponse()
                        data = json.loads(reply.read())
                        self.assertEqual(reply.status, status, data)
                        self.assertEqual(reply.getheader("Cache-Control"), "no-store")
                        return data

                self.assertEqual(request("connection"), {"status": "idle"})
                login.snapshot.assert_called_once_with()
                self.assertFalse(self.state.exists())
                request("connect", "{}", authorized=False, status=403)
                request("connect", "{}", origin="http://untrusted.invalid", status=403)
                request("connect", '{"redirect":"https://untrusted.invalid"}', status=400)
                request("connect", status=404)
                login.start.assert_not_called()
                self.assertEqual(request("connect", "{}"), {"status": "opening"})
                guard, invalidate = login.start.call_args.args
                guard()
                invalidate()
                self.assertEqual(request("cancel", "{}"), {"status": "cancelled"})
                self.assertEqual(request("disconnect", "{}")["remote_revocation"], "confirmed")
                login.start.assert_called_once()
                login.cancel.assert_called_once_with()
                login.disconnect.assert_called_once()
            finally:
                server.shutdown()
                worker.join(timeout=5)
        login.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
