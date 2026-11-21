"""Use a real loopback listener with fictional OAuth messages only."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, redirect_stderr, redirect_stdout
from http.client import HTTPConnection
from io import StringIO
from pathlib import Path
from socket import create_connection
import sys
from time import monotonic
import unittest
from urllib.parse import urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.chatgpt_callback import LocalChatGPTCallback


STATE = "synthetic-pending-state"
CODE = "synthetic-test-code+encoded=%"
CLIENT = "fictional-issued-client"


class ChatGPTCallbackTests(unittest.TestCase):
    def request(self, listener, target, *, method="GET", host=None):
        port = urlsplit(listener.redirect_uri).port
        headers = {} if host is None else {"Host": host}
        with closing(HTTPConnection("127.0.0.1", port, timeout=2)) as connection:
            connection.request(method, target, headers=headers)
            response = connection.getresponse()
            self.assertEqual(response.getheader("Cache-Control"), "no-store")
            self.assertEqual(response.getheader("Referrer-Policy"), "no-referrer")
            self.assertIn("default-src 'none'", response.getheader("Content-Security-Policy"))
            self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))
            content = response.read()
            for private in (CODE, STATE, CLIENT, "private-callback-canary"):
                self.assertNotIn(private.encode(), content)
            self.assertIn(b"Return to Mindgarden", content)
            return response.status, content

    def test_only_matching_exact_get_finishes_and_callback_data_stays_out_of_logs(self):
        stdout, stderr = StringIO(), StringIO()
        with LocalChatGPTCallback() as listener, redirect_stdout(stdout), redirect_stderr(stderr):
            redirect = urlsplit(listener.redirect_uri)
            self.assertEqual((redirect.scheme, redirect.hostname, redirect.path), ("http", "127.0.0.1", "/auth/callback"))
            self.assertIsNone(redirect.username)
            self.assertGreater(redirect.port, 0)
            self.assertEqual((redirect.query, redirect.fragment), ("", ""))
            with ThreadPoolExecutor(max_workers=1) as worker:
                waiting = worker.submit(listener.wait, STATE, timeout=3)
                state = {"state": STATE, "code": CODE, "client_id": CLIENT, "scope": "openid profile"}
                target = "/auth/callback?" + urlencode(state)
                self.assertEqual(self.request(listener, "/favicon.ico")[0], 404)
                self.assertEqual(self.request(listener, target, method="POST")[0], 405)
                self.assertEqual(self.request(listener, target, host=f"localhost:{redirect.port}")[0], 403)
                self.assertEqual(self.request(listener, "/" + target)[0], 404)
                self.assertEqual(self.request(listener, listener.redirect_uri + "?" + urlencode(state))[0], 404)
                self.assertEqual(self.request(listener, target.replace(STATE, "wrong-state"))[0], 400)
                self.assertFalse(waiting.done())
                status, page = self.request(listener, target)
                self.assertEqual(status, 200)
                self.assertIn(b"Close this tab", page)
                self.assertEqual(waiting.result(timeout=1), (CODE, CLIENT))
            with self.assertRaisesRegex(ContractError, "CHATGPT_CALLBACK"):
                listener.wait(STATE, timeout=0.1)
            with self.assertRaises(OSError):
                create_connection(("127.0.0.1", redirect.port), timeout=0.2)
        self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ""))

    def test_malformed_ambiguous_or_empty_values_never_claim_pending_attempt(self):
        with LocalChatGPTCallback() as listener, ThreadPoolExecutor(max_workers=1) as worker:
            waiting = worker.submit(listener.wait, STATE, timeout=3)
            prefix = f"/auth/callback?state={STATE}"
            malformed = (
                "",
                "&code=",
                "&code=example&code=duplicate",
                "&code=example&st%61te=duplicate",
                "&code=example&error=access_denied",
                "&code=example&client_id=",
                "&code=example&extra=unsupported",
                "&code=example&scope=bad%09scope",
                "&code=%FF",
                "&code=bad%ZZ",
                "&code=%0aexample",
                "&error=server_error",
                "&code=" + "c" * 8200,
            )
            for suffix in malformed:
                with self.subTest(suffix=suffix[:60]):
                    self.assertEqual(self.request(listener, prefix + suffix)[0], 400)
            self.assertFalse(waiting.done())
            self.assertEqual(self.request(listener, prefix + "&code=example")[0], 200)
            self.assertEqual(waiting.result(timeout=1), ("example", None))

    def test_only_correlated_access_denial_ends_flow_and_is_sanitized(self):
        with LocalChatGPTCallback() as listener, ThreadPoolExecutor(max_workers=1) as worker:
            waiting = worker.submit(listener.wait, STATE, timeout=3)
            denial = {"state": "wrong-state", "error": "access_denied", "error_description": "private-callback-canary"}
            self.assertEqual(self.request(listener, "/auth/callback?" + urlencode(denial))[0], 400)
            self.assertFalse(waiting.done())
            denial["state"] = STATE
            status, _ = self.request(listener, "/auth/callback?" + urlencode(denial))
            self.assertEqual(status, 200)
            with self.assertRaisesRegex(ContractError, "^CHATGPT_CONSENT_DENIED") as denied:
                waiting.result(timeout=1)
            self.assertNotIn("private-callback-canary", str(denied.exception))

    def test_timeout_and_cancellation_close_even_with_an_incomplete_request(self):
        with LocalChatGPTCallback() as listener:
            started = monotonic()
            with self.assertRaisesRegex(ContractError, "^CHATGPT_CALLBACK_TIMEOUT"):
                listener.wait(STATE, timeout=0.03)
            self.assertLess(monotonic() - started, 0.7)
        with LocalChatGPTCallback() as listener, ThreadPoolExecutor(max_workers=1) as worker:
            waiting = worker.submit(listener.wait, STATE, timeout=4)
            self.assertEqual(self.request(listener, "/favicon.ico")[0], 404)
            redirect = urlsplit(listener.redirect_uri)
            with closing(create_connection((redirect.hostname, redirect.port), timeout=1)) as connection:
                connection.sendall(b"GET /auth/callback?")
                listener.close()
                with self.assertRaisesRegex(ContractError, "^CHATGPT_CALLBACK_CANCELLED"):
                    waiting.result(timeout=0.7)
