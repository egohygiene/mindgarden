"""Operator-triggered status through the local Codex App Server."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic


TIMEOUT_SECONDS = 8
MAX_RESPONSE_BYTES = 65_536
PLAN_LABELS = {
    "free": "Free",
    "go": "Go",
    "plus": "Plus",
    "pro": "Pro",
    "team": "Team",
    "business": "Business",
    "enterprise": "Enterprise",
    "edu": "Edu",
}
BALANCE = re.compile(r"[0-9]{1,16}(?:\.[0-9]{1,8})?")
LOCAL_ENVIRONMENT = (
    "HOME",
    "CODEX_HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "LC_ALL",
    "DBUS_SESSION_BUS_ADDRESS",
    "XDG_RUNTIME_DIR",
)


class _Unavailable(Exception):
    pass


class _RpcRejected(_Unavailable):
    pass


def _status(status, detail):
    return {"status": status, "detail": detail, "models": [], "can_run": False}


def _quota_window(snapshot, field, label):
    window = snapshot.get(field)
    if not isinstance(window, dict):
        return None
    used = window.get("usedPercent")
    if type(used) is not int or not 0 <= used <= 100:
        return None
    result = {"label": label, "used_percent": used}
    duration = window.get("windowDurationMins")
    if type(duration) is int and 0 < duration <= 525_600:
        result["window_minutes"] = duration
    reset = window.get("resetsAt")
    if type(reset) is int and 0 < reset <= 253_402_300_799:
        result["resets_at"] = reset
    return result


def _limits(result):
    snapshot = result.get("rateLimits")
    if not isinstance(snapshot, dict):
        return None
    windows = []
    for field, label in (
        ("primary", "Primary quota"),
        ("secondary", "Secondary quota"),
    ):
        if window := _quota_window(snapshot, field, label):
            windows.append(window)
    limits = {"windows": windows}
    credits = snapshot.get("credits")
    if (
        isinstance(credits, dict)
        and type(credits.get("hasCredits")) is bool
        and type(credits.get("unlimited")) is bool
    ):
        balance = credits.get("balance")
        limits["credits"] = {
            "has_credits": credits["hasCredits"],
            "unlimited": credits["unlimited"],
            "balance": balance
            if isinstance(balance, str) and BALANCE.fullmatch(balance)
            else None,
        }
    return limits if windows or "credits" in limits else None


class _AccountConnection:
    def __init__(self, process):
        self.process = process
        self.deadline = monotonic() + TIMEOUT_SECONDS
        self.pending = bytearray()
        self.received = 0
        self.request_id = 0

    def _send(self, frame):
        message = json.dumps(frame, separators=(",", ":")).encode() + b"\n"
        self.process.stdin.write(message)

    def _receive(self):
        descriptor = self.process.stdout.fileno()
        while b"\n" not in self.pending:
            delay = self.deadline - monotonic()
            if delay <= 0 or not select.select([descriptor], [], [], delay)[0]:
                raise _Unavailable
            chunk = os.read(
                descriptor, min(4096, MAX_RESPONSE_BYTES + 1 - self.received)
            )
            self.received += len(chunk)
            if not chunk or self.received > MAX_RESPONSE_BYTES:
                raise _Unavailable
            self.pending.extend(chunk)
        line, _, self.pending = self.pending.partition(b"\n")
        frame = json.loads(line)
        if not isinstance(frame, dict):
            raise _Unavailable
        return frame

    def request(self, method, **params):
        self.request_id += 1
        self._send({"id": self.request_id, "method": method, "params": params})
        while True:
            frame = self._receive()
            if "id" not in frame and isinstance(frame.get("method"), str):
                continue
            if type(frame.get("id")) is not int or frame["id"] != self.request_id:
                raise _Unavailable
            if "error" in frame:
                raise _RpcRejected
            if not isinstance(frame.get("result"), dict):
                raise _Unavailable
            return frame["result"]

    def initialize(self):
        response = self.request(
            "initialize",
            clientInfo={"name": "mindgarden_studio", "version": "0.1.0"},
        )
        if not isinstance(response.get("userAgent"), str) or not response["userAgent"]:
            raise _Unavailable
        self._send({"method": "initialized", "params": {}})


def _command(executable, workspace):
    # These overrides keep the status process on the stock OpenAI path. The
    # local credential store stays on the runtime's existing configuration.
    command = [executable, "app-server", "--listen", "stdio://", "--strict-config"]
    for feature in (
        "hooks",
        "plugins",
        "remote_plugin",
        "apps",
        "code_mode_host",
        "shell_tool",
        "workspace_dependencies",
    ):
        command.extend(("--disable", feature))
    settings = (
        "analytics.enabled=false",
        "check_for_update_on_startup=false",
        'otel.exporter="none"',
        'otel.trace_exporter="none"',
        'otel.metrics_exporter="none"',
        'history.persistence="none"',
        'model_provider="openai"',
        'chatgpt_base_url="https://chatgpt.com/backend-api/"',
        "log_dir=" + json.dumps(str(Path(workspace) / "log")),
    )
    for setting in settings:
        command.extend(("--config", setting))
    return command


@contextmanager
def _account_process(executable):
    with TemporaryDirectory(prefix="mindgarden-codex-status-") as workspace:
        environment = {
            key: os.environ[key] for key in LOCAL_ENVIRONMENT if key in os.environ
        }
        # npm's Codex launcher uses /usr/bin/env node. Preserve the operator's
        # absolute search paths without resolving relative entries in the scratch directory.
        environment["PATH"] = os.pathsep.join(
            entry
            for entry in os.environ.get("PATH", os.defpath).split(os.pathsep)
            if os.path.isabs(entry)
        )
        # This is the disabled startup marker used by the tested Codex CLI.
        environment["CODEX_INTERNAL_APP_SERVER_REMOTE_CONTROL_DISABLED"] = "1"
        process = subprocess.Popen(
            _command(executable, workspace),
            cwd=workspace,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
            start_new_session=True,
        )
        try:
            yield _AccountConnection(process)
        finally:
            process.stdin.close()
            process.stdout.close()
            try:
                process.wait(timeout=0.25)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=1)


class CodexProvider:
    """Check recognized local auth and ChatGPT quota without opening a turn."""

    id = "codex"
    name = "Codex"
    disclosure = "cloud"

    def check(self):
        if sys.platform not in {"darwin", "linux"}:
            return _status(
                "unavailable", "The Codex status check requires macOS or Linux."
            )
        if not (executable := shutil.which("codex")):
            return _status(
                "unavailable", "Install the Codex CLI to check local sign-in."
            )

        try:
            with _account_process(str(Path(executable).absolute())) as connection:
                connection.initialize()
                snapshot = connection.request("account/read", refreshToken=False)
                if type(snapshot.get("requiresOpenaiAuth")) is not bool:
                    raise _Unavailable
                account = snapshot.get("account")
                if account is None and "account" in snapshot:
                    return _status(
                        "unconfigured",
                        "Sign in through the local Codex CLI, then check again.",
                    )
                if not isinstance(account, dict):
                    raise _Unavailable
                if account.get("type") == "apiKey":
                    return _status(
                        "ready",
                        "Codex reports a local API key. Uses API billing. Studio turns require a qualified runtime boundary.",
                    )
                if (
                    account.get("type") != "chatgpt"
                    or snapshot["requiresOpenaiAuth"] is False
                ):
                    return _status(
                        "unavailable",
                        "The active Codex authentication mode is unsupported here.",
                    )
                plan = account.get("planType")
                label = PLAN_LABELS.get(plan) if isinstance(plan, str) else None
                sign_in = "ChatGPT sign-in" + (f" ({label})" if label else "")
                result = _status(
                    "ready",
                    f"Codex reports local {sign_in}. Studio turns require a qualified runtime boundary.",
                )
                try:
                    limits = _limits(connection.request("account/rateLimits/read"))
                except (
                    _RpcRejected,
                    _Unavailable,
                    OSError,
                    ValueError,
                    RecursionError,
                ):
                    limits = None
                if limits is None:
                    result["detail"] += " Quota details are unavailable."
                else:
                    result["limits"] = limits
                return result
        except (
            _Unavailable,
            OSError,
            subprocess.SubprocessError,
            ValueError,
            RecursionError,
        ):
            return _status(
                "unavailable", "Codex did not return a usable local account status."
            )
