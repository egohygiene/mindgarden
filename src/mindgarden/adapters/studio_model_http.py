"""Bounded, text-only HTTP adapters for Studio's synthetic model check."""

from http.client import HTTPConnection, HTTPException, HTTPSConnection
import os
import re
from socket import SHUT_RDWR
from threading import Timer
from time import monotonic
from urllib.parse import urlencode

from ..domain.contracts import canonical_json, strict_json
from ..domain.validation import ContractError


GEMINI_HOST = "generativelanguage.googleapis.com"
OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434
GEMINI_RESOURCE = re.compile(r"models/[a-zA-Z0-9][a-zA-Z0-9._-]{0,120}")
OLLAMA_TAG = re.compile(
    r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}(?:/[a-zA-Z0-9][a-zA-Z0-9._-]{0,63})?"
    r"(?::[a-zA-Z0-9][a-zA-Z0-9._-]{0,63})?"
)
OLLAMA_DOWNLOADS = (
    ("gemma3:1b", "Gemma 3 (1B)"),
    ("gemma4:e2b", "Gemma 4 (E2B)"),
)
LIST_TIMEOUT = 8
RUN_TIMEOUT = 55
INSTALL_TIMEOUT = 300
LIST_LIMIT = 512 * 1024
RUN_LIMIT = 96 * 1024
PULL_LIMIT = 16 * 1024
TEXT_LIMIT = 16 * 1024
TOKEN_LIMIT = 1024
GEMINI_TEXT_DISALLOWED_PARTS = frozenset(
    {
        "functionCall",
        "functionResponse",
        "toolCall",
        "toolResponse",
        "executableCode",
        "codeExecutionResult",
        "inlineData",
        "fileData",
    }
)


class _JsonEndpoint:
    def __init__(self, host, port, connection):
        self.host = host
        self.port = port
        self.connection = connection

    def request(self, path, *, payload=None, api_key=None, seconds, limit):
        deadline = monotonic() + seconds
        headers = {"Accept": "application/json", "Accept-Encoding": "identity"}
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = canonical_json(payload)
        if api_key is not None:
            headers["x-goog-api-key"] = api_key

        # http.client has no redirect handling and does not consult proxy settings.
        connection = self.connection(self.host, self.port, timeout=seconds)
        watchdog = None
        try:
            connection.connect()
            socket = connection.sock
            remaining = _remaining(deadline)
            # A socket timeout bounds each idle operation. The watchdog also bounds a
            # response that keeps sending small fragments, including its headers.
            watchdog = Timer(remaining, _interrupt_socket, args=(socket,))
            watchdog.daemon = True
            watchdog.start()
            socket.settimeout(remaining)
            connection.request("GET" if body is None else "POST", path, body, headers)
            socket.settimeout(_remaining(deadline))
            with connection.getresponse() as response:
                if response.status == 429:
                    raise ContractError(
                        "MODEL_QUOTA: the provider's request limit was reached"
                    )
                if response.status != 200:
                    raise ContractError(
                        "MODEL_UNAVAILABLE: the provider did not accept this request"
                    )
                raw = _read_body(response, socket, deadline, limit)
        except (OSError, HTTPException):
            raise ContractError(
                "MODEL_UNAVAILABLE: the provider did not respond within the connection limits"
            ) from None
        finally:
            if watchdog is not None:
                watchdog.cancel()
            connection.close()

        try:
            value = strict_json(raw)
        except ContractError:
            raise ContractError(
                "MODEL_UNAVAILABLE: the provider response was not valid JSON"
            ) from None
        if not isinstance(value, dict):
            raise ContractError(
                "MODEL_UNAVAILABLE: the provider response was not a JSON object"
            )
        return value


def _interrupt_socket(socket):
    try:
        socket.shutdown(SHUT_RDWR)
    except OSError:
        pass


def _remaining(deadline):
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise TimeoutError
    return remaining


def _read_body(response, socket, deadline, limit):
    encoding = response.getheader("Content-Encoding", "identity")
    content_type = (
        response.getheader("Content-Type", "").partition(";")[0].strip().lower()
    )
    declared = response.getheader("Content-Length")
    if encoding not in ("", "identity") or content_type != "application/json":
        raise ContractError(
            "MODEL_UNAVAILABLE: the provider response used an unexpected format"
        )
    if declared is not None and (
        not re.fullmatch(r"[0-9]{1,9}", declared) or int(declared) > limit
    ):
        raise ContractError(
            "MODEL_UNAVAILABLE: the provider response exceeded its byte limit"
        )
    raw = bytearray()
    while len(raw) <= limit:
        socket.settimeout(_remaining(deadline))
        chunk = response.read1(min(16384, limit + 1 - len(raw)))
        if not chunk:
            break
        raw.extend(chunk)
    _remaining(deadline)
    if len(raw) > limit or declared is not None and int(declared) != len(raw):
        raise ContractError(
            "MODEL_UNAVAILABLE: the provider response exceeded its limit or was incomplete"
        )
    return bytes(raw)


