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

from mindgarden.adapters.chatgpt_oauth import ISSUER
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.chatgpt_callback import LocalChatGPTCallback
from mindgarden.interfaces.chatgpt_callback_page import CALLBACK_STYLE_POLICY, callback_page


STATE = "synthetic-pending-state"
CODE = "synthetic-test-code+encoded=%"
CLIENT = "fictional-issued-client"


class ChatGPTCallbackTests(unittest.TestCase):
    def request(self, listener, target, *, method="GET", host=None, destination="terminal", outcome="invalid"):
        port = urlsplit(listener.redirect_uri).port
        headers = {} if host is None else {"Host": host}
        with closing(HTTPConnection("127.0.0.1", port, timeout=2)) as connection:
            connection.request(method, target, headers=headers)
            response = connection.getresponse()
            self.assertEqual(response.getheader("Cache-Control"), "no-store")
            self.assertEqual(response.getheader("Referrer-Policy"), "no-referrer")
            policy = response.getheader("Content-Security-Policy")
            self.assertIn("default-src 'none'", policy)
            self.assertIn(CALLBACK_STYLE_POLICY, policy)
            self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))
            content = response.read()
            for private in (CODE, STATE, CLIENT, "private-callback-canary"):
                self.assertNotIn(private.encode(), content)
            self.assertEqual(content, callback_page(destination, outcome))
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
                state = [
                    ("state", STATE), ("code", CODE), ("client_id", CLIENT), ("scope", "openid profile"),
                    ("iss", ISSUER), ("session_state", "private-callback-canary"), ("other_provider_field", "one"),
                    ("other_provider_field", "two"),
                ]
                target = "/auth/callback?" + urlencode(state)
                self.assertEqual(self.request(listener, "/favicon.ico")[0], 404)
                self.assertEqual(self.request(listener, target, method="POST")[0], 405)
                self.assertEqual(self.request(listener, target, host=f"localhost:{redirect.port}")[0], 403)
                self.assertEqual(self.request(listener, "/" + target)[0], 404)
                self.assertEqual(self.request(listener, listener.redirect_uri + "?" + urlencode(state))[0], 404)
                self.assertEqual(self.request(listener, target.replace(STATE, "wrong-state"))[0], 400)
                self.assertFalse(waiting.done())
                status, _ = self.request(listener, target, outcome="received")
                self.assertEqual(status, 200)
                self.assertEqual(waiting.result(timeout=1), (CODE, CLIENT))
            with self.assertRaisesRegex(ContractError, "CHATGPT_CALLBACK"):
                listener.wait(STATE, timeout=0.1)
            with self.assertRaises(OSError):
                create_connection(("127.0.0.1", redirect.port), timeout=0.2)
        self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ""))

    def test_missing_wrong_or_ambiguous_state_never_claims_pending_attempt(self):
        with LocalChatGPTCallback() as listener, ThreadPoolExecutor(max_workers=1) as worker:
            waiting = worker.submit(listener.wait, STATE, timeout=3)
            malformed = (
                "",
                "?code=example",
                "?state=wrong-state&code=%FF",
                "?state=wrong-state&error=server_error",
                "?state=%ZZ&code=example",
                f"?state={STATE}&st%61te=duplicate&code=example",
                f"?state={STATE}&state=&code=example",
                f"?state={STATE}&state={STATE}&code=example",
                f"?state={STATE}&code=" + "c" * 8200,
                f"?state={STATE}&code=example" + "&extra=present" * 33,
            )
            for suffix in malformed:
                with self.subTest(suffix=suffix[:60]):
                    self.assertEqual(self.request(listener, "/auth/callback" + suffix)[0], 400)
            self.assertFalse(waiting.done())
            self.assertEqual(self.request(listener, f"/auth/callback?state={STATE}&code=example", outcome="received")[0], 200)
            self.assertEqual(waiting.result(timeout=1), ("example", None))

    def test_matched_malformed_core_fields_end_attempt_with_safe_terminal_error(self):
        malformed = (
            "",
            "&code=",
            "&code=first&c%6fde=duplicate",
            "&code=example&error=access_denied",
            "&code=example&client_id=",
            "&code=example&scope=bad%09scope",
            "&code=%FF",
            "&code=bad%ZZ",
            "&code=%0aexample",
            "&code",
            "&code=example&iss=https%3A%2F%2Fother.example",
            "&code=example&" + urlencode([("iss", ISSUER), ("iss", ISSUER)]),
            "&error=server_error&error_description=%0aprivate-callback-canary",
        )
        for suffix in malformed:
            with self.subTest(suffix=suffix), LocalChatGPTCallback(destination="studio") as listener:
                listener.arm(STATE, timeout=1)
                self.assertEqual(self.request(listener, f"/auth/callback?state={STATE}" + suffix, destination="studio")[0], 400)
                with self.assertRaisesRegex(ContractError, "^CHATGPT_CALLBACK_RESPONSE:") as invalid:
                    listener.wait(STATE)
                self.assertNotIn("private-callback-canary", str(invalid.exception))

    def test_matched_provider_error_ends_attempt_without_provider_details(self):
        with LocalChatGPTCallback(destination="studio") as listener:
            listener.arm(STATE, timeout=1)
            response = {
                "state": STATE, "error": "server_error", "error_description": "private-callback-canary",
                "error_uri": "https://example.invalid/private-callback-canary", "iss": ISSUER,
                "session_state": "private-callback-canary",
            }
            self.assertEqual(self.request(listener, "/auth/callback?" + urlencode(response), destination="studio")[0], 400)
            with self.assertRaisesRegex(ContractError, "^CHATGPT_CALLBACK_PROVIDER:") as failed:
                listener.wait(STATE)
            self.assertNotIn("private-callback-canary", str(failed.exception))
            self.assertNotIn("server_error", str(failed.exception))

    def test_only_correlated_access_denial_ends_flow_and_is_sanitized(self):
        with LocalChatGPTCallback() as listener, ThreadPoolExecutor(max_workers=1) as worker:
            waiting = worker.submit(listener.wait, STATE, timeout=3)
            denial = {"state": "wrong-state", "error": "access_denied", "error_description": "private-callback-canary"}
            self.assertEqual(self.request(listener, "/auth/callback?" + urlencode(denial))[0], 400)
            self.assertFalse(waiting.done())
            denial["state"] = STATE
            status, _ = self.request(listener, "/auth/callback?" + urlencode(denial), outcome="declined")
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
