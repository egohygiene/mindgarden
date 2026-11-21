"""A read-only loopback browser adapter over explicit query authority."""

from __future__ import annotations

from copy import deepcopy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from secrets import compare_digest, token_urlsafe
from time import sleep
from urllib.parse import parse_qs, urlsplit

from ..application.connector_evidence import connector_evidence
from ..application.evidence import resolve_evidence
from ..application.local_federation import require_private
from ..application.query import QueryContext
from ..application.retrieval import (
    build_index,
    record_key,
    render_context,
    search_payload,
)
from ..application.studio_assistant import (
    AssistantProvider,
    FixtureAssistant,
    REQUIRED_PROJECTIONS,
    ndjson,
    output_limit,
    prepare_turn,
    turn_lines,
)
from ..domain.contracts import canonical_json, read_object, safe_path, strict_json
from ..domain.validation import ContractError


HOST = "127.0.0.1"
ASSETS = Path(__file__).with_name("web")
SHARED_STATIC = {
    "/garden-cover.webp": ("garden-cover.webp", "image/webp"),
    "/garden-icon.svg": ("garden-icon.svg", "image/svg+xml"),
}
CLASSIC_STATIC = {
    **SHARED_STATIC,
    "/": ("index.html", "text/html; charset=utf-8"),
    "/garden.css": ("garden.css", "text/css; charset=utf-8"),
    "/garden.js": ("garden.js", "text/javascript; charset=utf-8"),
}
STUDIO_MEDIA_TYPES = {
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}
STUDIO_ASSET = re.compile(r"assets/[A-Za-z0-9_][A-Za-z0-9_.-]*-[A-Za-z0-9_-]{8,64}\.[a-z0-9]+")
STUDIO_BUILD = "Run npm --prefix web ci and npm --prefix web run build from a checkout, or select --interface classic."
MAX_STUDIO_ASSETS = 512
JSON = "application/json; charset=utf-8"
NDJSON = "application/x-ndjson; charset=utf-8"
MAX_POST_BYTES = 4096
STREAM_PAUSE_SECONDS = 0.14
PILOT_POST = frozenset({"/api/assistant/preview", "/api/assistant/run", "/api/booklet/preview", "/api/booklet/artifact"})
JSON_MEDIA_TYPE = re.compile(r"application/json(?:[ \t]*;[ \t]*charset=utf-8)?", re.IGNORECASE)
BOOKLET_MONTH = re.compile(r"[0-9]{4}-(?:0[1-9]|1[0-2])")
MAX_QUERY_LENGTH = 256
MAX_REQUEST_TARGET = 4096
MAX_OVERVIEW_NOTES = 64
MAX_SEARCH_RESULTS = 20
MAX_RESPONSE_BYTES = 1024 * 1024
RECORD_REF = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*")
CITATION_ORDINAL = re.compile(r"(?:0|[1-9][0-9]{0,5})")
CONTENT_POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self'; "
    "img-src 'self'; font-src 'self'; connect-src 'self'; base-uri 'none'; "
    "form-action 'none'; frame-ancestors 'none'"
)


