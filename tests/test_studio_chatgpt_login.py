"""Drive Studio's native browser broker through fictional loopback consent."""

from contextlib import closing
from http.client import HTTPConnection
from pathlib import Path
from socket import create_connection
import sys
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic, sleep
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.chatgpt_credentials import ChatGPTCredentials, ChatGPTStore
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.chatgpt_callback import LocalChatGPTCallback
from mindgarden.interfaces.studio_chatgpt_login import StudioChatGPTLogin
from mindgarden.interfaces.studio_diagnostics import StudioDiagnostics


class StudioChatGPTLoginTests(unittest.TestCase):
    def setUp(self):
        workspace = TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.directory = Path(workspace.name).resolve() / "chatgpt"
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
        self.guard = Mock()
        self.invalidate = Mock()

    def login(self, browse, **options):
        login = StudioChatGPTLogin(self.directory, browse=browse, oauth=self.oauth, **options)
        self.addCleanup(login.close)
        return login

    def until(self, condition, timeout=3):
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            if condition():
                return
            sleep(0.01)
        self.fail("The fictional consent operation did not settle")

    def wait_status(self, login, status):
        self.until(lambda: login.snapshot()["status"] == status)

    def consent(self, url):
        fields = parse_qs(urlsplit(url).query)
        callback = urlsplit(fields["redirect_uri"][0])
        target = callback.path + "?" + urlencode({
            "state": fields["state"][0], "code": "fixture-code", "client_id": self.credentials.client_id,
        })
        with closing(HTTPConnection(callback.hostname, callback.port, timeout=1)) as connection:
            connection.request("GET", target)
            result = connection.getresponse()
            self.assertEqual(result.status, 200)
            self.assertNotIn(b"fixture-code", result.read())
        return True

    def test_requires_explicit_start_and_arms_before_a_synchronous_browser(self):
        login = self.login(self.consent)
        diagnostics = StudioDiagnostics()
        login.attach_diagnostics(diagnostics.sign_in)
        self.assertEqual(login.snapshot(), {"status": "idle"})
        self.assertFalse(self.directory.exists())
        self.oauth.require_oidc.assert_not_called()

        def invalidate():
            # A separate instance can only take this lease after the worker's
            # application flow has released its own credential writer.
            with ChatGPTStore(self.directory).writer():
                self.assertEqual(ChatGPTStore(self.directory).read(), self.credentials)

        self.invalidate.side_effect = invalidate
        self.assertEqual(login.start(self.guard, self.invalidate), {"status": "opening"})
        self.wait_status(login, "authorized")
        self.assertEqual(login.snapshot(), {"status": "authorized"})
        self.oauth.exchange.assert_called_once()
        self.assertEqual(self.oauth.exchange.call_args.args[1:], ("fixture-code", self.credentials.client_id))
        self.assertEqual(ChatGPTStore(self.directory).read(), self.credentials)
        self.invalidate.assert_called_once_with()
        events = diagnostics.snapshot()["events"]
        self.assertEqual([event["code"] for event in events], [
            "CHATGPT_LOGIN_OPENING", "CHATGPT_LOGIN_WAITING", "CHATGPT_LOGIN_VERIFYING", "CHATGPT_LOGIN_AUTHORIZED",
        ])
        self.assertTrue(all(event["outcome"] == "ok" and event["operation"] == "sign-in" for event in events))
        self.assertNotIn("fixture-code", str(events))

    def test_fresh_visit_reports_previously_saved_consent_without_contacting_openai(self):
        ChatGPTStore(self.directory).save(self.credentials)
        browser = Mock()
        login = self.login(browser)
        self.assertEqual(login.snapshot(), {"status": "authorized"})
        browser.assert_not_called()
        self.oauth.require_oidc.assert_not_called()
        self.oauth.exchange.assert_not_called()

    def test_cancel_closes_the_waiting_callback_and_a_new_attempt_can_follow(self):
        urls = []

        def browser(url):
            urls.append(url)
            return self.consent(url) if len(urls) > 1 else True

        login = self.login(browser)
        login.start(self.guard, self.invalidate)
        self.wait_status(login, "waiting")
        with self.assertRaisesRegex(ContractError, "^CHATGPT_STATE_BUSY"):
            login.start(self.guard, self.invalidate)
        with self.assertRaisesRegex(ContractError, "^CHATGPT_STATE_BUSY"):
            login.disconnect(self.guard, self.invalidate)
        callback = urlsplit(parse_qs(urlsplit(urls[-1]).query)["redirect_uri"][0])
        self.assertEqual(login.cancel(), {"status": "cancelled"})
        with self.assertRaises(OSError):
            create_connection((callback.hostname, callback.port), timeout=0.2)
        self.oauth.exchange.assert_not_called()
        self.invalidate.assert_not_called()

        def try_again():
            try:
                return login.start(self.guard, self.invalidate)
            except ContractError as error:
                if not str(error).startswith("CHATGPT_STATE_BUSY:"):
                    raise
                return None

        self.until(try_again)
        self.wait_status(login, "authorized")
        self.assertNotEqual(parse_qs(urlsplit(urls[0]).query)["state"], parse_qs(urlsplit(urls[1]).query)["state"])

    def test_cancel_and_server_close_veto_a_blocked_exchange_before_saving(self):
        for action in ("cancel", "close"):
            with self.subTest(action=action):
                self.directory = self.directory.parent / action
                entered, release = Event(), Event()

                def exchange(*_arguments):
                    entered.set()
                    if not release.wait(2):
                        raise AssertionError("The test did not unblock the exchange")
                    return self.credentials

                self.oauth.exchange.side_effect = exchange
                login = self.login(self.consent)
                login.start(self.guard, self.invalidate)
                try:
                    self.assertTrue(entered.wait(2))
                    self.assertEqual(login.snapshot(), {"status": "verifying"})
                    with self.assertRaisesRegex(ContractError, "^CHATGPT_STATE_BUSY"), ChatGPTStore(self.directory).writer():
                        pass
                    getattr(login, action)()
                    self.assertEqual(login.snapshot(), {"status": "cancelled"})
                finally:
                    release.set()

                def credential_lease_released():
                    try:
                        with ChatGPTStore(self.directory).writer():
                            return True
                    except ContractError as error:
                        if not str(error).startswith("CHATGPT_STATE_BUSY:"):
                            raise
                        return False

                self.until(credential_lease_released)
                self.assertIsNone(ChatGPTStore(self.directory).read())
                self.invalidate.assert_not_called()

    def test_live_guard_rechecks_before_exchange_and_after_it_before_persistence(self):
        for stage in ("before-exchange", "before-save"):
            with self.subTest(stage=stage):
                self.directory = self.directory.parent / stage
                self.oauth.exchange.reset_mock()
                revoked = Event()

                def guard():
                    if revoked.is_set():
                        raise ContractError("SESSION_REVOKED: private-callback-canary")

                def browser(url):
                    opened = self.consent(url)
                    if stage == "before-exchange":
                        revoked.set()
                    return opened

                def exchange(*_arguments):
                    revoked.set()
                    return self.credentials

                self.oauth.exchange.side_effect = exchange
                login = self.login(browser)
                diagnostics = StudioDiagnostics()
                login.attach_diagnostics(diagnostics.sign_in)
                login.start(guard, self.invalidate)
                self.wait_status(login, "failed")
                self.assertEqual(login.snapshot(), {"status": "failed", "code": "SESSION_REVOKED"})
                event = diagnostics.snapshot()["events"][-1]
                self.assertEqual((event["code"], event["outcome"]), ("SESSION_REVOKED", "error"))
                self.assertNotIn("private-callback-canary", str(event))
                self.assertIsNone(ChatGPTStore(self.directory).read())
                self.invalidate.assert_not_called()
                if stage == "before-exchange":
                    self.oauth.exchange.assert_not_called()
                else:
                    self.oauth.exchange.assert_called_once()

    def test_stuck_native_opener_does_not_extend_the_callback_or_writer_lease(self):
        release = Event()

        class ShortCallback(LocalChatGPTCallback):
            def arm(self, state):
                super().arm(state, timeout=0.08)

        login = self.login(lambda _url: release.wait(2), callback=ShortCallback)
        try:
            with patch("mindgarden.interfaces.studio_chatgpt_login.BROWSER_START_TIMEOUT", 0.02):
                login.start(self.guard, self.invalidate)
                self.wait_status(login, "failed")
            self.assertEqual(login.snapshot(), {"status": "failed", "code": "CHATGPT_CALLBACK_TIMEOUT"})
            self.oauth.exchange.assert_not_called()
            with ChatGPTStore(self.directory).writer():
                self.assertIsNone(ChatGPTStore(self.directory).read())
        finally:
            release.set()

    def test_disconnect_reports_only_revocation_outcome_and_invalidates_after_local_clear(self):
        login = self.login(Mock())
        store = ChatGPTStore(self.directory)
        store.save(self.credentials)
        self.oauth.revoke.side_effect = ContractError("CHATGPT_OAUTH_REVOCATION: private-callback-canary")
        self.assertEqual(login.disconnect(self.guard, self.invalidate), {
            "status": "signed-out", "remote_revocation": "unconfirmed",
        })
        self.assertIsNone(store.read())
        self.assertEqual(store.registration(), self.credentials.registration)
        self.oauth.revoke.assert_called_once_with(self.credentials)
        self.invalidate.assert_called_once_with()
