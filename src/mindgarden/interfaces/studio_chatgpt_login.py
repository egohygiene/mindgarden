"""One per-visit native browser consent flow with a cached public status."""

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from threading import Event, RLock, Thread
from time import monotonic_ns
import webbrowser

from ..application import chatgpt_connection
from ..domain.validation import ContractError
from .chatgpt_callback import LocalChatGPTCallback


BROWSER_START_TIMEOUT = 1.0
SAFE_ERRORS = frozenset({
    "CHATGPT_BROWSER", "CHATGPT_CALLBACK", "CHATGPT_CALLBACK_CANCELLED", "CHATGPT_CALLBACK_TIMEOUT",
    "CHATGPT_CALLBACK_PROVIDER", "CHATGPT_CALLBACK_RESPONSE", "CHATGPT_CONSENT_DENIED", "CHATGPT_OWNER_MISMATCH", "CHATGPT_STATE_BUSY", "CHATGPT_STATE_CHANGED",
    "CHATGPT_STATE_INVALID", "CHATGPT_STATE_UNAVAILABLE",
    "CHATGPT_OAUTH_ATTEMPT", "CHATGPT_OAUTH_CALLBACK", "CHATGPT_OAUTH_CLIENT", "CHATGPT_OAUTH_DENIED",
    "CHATGPT_OAUTH_DEPENDENCY", "CHATGPT_OAUTH_ENDPOINT", "CHATGPT_OAUTH_IDENTITY", "CHATGPT_OAUTH_LIMIT",
    "CHATGPT_OAUTH_RESPONSE", "CHATGPT_OAUTH_SCOPE", "CHATGPT_OAUTH_UNAVAILABLE",
    "SESSION_EXPIRED", "SESSION_REVOKED", "SESSION_STALE", "SESSION_CONFIGURATION", "SESSION_REVISION",
})


@dataclass
class _Attempt:
    started: int = field(default_factory=monotonic_ns)
    listener: LocalChatGPTCallback | None = None
    cancelled: bool = False
    committed: bool = False


def _error_code(error: Exception) -> str:
    if isinstance(error, ContractError):
        code = str(error).partition(":")[0]
        if code in SAFE_ERRORS:
            return code
    return "CHATGPT_LOGIN_UNAVAILABLE"