def _status(status, detail, models=None):
    return {
        "status": status,
        "detail": detail,
        "models": models or [],
        "can_run": bool(models),
    }


def _validate_prompt(prompt):
    if not _bounded_text(prompt):
        raise ContractError(
            "MODEL_UNAVAILABLE: the fictional prompt is missing or exceeds its byte limit"
        )


def _bounded_text(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        return len(value.encode("utf-8")) <= TEXT_LIMIT
    except UnicodeError:
        return False


def _answer_text(value):
    if not _bounded_text(value):
        raise ContractError(
            "MODEL_UNAVAILABLE: the provider returned no bounded text answer"
        )
    return value.strip()


class GeminiProvider:
    id = "gemini"
    name = "Gemini Developer API"
    disclosure = "cloud"

    def __init__(self, *, api_key=None, endpoint=None):
        self._api_key = (
            os.environ.get("GEMINI_API_KEY", "") if api_key is None else api_key
        )
        self._endpoint = endpoint or _JsonEndpoint(GEMINI_HOST, 443, HTTPSConnection)

    def _key(self):
        if not isinstance(self._api_key, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{1,256}", self._api_key
        ):
            raise ContractError(
                "MODEL_NOT_CONFIGURED: set a valid GEMINI_API_KEY in the server environment"
            )
        return self._api_key

    def check(self):
        try:
            key = self._key()
        except ContractError as error:
            return _status("unconfigured", str(error))
        try:
            models = self._models(key)
        except ContractError as error:
            return _status("unavailable", str(error))
        return _status(
            "ready",
            "Gemini lists generation models for this project."
            if models
            else "Gemini listed no compatible generation models for this project.",
            models,
        )

    def _models(self, key):
        token = None
        seen = set()
        models = {}
        deadline = monotonic() + LIST_TIMEOUT
        for _ in range(3):
            params = {"pageSize": 100}
            if token is not None:
                params["pageToken"] = token
            remaining = deadline - monotonic()
            if remaining <= 0:
                break
            result = self._endpoint.request(
                "/v1/models?" + urlencode(params),
                api_key=key,
                seconds=remaining,
                limit=LIST_LIMIT,
            )
            rows = result.get("models", [])
            if not isinstance(rows, list) or len(rows) > 100 or "error" in result:
                break
            for row in rows:
                if not isinstance(row, dict):
                    continue
                model = row.get("name")
                methods = row.get("supportedGenerationMethods", [])
                if (
                    not isinstance(model, str)
                    or not GEMINI_RESOURCE.fullmatch(model)
                    or not isinstance(methods, list)
                    or "generateContent" not in methods
                ):
                    continue
                label = row.get("displayName")
                if (
                    not isinstance(label, str)
                    or not label.isprintable()
                    or len(label) > 100
                ):
                    label = model.removeprefix("models/")
                models[model] = {"id": model, "label": label}
            token = result.get("nextPageToken")
            if token in (None, ""):
                return [models[model] for model in sorted(models)]
            if not isinstance(token, str) or len(token) > 1024 or token in seen:
                break
            seen.add(token)
        raise ContractError("MODEL_UNAVAILABLE: Gemini model inventory was incomplete")

    def run(self, model: str, prompt: str) -> str:
        key = self._key()
        if not isinstance(model, str) or not GEMINI_RESOURCE.fullmatch(model):
            raise ContractError(
                "MODEL_UNAVAILABLE: select a listed Gemini generation model"
            )
        _validate_prompt(prompt)
        result = self._endpoint.request(
            "/v1/" + model + ":generateContent",
            api_key=key,
            payload={
                "store": False,
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "candidateCount": 1,
                    "maxOutputTokens": TOKEN_LIMIT,
                    "responseModalities": ["TEXT"],
                },
            },
            seconds=RUN_TIMEOUT,
            limit=RUN_LIMIT,
        )
        return _gemini_text(result)


