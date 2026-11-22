"""Use a separately consented ChatGPT plan for Studio's fictional text check."""

from dataclasses import dataclass
from hashlib import sha256
from http.client import HTTPException, HTTPSConnection
from pathlib import Path
import re
from threading import Timer
from time import monotonic, time

from ..domain.contracts import canonical_json, strict_json
from ..domain.validation import ContractError
from .chatgpt_credentials import MAX_TOKEN_LENGTH, ChatGPTCredentials, ChatGPTStore
from .chatgpt_oauth import ISSUER, _client_id
from .studio_model_http import (
    LIST_LIMIT,
    LIST_TIMEOUT,
    RUN_TIMEOUT,
    TEXT_LIMIT,
    _answer_text,
    _interrupt_socket,
    _read_body,
    _remaining,
    _status,
    _validate_prompt,
)


OPENAI_HOST = "api.openai.com"
DIRECT_SCOPE = "chatgpt.tokens.use.direct"
RESOURCE_SCOPE = "resource.invoke"
REQUIRED_SCOPES = frozenset({DIRECT_SCOPE, RESOURCE_SCOPE})
MODEL_SLUG = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}")
BEARER_TOKEN = re.compile(r"[a-zA-Z0-9._~+/\-]+=*")
MAX_MODELS = 250
ERROR_LIMIT = 8 * 1024
STREAM_LIMIT = 512 * 1024
EVENT_LIMIT = 96 * 1024
MAX_EVENTS = 1024
CATALOG_DETAILS = {
    "MODEL_NOT_CONFIGURED": "Sign in and allow direct ChatGPT plan use before checking models.",
    "MODEL_REAUTH": "Renew the local ChatGPT sign-in and check the connection again.",
    "MODEL_QUOTA": "ChatGPT plan use reached a limit. Check ChatGPT settings Usage.",
    "MODEL_UNAVAILABLE": "The local ChatGPT sign-in could not be verified.",
    "MODEL_CATALOG_EMPTY": "ChatGPT listed no available models for this plan.",
    "MODEL_CATALOG_NO_ENTITLEMENT": "ChatGPT reported that this account is ineligible for direct plan use.",
    "MODEL_CATALOG_TRANSPORT": "The bounded ChatGPT catalog connection did not complete.",
    "MODEL_CATALOG_HTTP": "ChatGPT did not accept the catalog request.",
    "MODEL_CATALOG_FORBIDDEN": "ChatGPT refused access to the model catalog.",
    "MODEL_CATALOG_SERVICE_UNAVAILABLE": "The ChatGPT model catalog service was unavailable.",
    "MODEL_CATALOG_RESPONSE": "The ChatGPT catalog response could not be verified.",
}
LIFECYCLE_EVENTS = frozenset(
    {"response.created", "response.queued", "response.in_progress"}
)
REASONING_EVENTS = frozenset(
    {
        "response.reasoning_summary_part.added",
        "response.reasoning_summary_part.done",
        "response.reasoning_summary_text.delta",
        "response.reasoning_summary_text.done",
        "response.reasoning_text.delta",
        "response.reasoning_text.done",
    }
)


@dataclass(frozen=True)
class _Catalog:
    issuer: str
    subject: str
    client_id: str
    scopes: tuple[str, ...]
    expires_at: int
    token_digest: bytes
    models: frozenset[str]


class _CatalogError(ContractError):
    def __init__(self, code):
        super().__init__("MODEL_UNAVAILABLE: " + CATALOG_DETAILS[code])
        self.code = code


def _catalog(credentials: ChatGPTCredentials, models: frozenset[str]) -> _Catalog:
    return _Catalog(
        credentials.issuer,
        credentials.subject,
        credentials.client_id,
        tuple(sorted(credentials.scopes)),
        credentials.expires_at,
        sha256(credentials.access_token.encode("ascii")).digest(),
        models,
    )