class StudioChatGPTLogin:
    def __init__(self, directory: Path, *, callback=None, browse=None, oauth=None):
        self._directory = directory
        self._callback = partial(LocalChatGPTCallback, destination="studio") if callback is None else callback
        self._browse = webbrowser.open if browse is None else browse
        self._oauth = oauth
        self._lock = RLock()
        self._closed = False
        self._disconnecting = False
        self._attempt: _Attempt | None = None
        self._status = {"status": "idle"}
        self._observe = None

    def attach_diagnostics(self, observe: Callable[[dict, int], None]) -> None:
        """Attach the visit's bounded event collector before accepting requests."""
        self._observe = observe

    def _progress(self, attempt: _Attempt, status: dict) -> None:
        self._status = status
        if self._observe is not None:
            self._observe(status, attempt.started)

    def snapshot(self) -> dict:
        with self._lock:
            if self._status["status"] == "idle":
                try:
                    if chatgpt_connection.status(self._directory)["status"] == "ready":
                        return {"status": "authorized"}
                except ContractError as error:
                    return {"status": "failed", "code": _error_code(error)}
            return dict(self._status)

    def _require_idle(self) -> None:
        if self._closed:
            raise ContractError("CHATGPT_LOGIN_UNAVAILABLE: restart the local Studio visit")
        if self._attempt is not None or self._disconnecting:
            raise ContractError("CHATGPT_STATE_BUSY: another owner transition is in progress")

    def start(self, guard: Callable[[], None], invalidate: Callable[[], None]) -> dict:
        """Launch the native browser in a worker after an explicit local action."""
        guard()
        with self._lock:
            self._require_idle()
            attempt = _Attempt()
            self._attempt = attempt
            self._progress(attempt, {"status": "opening"})
            worker = Thread(target=self._connect, args=(attempt, guard, invalidate), daemon=True,
                            name="mindgarden-studio-chatgpt-login")
            try:
                worker.start()
            except RuntimeError:
                self._attempt = None
                self._progress(attempt, {"status": "failed", "code": "CHATGPT_LOGIN_UNAVAILABLE"})
            return dict(self._status)

    def _require_pending(self, attempt: _Attempt) -> None:
        if self._closed or self._attempt is not attempt or attempt.cancelled:
            raise ContractError("CHATGPT_CALLBACK_CANCELLED: local sign-in was cancelled")

    def _open(self, attempt: _Attempt, url: str, verify: Callable[[], None]) -> bool:
        completed = Event()
        accepted = False

        def launch() -> None:
            nonlocal accepted
            try:
                with self._lock:
                    self._require_pending(attempt)
                accepted = bool(self._browse(url))
            except Exception:
                accepted = False
            finally:
                completed.set()

        # Some system browser launchers synchronously wait for the browser to
        # quit. The separate opener cannot keep the callback or store lease alive.
        verify()
        Thread(target=launch, daemon=True, name="mindgarden-chatgpt-open-browser").start()
        finished = completed.wait(BROWSER_START_TIMEOUT)
        verify()
        opened = not finished or accepted
        with self._lock:
            self._require_pending(attempt)
            if opened:
                self._progress(attempt, {"status": "waiting"})
        return opened

    def _connect(self, attempt: _Attempt, guard: Callable[[], None], invalidate: Callable[[], None]) -> None:
        def verify() -> None:
            with self._lock:
                self._require_pending(attempt)
            guard()
            with self._lock:
                self._require_pending(attempt)

        @contextmanager
        def callback():
            with self._callback() as listener:
                with self._lock:
                    self._require_pending(attempt)
                    attempt.listener = listener
                try:
                    yield listener
                finally:
                    with self._lock:
                        attempt.listener = None

        def verifying() -> None:
            with self._lock:
                self._require_pending(attempt)
                self._progress(attempt, {"status": "verifying"})

        @contextmanager
        def committing():
            # The consent thread owns the credential writer lease. Serialize
            # only its final guard and atomic save against UI cancel/close.
            with self._lock:
                self._require_pending(attempt)
                yield
                attempt.committed = True

        try:
            chatgpt_connection.connect(
                self._directory, callback=callback, browse=lambda url: self._open(attempt, url, verify),
                oauth=self._oauth, guard=verify, on_callback=verifying, committing=committing,
            )
            invalidate()
            status = {"status": "authorized"}
        except Exception as error:
            code = _error_code(error)
            status = {"status": "cancelled"} if code == "CHATGPT_CALLBACK_CANCELLED" else {"status": "failed", "code": code}
        with self._lock:
            if not self._closed and not attempt.cancelled:
                self._progress(attempt, status)
            self._attempt = None

    def _cancel_pending(self) -> LocalChatGPTCallback | None:
        attempt = self._attempt
        if attempt is None or attempt.committed:
            return None
        attempt.cancelled = True
        self._status = {"status": "cancelled"}
        return attempt.listener

    def cancel(self) -> dict:
        with self._lock:
            listener = self._cancel_pending()
            status = dict(self._status)
        if listener is not None:
            listener.close()
        return status

    def disconnect(self, guard: Callable[[], None], invalidate: Callable[[], None]) -> dict:
        """Explicitly revoke the current registration's tokens and clear the cache."""
        guard()
        with self._lock:
            self._require_idle()
            self._disconnecting = True

        def verify() -> None:
            with self._lock:
                if self._closed:
                    raise ContractError("CHATGPT_LOGIN_UNAVAILABLE: restart the local Studio visit")
            guard()

        status = None
        try:
            report = chatgpt_connection.disconnect(self._directory, oauth=self._oauth, guard=verify)
            invalidate()
            status = {"status": "signed-out", "remote_revocation": report["remote_revocation"]}
        except Exception as error:
            status = {"status": "failed", "code": _error_code(error)}
        finally:
            with self._lock:
                self._disconnecting = False
                if not self._closed and status is not None:
                    self._status = status
        return self.snapshot()

    def close(self) -> None:
        with self._lock:
            self._closed = True
            listener = self._cancel_pending()
        if listener is not None:
            listener.close()
