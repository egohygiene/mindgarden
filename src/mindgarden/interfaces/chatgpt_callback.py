"""Receive one native ChatGPT authorization callback on numeric loopback."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
from secrets import compare_digest
from threading import Event, Lock, Thread, TIMEOUT_MAX
from time import monotonic
from urllib.parse import parse_qsl

from ..domain.validation import ContractError


CALLBACK_HOST = "127.0.0.1"
CALLBACK_PATH = "/auth/callback"
MAX_TARGET_LENGTH = 8192
BAD_ESCAPE = re.compile(r"%(?![a-fA-F0-9]{2})")
SCOPE = re.compile(r"[\x21\x23-\x5b\x5d-\x7e]+(?: [\x21\x23-\x5b\x5d-\x7e]+)*")
CALLBACK_PAGE = (
    b'<!doctype html><html lang="en"><head><meta charset="utf-8">'
    b"<title>Return to Mindgarden</title></head><body>"
    b"<main><h1>Return to Mindgarden</h1>"
    b"<p>Close this tab and continue in your terminal.</p></main></body></html>"
)


def _visible_ascii(value: str, limit: int) -> bool:
    return 1 <= len(value) <= limit and all("!" <= char <= "~" for char in value)


def _callback_parameters(query: str) -> dict[str, str] | None:
    if not query or not query.isascii() or "#" in query or BAD_ESCAPE.search(query):
        return None
    try:
        pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True, errors="strict", max_num_fields=5)
    except ValueError:
        return None
    fields = dict(pairs)
    if len(fields) != len(pairs) or not _visible_ascii(fields.get("state", ""), 256):
        return None
    if "scope" in fields and (len(fields["scope"]) > 1024 or not SCOPE.fullmatch(fields["scope"])):
        return None
    if "error" in fields:
        if fields["error"] != "access_denied" or not fields.keys() <= {"state", "error", "scope", "error_description", "error_uri"}:
            return None
        for name in ("error_description", "error_uri"):
            if name in fields and (len(fields[name]) > 1024 or not fields[name].isprintable()):
                return None
    else:
        if not fields.keys() <= {"state", "code", "client_id", "scope"} or not _visible_ascii(fields.get("code", ""), 4096):
            return None
        if "client_id" in fields and not _visible_ascii(fields["client_id"], 256):
            return None
    return fields


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

    def _page(self, status: HTTPStatus) -> None:
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(CALLBACK_PAGE)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        if status == HTTPStatus.METHOD_NOT_ALLOWED:
            self.send_header("Allow", "GET")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(CALLBACK_PAGE)

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
        fields = _callback_parameters(query) if len(target) <= MAX_TARGET_LENGTH else None
        if fields is None or not self.server.owner._claim(fields):
            self._page(HTTPStatus.BAD_REQUEST)
            return
        try:
            self._page(HTTPStatus.OK)
        finally:
            self.server.owner._ready.set()


class LocalChatGPTCallback:
    """Bind before opening the browser, then receive one matching callback."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._ready = Event()
        self._server: _CallbackServer | None = None
        self._worker: Thread | None = None
        self._redirect_uri: str | None = None
        self._expected_state: str | None = None
        self._deadline = 0.0
        self._completed = False
        self._closed = False
        self._result: tuple[str, str | None] | None = None

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

    def _claim(self, fields: dict[str, str]) -> bool:
        with self._lock:
            if (
                self._closed or self._completed or self._expected_state is None or monotonic() >= self._deadline
                or not compare_digest(fields["state"], self._expected_state)
            ):
                return False
            self._completed = True
            if "code" in fields:
                self._result = fields["code"], fields.get("client_id")
            return True

    def wait(self, expected_state: str, *, timeout: float = 180) -> tuple[str, str | None]:
        if not isinstance(expected_state, str) or not _visible_ascii(expected_state, 256):
            raise ContractError("CHATGPT_CALLBACK: supply the pending sign-in state")
        if type(timeout) not in (int, float) or not 0 < timeout <= TIMEOUT_MAX:
            raise ContractError("CHATGPT_CALLBACK: supply a positive local sign-in timeout")
        with self._lock:
            if self._closed or self._server is None or self._worker is not None:
                raise ContractError("CHATGPT_CALLBACK: use a running, unused local sign-in listener")
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
        try:
            self._ready.wait(max(0, self._deadline - monotonic()))
            with self._lock:
                if self._closed:
                    raise ContractError("CHATGPT_CALLBACK_CANCELLED: local sign-in was cancelled")
                if not self._completed:
                    raise ContractError("CHATGPT_CALLBACK_TIMEOUT: local sign-in did not complete in time")
                if self._result is None:
                    raise ContractError("CHATGPT_CONSENT_DENIED: ChatGPT authorization was declined")
                return self._result
        finally:
            self.close()

    def close(self) -> None:
        """Stop accepting input and release a waiter, including during cancellation."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._result = self._expected_state = None
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