class ChatGPTProvider:
    id = "chatgpt"
    name = "ChatGPT plan"
    disclosure = "cloud"

    def __init__(self, state_directory: Path, *, store=None, endpoint=None, clock=time):
        self._store = ChatGPTStore(state_directory) if store is None else store
        self._endpoint = _ChatGPTEndpoint() if endpoint is None else endpoint
        self._clock = clock
        self._catalog = None

    def _credentials(self) -> ChatGPTCredentials:
        try:
            credentials = self._store.read()
        except (ContractError, OSError):
            raise ContractError(
                "MODEL_UNAVAILABLE: the local ChatGPT sign-in could not be read"
            ) from None
        if credentials is None or not REQUIRED_SCOPES.issubset(credentials.scopes):
            raise ContractError(
                "MODEL_NOT_CONFIGURED: enable direct ChatGPT plan use in the CLI"
            )
        if (
            credentials.issuer != ISSUER
            or not _client_id(credentials.client_id)
            or credentials.expires_at <= self._clock()
            or len(credentials.access_token) > MAX_TOKEN_LENGTH
            or not BEARER_TOKEN.fullmatch(credentials.access_token)
        ):
            raise ContractError(
                "MODEL_REAUTH: refresh or renew the ChatGPT sign-in in the CLI"
            )
        return credentials

    def check(self):
        self._catalog = None
        try:
            credentials = self._credentials()
            models = _listed_models(self._endpoint.models(credentials.access_token))
            model_ids = frozenset(item["id"] for item in models)
            catalog = _catalog(credentials, model_ids)
            self._selected_credentials(catalog)
        except (ContractError, OSError) as error:
            if isinstance(error, _CatalogError):
                code = error.code
            elif isinstance(error, OSError):
                code = "MODEL_CATALOG_TRANSPORT"
            else:
                code = str(error).partition(":")[0]
            status = (
                "unconfigured"
                if code in {"MODEL_NOT_CONFIGURED", "MODEL_REAUTH"}
                else "unavailable"
            )
            if code not in CATALOG_DETAILS:
                code = "MODEL_UNAVAILABLE"
            return {**_status(status, CATALOG_DETAILS[code]), "diagnostic_code": code}
        self._catalog = catalog
        if not models:
            return {**_status("ready", CATALOG_DETAILS["MODEL_CATALOG_EMPTY"]),
                    "diagnostic_code": "MODEL_CATALOG_EMPTY"}
        return _status("ready", "ChatGPT lists models for the signed-in plan.", models)

    def _selected_credentials(self, catalog: _Catalog) -> ChatGPTCredentials:
        try:
            credentials = self._credentials()
            if catalog == _catalog(credentials, catalog.models):
                return credentials
        except ContractError:
            pass
        self._catalog = None
        raise ContractError(
            "MODEL_REAUTH: verify the current ChatGPT sign-in and check the connection again"
        ) from None

    def run(self, model: str, prompt: str) -> str:
        _validate_prompt(prompt)
        catalog = self._catalog
        if catalog is None or not isinstance(model, str) or model not in catalog.models:
            raise ContractError(
                "MODEL_INVALID: select a model from the current ChatGPT plan check"
            )
        credentials = self._selected_credentials(catalog)
        try:
            answer = self._endpoint.infer(credentials.access_token, model, prompt)
        except ContractError as error:
            if str(error).split(":", 1)[0] in {"MODEL_REAUTH", "MODEL_NOT_CONFIGURED"}:
                self._catalog = None
            raise
        # The CLI may disconnect the account or renew its token while streaming.
        self._selected_credentials(catalog)
        return answer


def _listed_models(result):
    rows = result.get("models") if isinstance(result, dict) else None
    if not isinstance(rows, list) or len(rows) > MAX_MODELS or "error" in result:
        raise _CatalogError("MODEL_CATALOG_RESPONSE")
    models = {}
    for entry in rows:
        if not isinstance(entry, dict) or entry.get("visibility") != "list":
            continue
        slug = entry.get("slug")
        label = entry.get("display_name")
        if (
            not isinstance(slug, str)
            or MODEL_SLUG.fullmatch(slug) is None
            or not isinstance(label, str)
            or not label.isprintable()
            or len(label) > 120
        ):
            continue
        models.setdefault(slug, {"id": slug, "label": label})
    return list(models.values())


def _remote_error(status=None, code=None):
    if status == 429 or code == "subscription_sharing_usage_limit_exceeded":
        return ContractError(
            "MODEL_QUOTA: ChatGPT plan use reached a limit, check ChatGPT settings Usage"
        )
    if status == 401 or code == "subscription_sharing_invalid_user":
        return ContractError(
            "MODEL_REAUTH: refresh or renew the ChatGPT sign-in in the CLI"
        )
    if code == "subscription_sharing_usage_unavailable":
        return ContractError(
            "MODEL_UNAVAILABLE: ChatGPT plan usage could not be checked"
        )
    if status == 403 or code == "subscription_sharing_user_not_eligible":
        return ContractError("MODEL_UNAVAILABLE: ChatGPT plan access was not permitted")
    return ContractError("MODEL_UNAVAILABLE: ChatGPT could not complete the request")


