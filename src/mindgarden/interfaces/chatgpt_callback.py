"""Receive one native ChatGPT authorization callback on numeric loopback."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
from secrets import compare_digest
from threading import Event, Lock, Thread, TIMEOUT_MAX
from time import monotonic
from urllib.parse import unquote_plus

from ..adapters.chatgpt_oauth import ISSUER
from ..domain.validation import ContractError
from .chatgpt_callback_page import CALLBACK_STYLE_POLICY, callback_page


CALLBACK_HOST = "127.0.0.1"
CALLBACK_PATH = "/auth/callback"
MAX_TARGET_LENGTH = 8192
MAX_CALLBACK_FIELDS = 32
BAD_ESCAPE = re.compile(r"%(?![a-fA-F0-9]{2})")
SCOPE = re.compile(r"[\x21\x23-\x5b\x5d-\x7e]+(?: [\x21\x23-\x5b\x5d-\x7e]+)*")
OAUTH_MESSAGE = re.compile(r"[\x20-\x21\x23-\x5b\x5d-\x7e]+")
RESPONSE_FIELDS = frozenset({"state", "code", "client_id", "scope", "iss", "error", "error_description", "error_uri"})
CALLBACK_FAILURES = {
    "CHATGPT_CONSENT_DENIED": "ChatGPT authorization was declined",
    "CHATGPT_CALLBACK_RESPONSE": "ChatGPT returned an invalid authorization response",
    "CHATGPT_CALLBACK_PROVIDER": "ChatGPT could not complete authorization",
}


@dataclass(frozen=True)
class _CallbackResponse:
    state: str
    result: tuple[str, str | None] | str


def _visible_ascii(value: str, limit: int) -> bool:
    return 1 <= len(value) <= limit and all("!" <= char <= "~" for char in value)


def _decode(value: str) -> str | None:
    if not value.isascii() or BAD_ESCAPE.search(value):
        return None
    try:
        return unquote_plus(value, errors="strict")
    except UnicodeError:
        return None


def _callback_response(query: str) -> _CallbackResponse | None:
    if not query or "#" in query:
        return None
    pairs = query.split("&", MAX_CALLBACK_FIELDS)
    if len(pairs) > MAX_CALLBACK_FIELDS:
        return None

    fields: dict[str, str] = {}
    seen: set[str] = set()
    invalid = False
    for pair in pairs:
        raw_name, separator, raw_value = pair.partition("=")
        name = _decode(raw_name)
        # OAuth 2.0 authorization responses may add unrecognized extensions.
        if name not in RESPONSE_FIELDS:
            continue
        if name in seen:
            if name == "state":
                return None
            invalid = True
        seen.add(name)
        value = _decode(raw_value) if separator else None
        if value is None:
            invalid = True
        else:
            fields[name] = value

    state = fields.get("state", "")
    if not _visible_ascii(state, 256):
        return None
    malformed = _CallbackResponse(state, "CHATGPT_CALLBACK_RESPONSE")
    if (invalid or fields.get("iss", ISSUER) != ISSUER
            or "scope" in fields and (len(fields["scope"]) > 1024 or not SCOPE.fullmatch(fields["scope"]))):
        return malformed

    if "error" in fields:
        error = fields["error"]
        if ("code" in fields or "client_id" in fields or len(error) > 128 or not OAUTH_MESSAGE.fullmatch(error)
                or "error_description" in fields and (len(fields["error_description"]) > 1024
                                                       or not OAUTH_MESSAGE.fullmatch(fields["error_description"]))
                or "error_uri" in fields and not _visible_ascii(fields["error_uri"], 1024)):
            return malformed
        result = "CHATGPT_CONSENT_DENIED" if error == "access_denied" else "CHATGPT_CALLBACK_PROVIDER"
    else:
        if ("error_description" in fields or "error_uri" in fields or not _visible_ascii(fields.get("code", ""), 4096)
                or "client_id" in fields and not _visible_ascii(fields["client_id"], 256)):
            return malformed
        result = (fields["code"], fields.get("client_id"))
    return _CallbackResponse(state, result)


class _CallbackServer(ThreadingHTTPServer):
    allow_reuse_address = False
    owner: LocalChatGPTCallback

    def verify_request(self, request, client_address):
        return client_address[0] == CALLBACK_HOST

    def handle_error(self, request, client_address):
        # Never report URL-bearing callback exceptions through server logs.
        pass


class _CallbackHandler(BaseHTTPRequestHandler):
    server: _CallbackServer
    timeout = 1.0

    def log_message(self, format, *args):
        pass

    def send_error(self, code, message=None, explain=None):
        status = HTTPStatus.METHOD_NOT_ALLOWED if code == HTTPStatus.NOT_IMPLEMENTED else HTTPStatus(code)
        self._page(status)

    def _page(self, status: HTTPStatus, outcome: str = "invalid") -> None:
        content = callback_page(self.server.owner._destination, outcome)
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'; " + CALLBACK_STYLE_POLICY)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        if status == HTTPStatus.METHOD_NOT_ALLOWED:
            self.send_header("Allow", "GET")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(content)

    def do_GET(self):
        if self.headers.get_all("Host", []) != [f"{CALLBACK_HOST}:{self.server.server_port}"]:
            self._page(HTTPStatus.FORBIDDEN)
            return
        # Use the original request target, before the base handler's leading
        # slash adjustment, so only the documented callback path is accepted.
        target = self.requestline.split()[1]
        path, _, query = target.partition("?")
        if path != CALLBACK_PATH:
            self._page(HTTPStatus.NOT_FOUND)
            return
        response = _callback_response(query) if len(target) <= MAX_TARGET_LENGTH else None
        if response is None or not self.server.owner._claim(response):
            self._page(HTTPStatus.BAD_REQUEST)
            return
        try:
            if isinstance(response.result, tuple):
                self._page(HTTPStatus.OK, "received")
            elif response.result == "CHATGPT_CONSENT_DENIED":
                self._page(HTTPStatus.OK, "declined")
            else:
                self._page(HTTPStatus.BAD_REQUEST)
        finally:
            self.server.owner._ready.set()


class LocalChatGPTCallback:
    """Bind before opening the browser, then receive one matching callback."""

    def __init__(self, *, destination: str = "terminal") -> None:
        if destination not in ("terminal", "studio"):
            raise ContractError("CHATGPT_CALLBACK: choose a supported local sign-in destination")
        self._destination = destination
        self._lock = Lock()
        self._ready = Event()
        self._server: _CallbackServer | None = None
        self._worker: Thread | None = None
        self._redirect_uri: str | None = None
        self._expected_state: str | None = None
        self._deadline = 0.0
        self._waiting = False
        self._closed = False
        self._response: _CallbackResponse | None = None

    def __enter__(self) -> LocalChatGPTCallback:
        with self._lock:
            if self._closed or self._server is not None:
                raise ContractError("CHATGPT_CALLBACK: use a new local sign-in listener")
            try:
                server = _CallbackServer((CALLBACK_HOST, 0), _CallbackHandler)
            except OSError as error:
                raise ContractError("CHATGPT_CALLBACK: the local sign-in listener could not start") from error
            server.owner = self
            self._server = server
            self._redirect_uri = f"http://{CALLBACK_HOST}:{server.server_port}{CALLBACK_PATH}"
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    @property
    def redirect_uri(self) -> str:
        if self._redirect_uri is None:
            raise ContractError("CHATGPT_CALLBACK: start the local sign-in listener first")
        return self._redirect_uri

    def _claim(self, response: _CallbackResponse) -> bool:
        with self._lock:
            if (
                self._closed or self._response is not None or self._expected_state is None or monotonic() >= self._deadline
                or not compare_digest(response.state, self._expected_state)
            ):
                return False
            self._response = response
            return True

    def arm(self, expected_state: str, *, timeout: float = 180) -> None:
        """Accept this exact state before a system browser opener can block."""
        if not isinstance(expected_state, str) or not _visible_ascii(expected_state, 256):
            raise ContractError("CHATGPT_CALLBACK: supply the pending sign-in state")
        if type(timeout) not in (int, float) or not 0 < timeout <= TIMEOUT_MAX:
            raise ContractError("CHATGPT_CALLBACK: supply a positive local sign-in timeout")
        with self._lock:
            if self._closed or self._server is None or self._worker is not None:
                raise ContractError("CHATGPT_CALLBACK: use a running, unused local sign-in listener")
            self._arm(expected_state, timeout)

    def _arm(self, expected_state: str, timeout: float) -> None:
        self._expected_state = expected_state
        self._deadline = monotonic() + timeout
        self._worker = Thread(
            target=self._server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True,
            name="mindgarden-chatgpt-callback",
        )
        try:
            self._worker.start()
        except RuntimeError as error:
            self._worker = self._expected_state = None
            raise ContractError("CHATGPT_CALLBACK: the local sign-in listener could not start") from error

    def wait(self, expected_state: str, *, timeout: float = 180) -> tuple[str, str | None]:
        if not isinstance(expected_state, str) or not _visible_ascii(expected_state, 256):
            raise ContractError("CHATGPT_CALLBACK: supply the pending sign-in state")
        if type(timeout) not in (int, float) or not 0 < timeout <= TIMEOUT_MAX:
            raise ContractError("CHATGPT_CALLBACK: supply a positive local sign-in timeout")
        with self._lock:
            if self._closed:
                raise ContractError("CHATGPT_CALLBACK_CANCELLED: local sign-in was cancelled")
            if self._server is None or self._waiting:
                raise ContractError("CHATGPT_CALLBACK: use a running, unused local sign-in listener")
            if self._worker is None:
                self._arm(expected_state, timeout)
            elif not compare_digest(expected_state, self._expected_state):
                raise ContractError("CHATGPT_CALLBACK: use the state armed for local sign-in")
            self._waiting = True
        try:
            self._ready.wait(max(0, self._deadline - monotonic()))
            with self._lock:
                if self._closed:
                    raise ContractError("CHATGPT_CALLBACK_CANCELLED: local sign-in was cancelled")
                if self._response is None:
                    raise ContractError("CHATGPT_CALLBACK_TIMEOUT: local sign-in did not complete in time")
                result = self._response.result
                if isinstance(result, str):
                    raise ContractError(result + ": " + CALLBACK_FAILURES[result])
                return result
        finally:
            self.close()

    def close(self) -> None:
        """Stop accepting input and release a waiter, including during cancellation."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._response = self._expected_state = None
            self._ready.set()
            server, worker = self._server, self._worker
            self._server = self._worker = None
        if server is not None:
            try:
                if worker is not None:
                    server.shutdown()
                    worker.join()
            finally:
                server.server_close()