def browser_assets(interface: str) -> dict[str, tuple[str, str]]:
    """Select the classic routes or derive bounded Studio routes from the Vite manifest."""
    if interface == "classic":
        return CLASSIC_STATIC
    if interface != "studio":
        raise ContractError("VISIT_INTERFACE: choose classic or studio")
    try:
        index = safe_path(ASSETS, "studio/index.html")
        manifest = read_object(safe_path(ASSETS, "studio/.vite/manifest.json"))
        if not index.is_file():
            raise FileNotFoundError()
        if len(manifest) > MAX_STUDIO_ASSETS or not isinstance(manifest.get("index.html"), dict):
            raise ValueError()
        if manifest["index.html"].get("isEntry") is not True:
            raise ValueError()
        selected = set()
        for entry in manifest.values():
            if not isinstance(entry, dict) or not isinstance(entry.get("file"), str):
                raise ValueError()
            selected.add(entry["file"])
            for collection in (entry.get("css", []), entry.get("assets", [])):
                if not isinstance(collection, list) or not all(isinstance(name, str) for name in collection):
                    raise ValueError()
                selected.update(collection)
                if len(selected) > MAX_STUDIO_ASSETS:
                    raise ValueError()
        routes = {**SHARED_STATIC, "/": ("studio/index.html", "text/html; charset=utf-8")}
        for filename in sorted(selected):
            if len(filename) > 256 or not STUDIO_ASSET.fullmatch(filename):
                raise ValueError()
            relative = "studio/" + filename
            media_type = STUDIO_MEDIA_TYPES.get(Path(filename).suffix)
            if media_type is None or not safe_path(ASSETS, relative).is_file():
                raise ValueError()
            routes["/" + filename] = (relative, media_type)
    except FileNotFoundError as error:
        raise ContractError("VISIT_STUDIO_UNAVAILABLE: " + STUDIO_BUILD) from error
    except (ContractError, OSError, ValueError) as error:
        raise ContractError("VISIT_STUDIO_INVALID: the compiled bundle could not be verified. " + STUDIO_BUILD) from error
    return routes