def _error_code(payload):
    if not isinstance(payload, dict):
        return None
    error = payload.get("error", payload)
    return error.get("code") if isinstance(error, dict) else None


def _catalog_http_error(status, code):
    error = _remote_error(status, code)
    if not str(error).startswith("MODEL_UNAVAILABLE:"):
        return error
    if code == "subscription_sharing_user_not_eligible":
        return _CatalogError("MODEL_CATALOG_NO_ENTITLEMENT")
    if status == 403:
        return _CatalogError("MODEL_CATALOG_FORBIDDEN")
    if 500 <= status <= 599:
        return _CatalogError("MODEL_CATALOG_SERVICE_UNAVAILABLE")
    return _CatalogError("MODEL_CATALOG_HTTP")


def _json(raw):
    try:
        value = strict_json(raw)
    except ContractError:
        raise ContractError(
            "MODEL_UNAVAILABLE: ChatGPT returned invalid JSON"
        ) from None
    if not isinstance(value, dict):
        raise ContractError(
            "MODEL_UNAVAILABLE: ChatGPT returned an unexpected response"
        )
    return value


class _ChatGPTEndpoint:
    def __init__(self, connection=HTTPSConnection):
        self._connection = connection

    def models(self, token):
        return self._request("/v1/models", token)

    def infer(self, token, model, prompt):
        return self._request(
            "/v1/responses",
            token,
            {
                "model": model,
                "input": [{"role": "user", "content": prompt}],
                "store": False,
                "stream": True,
            },
        )

    def _request(self, path, token, payload=None):
        streaming = payload is not None
        seconds = RUN_TIMEOUT if streaming else LIST_TIMEOUT
        deadline = monotonic() + seconds
        headers = {
            "Accept": "text/event-stream" if streaming else "application/json",
            "Accept-Encoding": "identity",
            "Authorization": "Bearer " + token,
        }
        body = None
        if streaming:
            headers["Content-Type"] = "application/json"
            body = canonical_json(payload)

        # http.client does not consult proxy settings or follow redirects.
        connection = self._connection(OPENAI_HOST, 443, timeout=seconds)
        watchdog = None
        try:
            connection.connect()
            socket = connection.sock
            remaining = _remaining(deadline)
            watchdog = Timer(remaining, _interrupt_socket, args=(socket,))
            watchdog.daemon = True
            watchdog.start()
            socket.settimeout(remaining)
            connection.request("POST" if streaming else "GET", path, body, headers)
            socket.settimeout(_remaining(deadline))
            with connection.getresponse() as response:
                status = response.status
                if status != 200:
                    code = (
                        _http_error_code(response, socket, deadline)
                        if status in {400, 403, 503}
                        else None
                    )
                    raise _remote_error(status, code) if streaming else _catalog_http_error(status, code)
                if streaming:
                    return _read_inference(response, socket, deadline)
                try:
                    return _json(_read_body(response, socket, deadline, LIST_LIMIT))
                except ContractError:
                    raise _CatalogError("MODEL_CATALOG_RESPONSE") from None
        except (HTTPException, OSError):
            if not streaming:
                raise _CatalogError("MODEL_CATALOG_TRANSPORT") from None
            raise ContractError(
                "MODEL_UNAVAILABLE: the bounded ChatGPT connection did not complete"
            ) from None
        finally:
            if watchdog is not None:
                watchdog.cancel()
            connection.close()


def _http_error_code(response, socket, deadline):
    try:
        return _error_code(_json(_read_body(response, socket, deadline, ERROR_LIMIT)))
    except (ContractError, HTTPException, OSError):
        return None


def _event_stream_chunks(response, socket, deadline):
    content_type = (
        response.getheader("Content-Type", "").partition(";")[0].strip().lower()
    )
    declared = response.getheader("Content-Length")
    if content_type != "text/event-stream" or response.getheader(
        "Content-Encoding", "identity"
    ) not in ("", "identity"):
        raise ContractError(
            "MODEL_UNAVAILABLE: ChatGPT returned an unexpected content type"
        )
    if declared is not None and (
        not re.fullmatch(r"[0-9]{1,9}", declared) or int(declared) > STREAM_LIMIT
    ):
        raise ContractError("MODEL_UNAVAILABLE: ChatGPT exceeded its body byte limit")

    received = 0
    while not response.isclosed():
        socket.settimeout(_remaining(deadline))
        chunk = response.read1(min(8192, STREAM_LIMIT + 1 - received))
        if not chunk:
            break
        received += len(chunk)
        if received > STREAM_LIMIT:
            raise ContractError(
                "MODEL_UNAVAILABLE: ChatGPT exceeded its body byte limit"
            )
        _remaining(deadline)
        yield chunk
    _remaining(deadline)
    if declared is not None and int(declared) != received:
        raise ContractError(
            "MODEL_UNAVAILABLE: the ChatGPT response body was incomplete"
        )


