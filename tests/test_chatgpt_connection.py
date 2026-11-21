"""Rehearse local consent, renewal and removal with a synthetic OAuth client."""

from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import replace
from http.client import HTTPConnection
from io import StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import Mock
from urllib.parse import parse_qs, urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.chatgpt_credentials import ChatGPTCredentials, ChatGPTStore
from mindgarden.application import chatgpt_connection
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.chatgpt_callback import LocalChatGPTCallback
from mindgarden.interfaces.cli import ExitCode, main


class ChatGPTConnectionTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve() / "chatgpt"
        self.store = ChatGPTStore(self.directory)
        self.urls = []
        self.oauth = Mock()
        self.credentials = ChatGPTCredentials(
            issuer="https://auth.openai.com",
            subject="synthetic-subject",
            client_id="oaiapp_0123456789abcdef",
            scopes=("chatgpt.tokens.use.direct", "offline_access", "openid", "resource.invoke"),
            access_token="fixture-secret-access",
            refresh_token="fixture-secret-refresh",
            id_token="fixture-secret-identity",
            expires_at=1_999_999_999,
            earliest_refresh_at=1_999_999_000,
        )
        self.oauth.exchange.return_value = self.credentials

    @contextmanager
    def callback(self):
        listener = Mock(redirect_uri="http://127.0.0.1:37791/auth/callback")

        def wait(state):
            query = parse_qs(urlsplit(self.urls[-1]).query)
            self.assertEqual([state], query["state"])
            return "fixture-authorization-code", self.credentials.client_id

        listener.wait.side_effect = wait
        yield listener

    def browse(self, url):
        self.urls.append(url)
        self.assertEqual(urlsplit(url).netloc, "auth.openai.com")
        return True

    def connect(self):
        return chatgpt_connection.connect(
            self.directory, oauth=self.oauth, callback=self.callback, browse=self.browse
        )

    def test_first_connect_and_returning_authorization_keep_host_and_client(self):
        self.assertFalse(self.directory.exists())
        self.assertEqual(chatgpt_connection.status(self.directory), {"status": "signed-out", "registration_saved": False})
        self.assertFalse(self.directory.exists())
        self.assertEqual(self.connect(), {"status": "authorized", "registration_saved": True})
        self.assertEqual(self.store.read(), self.credentials)
        self.connect()
        first, second = (parse_qs(urlsplit(url).query) for url in self.urls)
        self.assertEqual(first["client_id"], ["dynamic_agent_client"])
        self.assertEqual(second["client_id"], [self.credentials.client_id])
        self.assertEqual(first["ext_agent_host_id"], second["ext_agent_host_id"])
        for field in ("state", "nonce", "code_challenge"):
            self.assertNotEqual(first[field], second[field])
        self.assertNotIn("fixture-secret", repr(self.urls))

    def test_denied_consent_or_missing_browser_preserves_the_active_registration(self):
        self.connect()
        self.oauth.exchange.reset_mock()

        @contextmanager
        def denied():
            listener = Mock(redirect_uri="http://127.0.0.1:37791/auth/callback")
            listener.wait.side_effect = ContractError("CHATGPT_CONSENT_DENIED: consent was declined")
            yield listener

        with self.assertRaisesRegex(ContractError, "CHATGPT_CONSENT_DENIED"):
            chatgpt_connection.connect(self.directory, oauth=self.oauth, callback=denied, browse=self.browse)
        with self.assertRaisesRegex(ContractError, "CHATGPT_BROWSER"):
            chatgpt_connection.connect(self.directory, oauth=self.oauth, callback=self.callback, browse=lambda url: False)
        self.oauth.exchange.assert_not_called()
        self.assertEqual(self.store.read(), self.credentials)

    def test_live_loopback_callback_completes_with_a_fake_oauth_exchange(self):
        observed = []
        workers = []

        @contextmanager
        def callback():
            with LocalChatGPTCallback() as listener:
                yield Mock(redirect_uri=listener.redirect_uri,
                           wait=lambda state: listener.wait(state, timeout=5))

        def browser(url):
            values = parse_qs(urlsplit(url).query)
            callback_uri = urlsplit(values["redirect_uri"][0])
            self.assertEqual(callback_uri.hostname, "127.0.0.1")
            query = urlencode({
                "state": values["state"][0], "code": "fixture-code", "client_id": self.credentials.client_id,
            })

            def deliver():
                http = HTTPConnection(callback_uri.hostname, callback_uri.port, timeout=5)
                try:
                    http.request("GET", callback_uri.path + "?" + query)
                    response = http.getresponse()
                    observed.append((response.status, response.read()))
                finally:
                    http.close()

            worker = Thread(target=deliver, daemon=True)
            workers.append(worker)
            worker.start()
            return True

        self.assertEqual(
            chatgpt_connection.connect(self.directory, oauth=self.oauth, callback=callback, browse=browser)["status"],
            "authorized",
        )
        workers[0].join(timeout=5)
        self.assertEqual(observed[0][0], 200)
        self.assertNotIn(b"fixture-code", observed[0][1])
        self.oauth.exchange.assert_called_once()
        self.assertEqual(self.oauth.exchange.call_args.args[1:], ("fixture-code", self.credentials.client_id))

    def test_refresh_applies_only_after_earliest_time_and_rotates_tokens(self):
        self.connect()
        result = chatgpt_connection.refresh(self.directory, oauth=self.oauth, clock=lambda: 1_999_998_999)
        self.assertEqual(result["status"], "refresh-not-due")
        self.oauth.refresh.assert_not_called()
        self.assertEqual(chatgpt_connection.status(self.directory, clock=lambda: 1_999_999_999)["status"], "expired")
        renewed = replace(self.credentials, access_token="fixture-next-access", refresh_token="fixture-next-refresh",
                          expires_at=2_000_000_999, earliest_refresh_at=2_000_000_500)
        self.oauth.refresh.return_value = renewed
        result = chatgpt_connection.refresh(self.directory, oauth=self.oauth, clock=lambda: 1_999_999_000)
        self.assertEqual(result, {"status": "refreshed", "expires_at": renewed.expires_at})
        self.oauth.refresh.assert_called_once_with(self.credentials)
        self.assertEqual(self.store.read(), renewed)

    def test_disconnect_reports_unconfirmed_remote_revocation_and_clears_local_tokens(self):
        self.connect()
        self.oauth.revoke.side_effect = ContractError("CHATGPT_OAUTH_UNAVAILABLE: bounded revocation did not finish")
        result = chatgpt_connection.disconnect(self.directory, oauth=self.oauth)
        self.assertEqual(result, {"status": "signed-out", "remote_revocation": "unconfirmed"})
        self.assertIsNone(self.store.read())
        self.assertEqual(self.store.registration().client_id, self.credentials.client_id)
        self.assertEqual(chatgpt_connection.disconnect(self.directory, oauth=self.oauth)["remote_revocation"], "not-needed")
        self.oauth.revoke.assert_called_once_with(self.credentials)

    def test_terminal_refresh_errors_remove_tokens_but_transient_errors_preserve_them(self):
        self.connect()
        self.oauth.refresh.side_effect = ContractError("CHATGPT_OAUTH_UNAVAILABLE: retry later")
        with self.assertRaisesRegex(ContractError, "CHATGPT_OAUTH_UNAVAILABLE"):
            chatgpt_connection.refresh(self.directory, oauth=self.oauth, clock=lambda: 2_000_000_000)
        self.assertEqual(self.store.read(), self.credentials)
        self.oauth.refresh.side_effect = ContractError("CHATGPT_REFRESH_REAUTHORIZE: sign in again")
        with self.assertRaisesRegex(ContractError, "CHATGPT_REFRESH_REAUTHORIZE"):
            chatgpt_connection.refresh(self.directory, oauth=self.oauth, clock=lambda: 2_000_000_000)
        self.assertIsNone(self.store.read())
        self.assertEqual(self.store.registration().client_id, self.credentials.client_id)

    def test_narrowed_refresh_scope_requires_new_consent(self):
        self.connect()
        self.oauth.refresh.side_effect = ContractError("CHATGPT_OAUTH_SCOPE: ChatGPT plan permissions were not confirmed")
        with self.assertRaisesRegex(ContractError, "CHATGPT_OAUTH_SCOPE"):
            chatgpt_connection.refresh(self.directory, oauth=self.oauth, clock=lambda: 2_000_000_000)
        self.assertIsNone(self.store.read())
        self.assertTrue(self.store.registration())

    def test_cli_status_uses_stable_redacted_shape(self):
        self.connect()
        with redirect_stdout(StringIO()) as stdout, redirect_stderr(StringIO()) as stderr:
            result = main(["chatgpt", "status", "--state-directory", str(self.directory)])
        self.assertEqual(result, ExitCode.SUCCESS)
        self.assertEqual(stderr.getvalue(), "")
        state = json.loads(stdout.getvalue())
        self.assertCountEqual(state, ["status", "registration_saved", "expires_at"])
        self.assertNotIn("fixture-secret", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
