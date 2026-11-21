"""Protect one explicit ChatGPT owner profile outside garden records."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
import os
from pathlib import Path
from tempfile import mkstemp
from threading import local
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from ..domain.contracts import canonical_json, strict_json
from ..domain.validation import ContractError
from .registry_acl import require_no_extended_acl
from .registry_files import read_control, registry_writer


CONNECTION_SCHEMA = "mindgarden.chatgpt-owner-connection/v1"
HOST_SCHEMA = "mindgarden.chatgpt-owner-host/v1"
MAX_STATE_BYTES = 128 * 1024
MAX_TOKEN_LENGTH = 32 * 1024
MAX_TIMESTAMP = 253402300799
REGISTRATION_FIELDS = {"issuer", "subject", "client_id"}
CREDENTIAL_FIELDS = {"scopes", "access_token", "refresh_token", "id_token", "expires_at", "earliest_refresh_at"}


@dataclass(frozen=True)
class ChatGPTRegistration:
    issuer: str
    subject: str = field(repr=False)
    client_id: str


@dataclass(frozen=True)
class ChatGPTCredentials:
    issuer: str
    subject: str = field(repr=False)
    client_id: str
    scopes: tuple[str, ...]
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    id_token: str = field(repr=False)
    expires_at: int
    earliest_refresh_at: int | None = None

    @property
    def registration(self) -> ChatGPTRegistration:
        return ChatGPTRegistration(self.issuer, self.subject, self.client_id)


def _invalid() -> ContractError:
    return ContractError("CHATGPT_STATE_INVALID: the local ChatGPT owner state is invalid")


def _unavailable() -> ContractError:
    return ContractError("CHATGPT_STATE_UNAVAILABLE: use accessible owner-only ChatGPT state outside Git and garden records")


def _token(value: object, maximum: int) -> bool:
    return (isinstance(value, str) and 0 < len(value) <= maximum and value.isascii()
            and value.isprintable() and " " not in value)


def _issuer(value: object) -> bool:
    if not _token(value, 1024):
        return False
    try:
        url = urlsplit(value)
        port = url.port
        return (url.scheme == "https" and bool(url.hostname) and (port is None or port > 0) and url.username is None
                and url.password is None and not any(mark in value for mark in "?#\\"))
    except ValueError:
        return False


def _registration(value: object) -> ChatGPTRegistration:
    if (not isinstance(value, dict) or value.keys() != REGISTRATION_FIELDS or not _issuer(value["issuer"])
            or not _token(value["subject"], 1024) or not _token(value["client_id"], 512)):
        raise _invalid()
    return ChatGPTRegistration(**value)


def _timestamp(value: object) -> bool:
    return type(value) is int and 0 < value <= MAX_TIMESTAMP


def _validate_credentials(value: ChatGPTCredentials) -> None:
    if not isinstance(value, ChatGPTCredentials):
        raise _invalid()
    _registration({key: getattr(value, key) for key in REGISTRATION_FIELDS})
    scopes = value.scopes
    if (not isinstance(scopes, tuple) or not 0 < len(scopes) <= 64
            or not all(_token(scope, 256) and '"' not in scope and "\\" not in scope for scope in scopes)
            or len(set(scopes)) != len(scopes)
            or not all(_token(secret, MAX_TOKEN_LENGTH) for secret in (value.access_token, value.refresh_token, value.id_token))
            or not _timestamp(value.expires_at)
            or value.earliest_refresh_at is not None and not _timestamp(value.earliest_refresh_at)):
        raise _invalid()


def _read_bytes(path: Path) -> bytes | None:
    try:
        raw = read_control(path, missing_ok=True)
    except ContractError as error:
        if str(error).startswith("REGISTRY_BUDGET:"):
            raise _invalid() from None
        raise _unavailable() from None
    if raw is not None and len(raw) > MAX_STATE_BYTES:
        raise _invalid()
    return raw


def _document(raw: bytes) -> dict:
    try:
        value = strict_json(raw)
    except ContractError:
        raise _invalid() from None
    if not isinstance(value, dict):
        raise _invalid()
    return value


def _replace(path: Path, document: dict, expected: bytes | None) -> None:
    """Durably replace the one envelope without keeping prior token snapshots."""
    content = canonical_json(document)
    if len(content) > MAX_STATE_BYTES:
        raise _invalid()
    temporary = None
    try:
        descriptor, temporary = mkstemp(prefix=".chatgpt-state-", dir=path.parent)
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            require_no_extended_acl(stream.fileno())
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if _read_bytes(path) != expected:
            raise ContractError("CHATGPT_STATE_CHANGED: the owner state changed while staging")
        os.replace(temporary, path)
        temporary = None
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        raise _unavailable() from None
    finally:
        if temporary is not None:
            try:
                Path(temporary).unlink(missing_ok=True)
            except OSError:
                pass


class ChatGPTStore:
    """Store one local owner's credentials and retain their identity on clear."""

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self._connection = self.directory / "connection.json"
        self._host = self.directory / "host.json"
        self._lease = local()

    @contextmanager
    def writer(self) -> Iterator[ChatGPTStore]:
        """Serialize a transition across processes and nest calls on this thread."""
        process_id = os.getpid()
        if getattr(self._lease, "process_id", None) == process_id:
            yield self
            return
        try:
            with registry_writer(self._connection):
                self._lease.process_id = process_id
                try:
                    yield self
                finally:
                    del self._lease.process_id
        except ContractError as error:
            if str(error).startswith("REGISTRY_LOCKED:"):
                raise ContractError("CHATGPT_STATE_BUSY: another owner transition is in progress") from None
            if str(error).startswith("REGISTRY_"):
                raise _unavailable() from None
            raise

    def _read_host(self) -> str | None:
        raw = _read_bytes(self._host)
        if raw is None:
            return None
        document = _document(raw)
        if document.keys() != {"schema", "id"} or document["schema"] != HOST_SCHEMA or not _token(document["id"], 45):
            raise _invalid()
        value = document["id"]
        try:
            identifier = UUID(value)
        except ValueError:
            raise _invalid() from None
        if identifier.version != 4 or identifier.urn != value:
            raise _invalid()
        return value

    def host_id(self) -> str:
        """Read the installation's random ID or initialize it explicitly."""
        existing = self._read_host()
        if existing is not None:
            return existing
        with self.writer():
            existing = self._read_host()
            if existing is not None:
                return existing
            identifier = uuid4().urn
            _replace(self._host, {"schema": HOST_SCHEMA, "id": identifier}, None)
            return identifier

    def _state(self) -> tuple[bytes | None, ChatGPTRegistration | None, ChatGPTCredentials | None]:
        raw = _read_bytes(self._connection)
        if raw is None:
            return None, None, None
        document = _document(raw)
        if (document.keys() != {"schema", "registration", "credentials"}
                or document["schema"] != CONNECTION_SCHEMA):
            raise _invalid()
        registration = _registration(document["registration"])
        supplied = document["credentials"]
        if supplied is None:
            return raw, registration, None
        if not isinstance(supplied, dict) or supplied.keys() != CREDENTIAL_FIELDS or not isinstance(supplied["scopes"], list):
            raise _invalid()
        credentials = ChatGPTCredentials(**document["registration"], **{**supplied, "scopes": tuple(supplied["scopes"])})
        _validate_credentials(credentials)
        return raw, registration, credentials

    def read(self) -> ChatGPTCredentials | None:
        """Read validated local credentials without changing state."""
        return self._state()[2]

    def registration(self) -> ChatGPTRegistration | None:
        """Read the bound owner identity, including after sign-out."""
        return self._state()[1]

    def save(self, credentials: ChatGPTCredentials) -> None:
        _validate_credentials(credentials)
        with self.writer():
            raw, registration, _ = self._state()
            if registration is not None and registration != credentials.registration:
                raise ContractError("CHATGPT_OWNER_MISMATCH: this profile is bound to a different owner")
            self._write(raw, credentials.registration, {key: getattr(credentials, key) for key in CREDENTIAL_FIELDS})

    def clear(self) -> None:
        """Remove credentials atomically while retaining the selected owner."""
        with self.writer():
            raw, registration, credentials = self._state()
            if credentials is not None:
                self._write(raw, registration, None)

    def _write(self, expected: bytes | None, registration: ChatGPTRegistration, credentials: dict | None) -> None:
        _replace(self._connection, {
            "schema": CONNECTION_SCHEMA,
            "registration": {key: getattr(registration, key) for key in REGISTRATION_FIELDS},
            "credentials": credentials,
        }, expected)