def _stream_lines(response, socket, deadline):
    pending = b""
    for chunk in _event_stream_chunks(response, socket, deadline):
        lines = (pending + chunk).split(b"\n")
        pending = lines.pop()
        for line in lines:
            yield line.removesuffix(b"\r")
        if len(pending) > EVENT_LIMIT:
            raise ContractError(
                "MODEL_UNAVAILABLE: ChatGPT exceeded its event byte limit"
            )


def _stream_events(lines):
    name = b""
    data = []
    size = 0
    count = 0
    for line in lines:
        size += len(line) + 1
        if size > EVENT_LIMIT or count >= MAX_EVENTS:
            raise ContractError("MODEL_UNAVAILABLE: ChatGPT exceeded its event limit")
        if not line:
            if data:
                event = _json(b"\n".join(data))
                kind = event.get("type")
                if not isinstance(kind, str) or name and name != kind.encode("utf-8"):
                    raise ContractError(
                        "MODEL_UNAVAILABLE: ChatGPT returned malformed events"
                    )
                count += 1
                yield kind, event
            name, data, size = b"", [], 0
            continue
        key, _, value = line.partition(b":")
        value = value.removeprefix(b" ")
        if key == b"data":
            data.append(value)
        elif key == b"event":
            name = value


def _text_part(part):
    if (
        not isinstance(part, dict)
        or part.get("type") != "output_text"
        or not isinstance(part.get("text"), str)
        or len(part["text"].encode("utf-8")) > TEXT_LIMIT
    ):
        raise ContractError(
            "MODEL_UNAVAILABLE: ChatGPT returned output outside the text contract"
        )
    return part["text"]


def _item_text(item):
    if isinstance(item, dict) and item.get("type") == "reasoning":
        return []
    if (
        not isinstance(item, dict)
        or item.get("type") != "message"
        or item.get("role") != "assistant"
        or not isinstance(item.get("content"), list)
    ):
        raise ContractError(
            "MODEL_UNAVAILABLE: ChatGPT returned output outside the text contract"
        )
    return [_text_part(part) for part in item["content"]]


def _response_text(response, *, completed):
    if not isinstance(response, dict) or not isinstance(response.get("output"), list):
        raise ContractError(
            "MODEL_UNAVAILABLE: ChatGPT returned an incomplete response snapshot"
        )
    if completed and (
        response.get("status") != "completed"
        or response.get("error") is not None
        or response.get("incomplete_details") is not None
    ):
        raise ContractError(
            "MODEL_UNAVAILABLE: ChatGPT returned an incomplete response snapshot"
        )
    text = "".join(
        fragment for item in response["output"] for fragment in _item_text(item)
    )
    if len(text.encode("utf-8")) > TEXT_LIMIT:
        raise ContractError("MODEL_UNAVAILABLE: ChatGPT exceeded its text output limit")
    return _answer_text(text) if completed else text


def _read_inference(response, socket, deadline):
    delta_bytes = 0
    for kind, event in _stream_events(_stream_lines(response, socket, deadline)):
        if kind == "response.completed":
            return _response_text(event.get("response"), completed=True)
        if kind == "response.failed":
            raise _remote_error(code=_error_code(event.get("response")))
        if kind == "error":
            raise _remote_error(code=_error_code(event))
        if kind == "response.incomplete":
            break
        if kind == "response.output_text.delta":
            delta = event.get("delta")
            if not isinstance(delta, str):
                break
            delta_bytes += len(delta.encode("utf-8"))
            if delta_bytes > TEXT_LIMIT:
                raise ContractError(
                    "MODEL_UNAVAILABLE: ChatGPT exceeded its text output limit"
                )
        elif kind == "response.output_text.done":
            _text_part({"type": "output_text", "text": event.get("text")})
        elif kind in {"response.output_item.added", "response.output_item.done"}:
            _item_text(event.get("item"))
        elif kind in {"response.content_part.added", "response.content_part.done"}:
            _text_part(event.get("part"))
        elif kind in LIFECYCLE_EVENTS:
            _response_text(event.get("response"), completed=False)
        elif kind not in REASONING_EVENTS:
            raise ContractError(
                "MODEL_UNAVAILABLE: ChatGPT returned an unsupported event"
            )
    raise ContractError("MODEL_UNAVAILABLE: ChatGPT ended without completed inference")
