"""Fixed, short-lived operation events for one local Studio visit."""

from collections import deque
from threading import Lock
from time import monotonic_ns, time_ns

from ..application.model_lab import CATALOG_CODES
from ..domain.validation import ContractError
from .studio_chatgpt_login import SAFE_ERRORS as CHATGPT_ERRORS


CAPACITY = 80
PROVIDERS = frozenset({"chatgpt", "codex", "gemini", "ollama", "studio"})
OPERATIONS = frozenset({"check", "run", "install", "sign-in", "cancel", "disconnect", "sources"})
OK_CODES = frozenset({
    "MODEL_CHECK_OK", "MODEL_RUN_OK", "MODEL_INSTALL_OK", "SOURCES_OK",
    "CHATGPT_LOGIN_OPENING", "CHATGPT_LOGIN_WAITING", "CHATGPT_LOGIN_VERIFYING",
    "CHATGPT_LOGIN_AUTHORIZED", "CHATGPT_LOGIN_SIGNED_OUT",
})
ATTENTION_CODES = frozenset({
    "MODEL_REAUTH", "MODEL_NOT_CONFIGURED", "MODEL_QUOTA", "MODEL_INVALID", "MODEL_REVIEW", "MODEL_BUSY",
    "MODEL_CATALOG_EMPTY", "MODEL_CATALOG_NO_ENTITLEMENT", "MODEL_CHECK_SUPERSEDED", "PROJECTION_DENIED",
    "CHATGPT_LOGIN_CANCELLED", "CHATGPT_LOGIN_IDLE", "CHATGPT_LOGIN_REVOCATION_UNCONFIRMED", "CHATGPT_CONSENT_DENIED",
    "CHATGPT_CALLBACK_CANCELLED", "CHATGPT_STATE_BUSY",
})
ERROR_CODES = CHATGPT_ERRORS | {
    "MODEL_UNAVAILABLE", "MODEL_CATALOG_TRANSPORT", "MODEL_CATALOG_HTTP", "MODEL_CATALOG_RESPONSE",
    "MODEL_CATALOG_FORBIDDEN", "MODEL_CATALOG_SERVICE_UNAVAILABLE",
    "CHATGPT_LOGIN_UNAVAILABLE", "SESSION_REVISION", "WRITE_LOCKED", "QUERY_INTEGRITY", "QUERY_BUDGET",
    "DIAGNOSTIC_UNAVAILABLE",
}
ALL_CODES = OK_CODES | ATTENTION_CODES | ERROR_CODES


def safe_code(code, allowed):
    return code if type(code) is str and code in allowed else "DIAGNOSTIC_UNAVAILABLE"


def model_check_code(provider, snapshot):
    for state in snapshot.get("providers", []):
        if state.get("id") != provider:
            continue
        if "diagnostic_code" in state:
            return safe_code(state["diagnostic_code"], CATALOG_CODES)
        status = state.get("status")
        if type(status) is not str:
            return "DIAGNOSTIC_UNAVAILABLE"
        if status == "ready":
            return "MODEL_CHECK_OK" if provider == "codex" or state.get("models") else "MODEL_CATALOG_EMPTY"
        return {
            "unchecked": "MODEL_CHECK_SUPERSEDED",
            "unconfigured": "MODEL_NOT_CONFIGURED",
            "unavailable": "MODEL_UNAVAILABLE",
        }.get(status, "DIAGNOSTIC_UNAVAILABLE")
    return "DIAGNOSTIC_UNAVAILABLE"


def login_status_code(status):
    if status.get("status") == "failed":
        return safe_code(status.get("code"), CHATGPT_ERRORS | {"CHATGPT_LOGIN_UNAVAILABLE"})
    return {
        "opening": "CHATGPT_LOGIN_OPENING",
        "waiting": "CHATGPT_LOGIN_WAITING",
        "verifying": "CHATGPT_LOGIN_VERIFYING",
        "authorized": "CHATGPT_LOGIN_AUTHORIZED",
        "cancelled": "CHATGPT_LOGIN_CANCELLED",
    }.get(status.get("status"), "CHATGPT_LOGIN_IDLE")


def login_action_code(operation, status):
    if status.get("status") == "failed":
        return login_status_code(status)
    if operation == "cancel" and status.get("status") == "cancelled":
        return "CHATGPT_LOGIN_CANCELLED"
    if operation == "disconnect" and status.get("status") == "signed-out":
        return ("CHATGPT_LOGIN_REVOCATION_UNCONFIRMED" if status.get("remote_revocation") == "unconfirmed"
                else "CHATGPT_LOGIN_SIGNED_OUT")
    return "CHATGPT_LOGIN_IDLE"


class StudioDiagnostics:
    def __init__(self):
        self._events = deque(maxlen=CAPACITY)
        self._next_id = 1
        self._lock = Lock()

    def record(self, provider, operation, code, started):
        if type(operation) is not str or operation not in OPERATIONS:
            return
        provider = provider if type(provider) is str and provider in PROVIDERS else "studio"
        code = safe_code(code, ALL_CODES)
        outcome = "ok" if code in OK_CODES else "attention" if code in ATTENTION_CODES else "error"
        with self._lock:
            self._events.append({
                "id": self._next_id, "source": "server", "provider": provider, "operation": operation,
                "outcome": outcome, "code": code, "at_ms": time_ns() // 1_000_000,
                "duration_ms": (monotonic_ns() - started) // 1_000_000,
            })
            self._next_id += 1

    def observe(self, provider, operation, action, outcome):
        started = monotonic_ns()
        try:
            value = action()
        except (ValueError, OSError) as error:
            code = str(error).partition(":")[0] if isinstance(error, ContractError) else None
            self.record(provider, operation, code, started)
            raise
        if outcome is not None:
            self.record(provider, operation, outcome(value), started)
        return value

    def sign_in(self, status, started):
        self.record("chatgpt", "sign-in", login_status_code(status), started)

    def snapshot(self):
        with self._lock:
            return {"events": [dict(event) for event in self._events], "capacity": CAPACITY}