class RequestError(Exception):
    def __init__(self, status: HTTPStatus, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code


def bad_query() -> RequestError:
    return RequestError(HTTPStatus.BAD_REQUEST, "WEB_QUERY", "Supply the expected bounded query parameters.")


def unavailable() -> RequestError:
    return RequestError(HTTPStatus.NOT_FOUND, "WEB_NOT_FOUND", "This item is unavailable in the authorized view.")


def browser_error(error: ContractError) -> RequestError:
    # Keep opaque diagnostics for denied items and avoid echoing machine-local
    # paths, storage errors, inputs, or record identifiers into the browser.
    code = str(error).split(":", 1)[0]
    if code in {"SESSION_EXPIRED", "SESSION_REVOKED", "SESSION_STALE", "SESSION_CONFIGURATION"}:
        return RequestError(HTTPStatus.FORBIDDEN, code, "Restart with an active explicit local session.")
    if code == "PROJECTION_DENIED":
        return RequestError(HTTPStatus.FORBIDDEN, code, "The explicit session does not allow this view.")
    if code in {"ASSISTANT_INVALID", "BOOKLET_FORMAT"}:
        return RequestError(HTTPStatus.BAD_REQUEST, code, "Choose a supported bounded preview or run request.")
    if code in {"ASSISTANT_APPROVAL", "BOOKLET_REVIEW"}:
        return RequestError(HTTPStatus.CONFLICT, code, "Preview and approve the current selection again.")
    if code in {"ASSISTANT_FOCUS", "BOOKLET_UNAVAILABLE"}:
        return RequestError(HTTPStatus.NOT_FOUND, code, "This selection is unavailable in the authorized view.")
    if code == "ASSISTANT_UNAVAILABLE":
        return RequestError(HTTPStatus.SERVICE_UNAVAILABLE, code, "The local fixture could not complete the turn.")
    if code in {"SESSION_REVISION", "WRITE_LOCKED", "QUERY_INTEGRITY"}:
        return RequestError(HTTPStatus.CONFLICT, code, "The authorized records could not be verified. Check the garden locally and refresh the session.")
    if code in {"QUERY_BUDGET", "CONTEXT_BUDGET"}:
        return RequestError(HTTPStatus.UNPROCESSABLE_ENTITY, code, "The result exceeds the allowed output budget. Try a narrower selection.")
    if code == "EVIDENCE_FORMAT":
        return RequestError(HTTPStatus.UNPROCESSABLE_ENTITY, code, "This evidence selection has no UTF-8 text preview.")
    if code == "EVIDENCE_UNAVAILABLE":
        return unavailable()
    return RequestError(HTTPStatus.SERVICE_UNAVAILABLE, "WEB_UNAVAILABLE", "The explicit local view could not be verified.")


def note_summary(record: dict) -> dict:
    fields = ("reference", "title", "kind", "record_type", "review", "scope", "domains", "topics", "tags")
    return {**{key: record[key] for key in fields}, "source_count": len(record["sources"])}


def overview_limit(context: QueryContext) -> int:
    return min(MAX_OVERVIEW_NOTES, context.session["budgets"]["max_results"])


def garden_payload(context: QueryContext, demo: bool, *, assistant: bool = False) -> dict:
    index = build_index(context, enforce_bytes=False)
    capabilities = {
        name: name in context.session["projections"]
        for name in ("search", "graph", "backlinks", "context", "evidence")
    }
    projections = set(context.session["projections"])
    capabilities["assistant"] = assistant and REQUIRED_PROJECTIONS <= projections
    capabilities["booklet"] = assistant and {"context", "source-evidence"} <= projections
    maximum = overview_limit(context)
    notes = [note_summary(record) for record in index["records"][:maximum]]
    keys = {record_key(record["reference"]) for record in notes}
    edges = []
    if capabilities["graph"]:
        context.require("graph")
        edges = [edge for edge in index["edges"] if edge["source"] in keys and edge["target"] in keys]
    return {
        "title": "Willow Garden" if demo else "Mindgarden",
        "demo": demo,
        "status": "ready",
        "capabilities": capabilities,
        "scope": index["scope"],
        "inputs": index["inputs"],
        "notes": notes,
        "graph": {"nodes": notes if capabilities["graph"] else [], "edges": edges[:maximum]},
        "limited": len(index["records"]) > maximum or len(edges) > maximum,
    }


def detail_payload(context: QueryContext, reference: str) -> dict:
    index = build_index(context, enforce_bytes=False)
    records = {record_key(record["reference"]): record for record in index["records"]}
    record = records.get(reference)
    if record is None:
        raise unavailable()
    note = {**note_summary(record), **{key: record[key] for key in ("content", "sources", "qualifications")}}
    maximum = context.session["budgets"]["max_results"]
    links, backlinks = [], []
    if "graph" in context.session["projections"]:
        context.require("graph")
        for edge in index["edges"]:
            target = (edge["target"] if edge["source"] == reference else
                      edge["source"] if not edge["directed"] and edge["target"] == reference else None)
            if target is not None:
                linked = records[target]
                links.append({"to": target, "type": edge["type"], "reference": linked["reference"],
                              "title": linked["title"], "scope": edge["scope"], "review": linked["review"]})
    if "backlinks" in context.session["projections"]:
        context.require("backlinks")
        backlinks = [{**link, "title": records[link["from"]]["title"]}
                     for link in index["backlinks"][reference][:maximum]]
    return {"note": note, "links": links[:maximum], "backlinks": backlinks, "scope": index["scope"]}


def evidence_payload(context: QueryContext, reference: str, ordinal: int) -> dict:
    index = build_index(context, projection="evidence")
    record = next((item for item in index["records"] if record_key(item["reference"]) == reference), None)
    if record is None or ordinal >= len(record["sources"]):
        raise unavailable()
    citation = record["sources"][ordinal]
    return resolve_evidence(context, citation["source"], citation["locator"], citation["content_sha256"])


def context_payload(context: QueryContext, query: str) -> bytes:
    context.require("context")
    if not context.bindings.gardens:
        raise unavailable()
    profile = {
        "schema": "mindgarden.context-profile/v1",
        "id": "browser-context",
        "garden": next(iter(context.bindings.gardens)),
        "title": "Garden context",
        "description": "Bounded context for the explicit browser query.",
        "query": query,
        "include": [],
        "exclude": [],
        "kinds": [],
        "max_items": 5,
        "max_bytes": 16384,
        "max_candidates": 20,
    }
    return render_context(context, profile, "json")


def parameters(raw: str, expected: set[str]) -> dict[str, str]:
    try:
        query = parse_qs(raw, keep_blank_values=True, strict_parsing=True, errors="strict", max_num_fields=len(expected))
    except ValueError as error:
        raise bad_query() from error
    if query.keys() != expected or any(len(values) != 1 for values in query.values()):
        raise bad_query()
    return {key: values[0] for key, values in query.items()}


class GardenServer(ThreadingHTTPServer):
    allow_reuse_address = False

    def __init__(self, port: int, context: QueryContext, demo: bool, assets: dict[str, tuple[str, str]],
                 assistant: AssistantProvider | None = None):
        self.context = context
        self.demo = demo
        self.assets = assets
        self.assistant = assistant
        self.access_token = token_urlsafe(32)
        super().__init__((HOST, port), GardenHandler)
        self.authority = HOST if self.server_port == 80 else f"{HOST}:{self.server_port}"
        self.origin = f"http://{self.authority}"
        self.url = f"{self.origin}/#access={self.access_token}"

    def handle_error(self, request, client_address):
        # Socket failures can happen when a browser navigates away mid-response.
        # Never print raw exceptions or private content through request logs.
        pass


class GardenHandler(BaseHTTPRequestHandler):
    server: GardenServer
    timeout = 5

    def log_message(self, format, *args):
        pass

    def send_error(self, code, message=None, explain=None):
        if code == HTTPStatus.NOT_IMPLEMENTED:
            error = RequestError(HTTPStatus.METHOD_NOT_ALLOWED, "WEB_METHOD", "Only GET and HEAD are supported.")
        else:
            error = RequestError(HTTPStatus(code), "WEB_REQUEST", "The HTTP request could not be accepted.")
        self.respond_error(error)

    def response_headers(self, status: HTTPStatus, media_type: str, *, length: int | None,
                         filename: str | None = None) -> None:
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", media_type)
        if length is not None:
            self.send_header("Content-Length", str(length))
        if filename is not None:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.send_header("Content-Security-Policy", CONTENT_POLICY)
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        if status == HTTPStatus.METHOD_NOT_ALLOWED:
            self.send_header("Allow", "GET, HEAD")
        self.end_headers()

    def respond(self, status: HTTPStatus, media_type: str, body: bytes, *, filename: str | None = None) -> None:
        self.response_headers(status, media_type, length=len(body), filename=filename)
        if self.command != "HEAD":
            self.wfile.write(body)

    def respond_error(self, error: RequestError) -> None:
        body = canonical_json({"error": {"code": error.code, "message": str(error)}})
        self.respond(error.status, JSON, body)

    def authorize_host(self, *, require_origin: bool = False) -> None:
        hosts = self.headers.get_all("Host", [])
        origins = self.headers.get_all("Origin", [])
        fetch_sites = self.headers.get_all("Sec-Fetch-Site", [])
        valid_origins = ([self.server.origin],) if require_origin else ([], [self.server.origin])
        if (hosts != [self.server.authority] or origins not in valid_origins
                or fetch_sites not in ([], ["none"], ["same-origin"])):
            raise RequestError(HTTPStatus.FORBIDDEN, "WEB_ORIGIN", "Use the exact loopback address printed by Mindgarden.")

    def authorize_browser(self) -> None:
        credentials = self.headers.get_all("Authorization", [])
        header = credentials[0] if len(credentials) == 1 else ""
        expected = f"Bearer {self.server.access_token}"
        if not compare_digest(header.encode("latin-1"), expected.encode("ascii")):
            raise RequestError(HTTPStatus.FORBIDDEN, "WEB_ACCESS", "Open the full access link printed by Mindgarden.")

    def api(self, path: str, raw_query: str) -> bytes:
        self.authorize_browser()
        # Pin the launch authority while keeping mutable query snapshots local to
        # each request. Replacing the session file cannot widen the running view.
        context = deepcopy(self.server.context)
        if path == "/api/garden":
            parameters(raw_query, set())
            body = canonical_json(garden_payload(context, self.server.demo, assistant=self.server.assistant is not None))
        elif path == "/api/connectors":
            parameters(raw_query, set())
            index = build_index(context, projection="evidence", enforce_bytes=False)
            records = index["records"][:overview_limit(context)]
            body = canonical_json(connector_evidence(context, records, demo=self.server.demo))
        elif path in {"/api/search", "/api/context"}:
            query = parameters(raw_query, {"q"})["q"].strip()
            if len(query) > MAX_QUERY_LENGTH or not all(char.isprintable() for char in query):
                raise bad_query()
            body = (canonical_json(search_payload(context, query, limit=MAX_SEARCH_RESULTS))
                    if path == "/api/search" else context_payload(context, query))
        elif path in {"/api/note", "/api/evidence"}:
            args = parameters(raw_query, {"ref"} if path == "/api/note" else {"ref", "citation"})
            if not RECORD_REF.fullmatch(args["ref"]):
                raise bad_query()
            if path == "/api/note":
                body = canonical_json(detail_payload(context, args["ref"]))
            else:
                if not CITATION_ORDINAL.fullmatch(args["citation"]):
                    raise bad_query()
                body = canonical_json(evidence_payload(context, args["ref"], int(args["citation"])))
        else:
            raise unavailable()
        if len(body) > MAX_RESPONSE_BYTES:
            raise ContractError("QUERY_BUDGET: browser output exceeds its byte ceiling")
        context.ensure_output(body)
        return body

    def post_body(self) -> dict:
        media_types = self.headers.get_all("Content-Type", [])
        if len(media_types) != 1 or not JSON_MEDIA_TYPE.fullmatch(media_types[0]):
            raise RequestError(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "WEB_MEDIA", "Send a UTF-8 JSON object.")
        lengths = self.headers.get_all("Content-Length", [])
        if (len(lengths) != 1 or not re.fullmatch(r"[1-9][0-9]{0,9}", lengths[0])
                or self.headers.get_all("Transfer-Encoding") or self.headers.get_all("Content-Encoding")):
            raise bad_query()
        length = int(lengths[0])
        if length > MAX_POST_BYTES:
            raise RequestError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "WEB_QUERY", "The JSON request exceeds the local byte limit.")
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise bad_query()
        try:
            value = strict_json(raw.decode("utf8"))
        except (ContractError, UnicodeError) as error:
            raise bad_query() from error
        if not isinstance(value, dict):
            raise bad_query()
        return value

    def respond_turn(self, context: QueryContext, lines: tuple[bytes, ...]) -> None:
        try:
            context.check_live()
        except ContractError as error:
            self.respond_error(browser_error(error))
            return
        self.response_headers(HTTPStatus.OK, NDJSON, length=None)
        sent = len(lines[0])
        try:
            self.wfile.write(lines[0])
            for line in lines[1:]:
                sleep(STREAM_PAUSE_SECONDS)
                try:
                    context.check_live()
                except ContractError as error:
                    diagnostic = browser_error(error)
                    final = ndjson({"type": "error", "code": diagnostic.code, "message": str(diagnostic)})
                    if sent + len(final) <= output_limit(context):
                        self.wfile.write(final)
                    return
                self.wfile.write(line)
                sent += len(line)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            return

    def booklet_post(self, context: QueryContext, value: dict) -> tuple[str, bytes, str | None]:
        from ..application.booklet import booklet_artifact, booklet_preview

        context.require("source-evidence")
        artifact = self.path == "/api/booklet/artifact"
        expected = {"month", "plan_sha256", "format"} if artifact else {"month"}
        month = value.get("month")
        if value.keys() != expected or not isinstance(month, str) or not BOOKLET_MONTH.fullmatch(month):
            raise bad_query()
        if not artifact:
            return JSON, canonical_json(booklet_preview(context, month)), None
        format = value["format"]
        if format not in ("pdf", "evidence") or not isinstance(value["plan_sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", value["plan_sha256"]):
            raise bad_query()
        mime, data = booklet_artifact(context, month, value["plan_sha256"], format)
        suffix = ".pdf" if format == "pdf" else "-evidence.json"
        return mime, data, "mindgarden-booklet-" + month + suffix

    def do_POST(self):
        provider = self.server.assistant
        try:
            if provider is None or self.path not in PILOT_POST:
                raise RequestError(HTTPStatus.METHOD_NOT_ALLOWED, "WEB_METHOD", "This route does not support POST.")
            self.authorize_host(require_origin=True)
            self.authorize_browser()
            context = deepcopy(self.server.context)
            context.check_live()
            value = self.post_body()
            filename = None
            if self.path.startswith("/api/assistant/"):
                run = self.path == "/api/assistant/run"
                prepared = prepare_turn(context, provider, value, run=run)
                if run:
                    lines = turn_lines(context, provider, prepared)
                else:
                    mime, body = JSON, canonical_json(prepared.preview)
            else:
                run = False
                mime, body, filename = self.booklet_post(context, value)
            if not run:
                if len(body) > MAX_RESPONSE_BYTES:
                    raise ContractError("QUERY_BUDGET: browser output exceeds its byte ceiling")
                context.ensure_output(body)
        except RequestError as error:
            self.respond_error(error)
        except ContractError as error:
            self.respond_error(browser_error(error))
        except (ValueError, OSError):
            self.respond_error(RequestError(HTTPStatus.SERVICE_UNAVAILABLE, "WEB_UNAVAILABLE", "The local view is unavailable."))
        else:
            if run:
                self.respond_turn(context, lines)
            else:
                self.respond(HTTPStatus.OK, mime, body, filename=filename)

    def do_GET(self):
        try:
            self.authorize_host()
            if len(self.path) > MAX_REQUEST_TARGET:
                raise bad_query()
            raw = urlsplit(self.path)
            if raw.scheme or raw.netloc or raw.fragment:
                raise bad_query()
            if raw.path.startswith("/api/"):
                body, media_type = self.api(raw.path, raw.query), JSON
            elif raw.path in self.server.assets and not raw.query:
                filename, media_type = self.server.assets[raw.path]
                body = safe_path(ASSETS, filename).read_bytes()
            else:
                raise unavailable()
        except RequestError as error:
            self.respond_error(error)
        except ContractError as error:
            self.respond_error(browser_error(error))
        except FileNotFoundError:
            self.respond_error(unavailable())
        except (ValueError, OSError):
            self.respond_error(RequestError(HTTPStatus.SERVICE_UNAVAILABLE, "WEB_UNAVAILABLE", "The local view is unavailable."))
        else:
            self.respond(HTTPStatus.OK, media_type, body)

    do_HEAD = do_GET


def make_server(local_config: Path, scope: Path, *, port: int = 0, demo: bool = False,
                interface: str = "classic", assistant: str = "off") -> GardenServer:
    """Pin an explicitly approved local view and bind a numeric loopback socket."""
    if type(port) is not int or not 0 <= port <= 65535:
        raise ContractError("WEB_PORT: supply a port between 0 and 65535")
    if assistant not in ("off", "fixture") or assistant == "fixture" and not (demo and interface == "studio"):
        raise ContractError("VISIT_ASSISTANT: the local fixture requires the fictional Studio launch")
    assets = browser_assets(interface)
    context = QueryContext.load(local_config, scope)
    context.require("index")
    provider = None
    if assistant == "fixture":
        require_private(context)
        provider = FixtureAssistant()
    return GardenServer(port, context, demo, assets, provider)


def serve_garden(local_config: Path, scope: Path, *, port: int = 0, demo: bool = False,
                 interface: str = "classic", assistant: str = "off") -> int:
    """Print the browser access link and serve until interrupted."""
    with make_server(local_config, scope, port=port, demo=demo, interface=interface, assistant=assistant) as server:
        print(server.url, flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0