def _gemini_text(result):
    candidates = result.get("candidates")
    feedback = result.get("promptFeedback", {})
    if (
        "error" in result
        or not isinstance(feedback, dict)
        or feedback.get("blockReason") not in (None, "", "BLOCK_REASON_UNSPECIFIED")
        or not isinstance(candidates, list)
        or len(candidates) != 1
        or not isinstance(candidates[0], dict)
        or candidates[0].get("finishReason") != "STOP"
    ):
        raise ContractError(
            "MODEL_UNAVAILABLE: Gemini did not return a complete text answer"
        )
    content = candidates[0].get("content")
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list) or not parts:
        raise ContractError(
            "MODEL_UNAVAILABLE: Gemini did not return a complete text answer"
        )
    text = []
    for part in parts:
        if not isinstance(part, dict) or GEMINI_TEXT_DISALLOWED_PARTS & part.keys():
            raise ContractError(
                "MODEL_UNAVAILABLE: Gemini returned unexpected non-text output"
            )
        if part.get("thought") is True:
            continue
        if not isinstance(part.get("text"), str):
            raise ContractError(
                "MODEL_UNAVAILABLE: Gemini returned unexpected non-text output"
            )
        text.append(part["text"])
    return _answer_text("".join(text))


def _local_tag(tag):
    return (
        isinstance(tag, str)
        and len(tag) <= 128
        and OLLAMA_TAG.fullmatch(tag) is not None
        and "cloud" not in re.split(r"[^a-z0-9]+", tag.lower())
    )


def _remote_model(row):
    return any(
        row.get(field) not in (None, "") for field in ("remote_model", "remote_host")
    )


class OllamaProvider:
    id = "ollama"
    name = "Ollama"
    disclosure = "loopback"

    def __init__(self, *, endpoint=None):
        self._endpoint = endpoint or _JsonEndpoint(
            OLLAMA_HOST, OLLAMA_PORT, HTTPConnection
        )

    @property
    def downloadable(self):
        return [{"id": model, "label": label} for model, label in OLLAMA_DOWNLOADS]

    def _models(self):
        result = self._endpoint.request(
            "/api/tags", seconds=LIST_TIMEOUT, limit=LIST_LIMIT
        )
        rows = result.get("models")
        if "error" in result or not isinstance(rows, list) or len(rows) > 250:
            raise ContractError(
                "MODEL_UNAVAILABLE: Ollama model inventory was incomplete"
            )
        local = set()
        for row in rows:
            if not isinstance(row, dict) or _remote_model(row):
                continue
            name = row.get("name") or row.get("model")
            declared = row.get("model", name)
            if _local_tag(name) and declared == name:
                local.add(name)
        return [{"id": model, "label": model} for model in sorted(local)]

    def check(self):
        try:
            models = self._models()
        except ContractError as error:
            return {**_status("unavailable", str(error)), "downloadable": []}
        detail = (
            "Ollama has installed models."
            if models
            else "Ollama is running with no eligible installed model."
        )
        installed = {item["id"] for item in models}
        return {
            **_status("ready", detail, models),
            "downloadable": [
                item for item in self.downloadable if item["id"] not in installed
            ],
        }

    def run(self, model: str, prompt: str) -> str:
        _validate_prompt(prompt)
        if not _local_tag(model) or model not in {
            item["id"] for item in self._models()
        }:
            raise ContractError(
                "MODEL_UNAVAILABLE: select an installed Ollama model without a hosted tag"
            )
        result = self._endpoint.request(
            "/api/chat",
            payload={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "options": {"num_predict": TOKEN_LIMIT},
                "stream": False,
                "think": False,
            },
            seconds=RUN_TIMEOUT,
            limit=RUN_LIMIT,
        )
        message = result.get("message")
        if (
            "error" in result
            or _remote_model(result)
            or result.get("done") is not True
            or result.get("done_reason") not in (None, "stop")
            or not isinstance(message, dict)
            or message.get("role") != "assistant"
            or message.get("tool_calls") not in (None, [])
            or message.get("images") not in (None, [])
        ):
            raise ContractError(
                "MODEL_UNAVAILABLE: Ollama did not return a complete text answer"
            )
        return _answer_text(message.get("content"))

    def install(self, model: str) -> None:
        if model not in {item["id"] for item in self.downloadable}:
            raise ContractError("MODEL_UNAVAILABLE: select a supported Ollama download")
        result = self._endpoint.request(
            "/api/pull",
            payload={"model": model, "stream": False, "insecure": False},
            seconds=INSTALL_TIMEOUT,
            limit=PULL_LIMIT,
        )
        if "error" in result or result.get("status") != "success":
            raise ContractError(
                "MODEL_UNAVAILABLE: Ollama did not confirm the model download"
            )
