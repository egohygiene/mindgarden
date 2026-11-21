"""Validate the local OpenAI public-client sign-in and renewable session."""

from base64 import urlsafe_b64encode
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from hmac import compare_digest
from http.client import HTTPException, HTTPSConnection
import re
from secrets import token_urlsafe
from socket import SHUT_RDWR
from threading import Timer
from time import monotonic, time
from urllib.parse import urlencode

from ..domain.contracts import strict_json
from ..domain.validation import ContractError
from .chatgpt_credentials import ChatGPTCredentials


ISSUER = "https://auth.openai.com"
AUTH_HOST = "auth.openai.com"
RESOURCE = "https://api.openai.com/v1"
AUTHORIZE_PATH = "/api/accounts/authorize"
TOKEN_PATH = "/api/accounts/oauth/token"
DISCOVERY_PATH = "/.well-known/openid-configuration"
JWKS_PATH = "/.well-known/jwks.json"
REVOKE_PATH = "/api/accounts/oauth/revoke"
REGISTRATION_CLIENT_ID = "dynamic_agent_client"
SCOPES = (
    "openid",
    "profile",
    "email",
    "offline_access",
    "resource.invoke",
    "chatgpt.tokens.use.direct",
)
RESPONSE_LIMIT = 128 * 1024
ERROR_LIMIT = 4 * 1024
FORM_LIMIT = 64 * 1024
TOKEN_LIMIT = 16 * 1024
TOTAL_SECONDS = 15
MAX_UNIX_SECONDS = 253_402_300_799
CALLBACK = re.compile(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})/auth/callback")
HOST_ID = re.compile(
    r"(?:urn:uuid:[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"
    r"|urn:ietf:params:oauth:jwk-thumbprint:sha-256:[a-zA-Z0-9_-]{43})"
)
PUBLIC_ID = re.compile(r"[a-zA-Z0-9._~-]{1,256}")
VISIBLE_ASCII = re.compile(r"[!-~]+")
BASE64URL = re.compile(r"[a-zA-Z0-9_-]+")
TERMINAL_REFRESH_ERRORS = frozenset(
    {
        "invalid_grant",
        "invalid_refresh_token",
        "token_expired",
        "refresh_token_expired",
        "refresh_token_invalidated",
        "refresh_token_reused",
    }
)


@dataclass(frozen=True)
class OAuthAttempt:
    authorization_url: str = field(repr=False)
    state: str = field(repr=False)
    redirect_uri: str
    issued_client_id: str | None
    _nonce: str = field(repr=False)
    _verifier: str = field(repr=False)


def _client_id(value):
    return (
        isinstance(value, str)
        and value != REGISTRATION_CLIENT_ID
        and PUBLIC_ID.fullmatch(value) is not None
    )


def new_attempt(
    host_id: str, redirect_uri: str, issued_client_id: str | None = None
) -> OAuthAttempt:
    callback = (
        CALLBACK.fullmatch(redirect_uri) if isinstance(redirect_uri, str) else None
    )
    if (
        not isinstance(host_id, str)
        or not HOST_ID.fullmatch(host_id)
        or not callback
        or int(callback[1]) > 65535
        or issued_client_id is not None
        and not _client_id(issued_client_id)
    ):
        raise ContractError("CHATGPT_OAUTH_ATTEMPT: invalid local sign-in registration")

    state, nonce, verifier = token_urlsafe(32), token_urlsafe(32), token_urlsafe(48)
    challenge = (
        urlsafe_b64encode(sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    parameters = {
        "client_id": issued_client_id or REGISTRATION_CLIENT_ID,
        "ext_agent_host_id": host_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "resource": RESOURCE,
        "state": state,
        "nonce": nonce,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    }
    if issued_client_id is None:
        parameters["agent_name_hint"] = "Mindgarden Studio"
    return OAuthAttempt(
        ISSUER + AUTHORIZE_PATH + "?" + urlencode(parameters),
        state,
        redirect_uri,
        issued_client_id,
        nonce,
        verifier,
    )


def _remaining(deadline):
    seconds = deadline - monotonic()
    if seconds <= 0:
        raise TimeoutError
    return seconds


def _interrupt(socket):
    try:
        socket.shutdown(SHUT_RDWR)
    except OSError:
        pass


class _OpenAITransport:
    """Only HTTPS on the fixed OpenAI auth host, without redirect handling."""

    def request(self, path, *, deadline, form=None, empty=False):
        if path not in {TOKEN_PATH, DISCOVERY_PATH, JWKS_PATH, REVOKE_PATH}:
            raise ContractError(
                "CHATGPT_OAUTH_ENDPOINT: unsupported authorization endpoint"
            )
        headers = {"Accept": "application/json", "Accept-Encoding": "identity"}
        body = None if form is None else urlencode(form).encode("ascii")
        if body is not None:
            if len(body) > FORM_LIMIT:
                raise ContractError(
                    "CHATGPT_OAUTH_LIMIT: authorization form exceeds the byte budget"
                )
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        connection = watchdog = None
        try:
            connection = HTTPSConnection(AUTH_HOST, 443, timeout=_remaining(deadline))
            connection.connect()
            socket = connection.sock
            seconds = _remaining(deadline)
            watchdog = Timer(seconds, _interrupt, args=(socket,))
            watchdog.daemon = True
            watchdog.start()
            socket.settimeout(seconds)
            connection.request("GET" if body is None else "POST", path, body, headers)
            socket.settimeout(_remaining(deadline))
            with connection.getresponse() as response:
                if response.status != 200:
                    refresh = (
                        path == TOKEN_PATH
                        and form is not None
                        and form.get("grant_type") == "refresh_token"
                    )
                    raise _refusal(response, socket, deadline, refresh=refresh)
                raw = _response_body(response, socket, deadline, empty=empty)
        except (OSError, HTTPException):
            raise ContractError(
                "CHATGPT_OAUTH_UNAVAILABLE: authorization service did not respond within the connection limits"
            ) from None
        finally:
            if watchdog is not None:
                watchdog.cancel()
            if connection is not None:
                connection.close()
        if empty:
            return None
        try:
            response = strict_json(raw)
        except (ValueError, RecursionError):
            raise ContractError(
                "CHATGPT_OAUTH_RESPONSE: invalid authorization response"
            ) from None
        if not isinstance(response, dict):
            raise ContractError(
                "CHATGPT_OAUTH_RESPONSE: invalid authorization response"
            )
        return response


def _refusal(response, socket, deadline, *, refresh):
    if response.status not in {400, 401, 403}:
        return ContractError(
            "CHATGPT_OAUTH_UNAVAILABLE: authorization service returned an unexpected status"
        )
    if refresh:
        try:
            body = _response_body(
                response, socket, deadline, empty=False, limit=ERROR_LIMIT
            )
            value = strict_json(body)
        except (ValueError, RecursionError):
            value = None
        error = value.get("error") if isinstance(value, dict) else None
        code = error.get("code") if isinstance(error, dict) else error
        if isinstance(code, str):
            if code in TERMINAL_REFRESH_ERRORS:
                return ContractError(
                    "CHATGPT_REFRESH_REAUTHORIZE: the local ChatGPT session ended. Sign in again."
                )
            if code == "invalid_client":
                return ContractError(
                    "CHATGPT_OAUTH_CLIENT: OpenAI did not accept this client registration"
                )
    return ContractError("CHATGPT_OAUTH_DENIED: sign-in or refresh was declined")


def _response_body(response, socket, deadline, *, empty, limit=RESPONSE_LIMIT):
    maximum = 0 if empty else limit
    encoding = response.getheader("Content-Encoding", "identity")
    content_type = (
        response.getheader("Content-Type", "").partition(";")[0].strip().lower()
    )
    declared = response.getheader("Content-Length")
    if (
        encoding not in ("", "identity")
        or not empty
        and content_type != "application/json"
    ):
        raise ContractError(
            "CHATGPT_OAUTH_RESPONSE: unexpected authorization response format"
        )
    if declared is not None and (
        not re.fullmatch(r"[0-9]{1,9}", declared) or int(declared) > maximum
    ):
        raise ContractError(
            "CHATGPT_OAUTH_LIMIT: authorization response exceeds the byte budget"
        )
    raw = bytearray()
    while len(raw) <= maximum:
        socket.settimeout(_remaining(deadline))
        chunk = response.read1(min(16384, maximum + 1 - len(raw)))
        if not chunk:
            break
        raw.extend(chunk)
    _remaining(deadline)
    if len(raw) > maximum or declared is not None and len(raw) != int(declared):
        raise ContractError(
            "CHATGPT_OAUTH_LIMIT: authorization response exceeded its budget or was incomplete"
        )
    return bytes(raw)


def _oidc():
    try:
        import jwt
        from jwt.algorithms import RSAAlgorithm
        from jwt.exceptions import PyJWTError

        if not jwt.algorithms.has_crypto:
            raise ImportError
    except (ImportError, AttributeError):
        raise ContractError(
            "CHATGPT_OAUTH_DEPENDENCY: install requirements/chatgpt.txt for OIDC verification"
        ) from None
    return jwt, RSAAlgorithm, PyJWTError


def _secret(value, maximum=TOKEN_LIMIT):
    return (
        isinstance(value, str)
        and 0 < len(value) <= maximum
        and VISIBLE_ASCII.fullmatch(value) is not None
    )


def _scopes(value):
    if not isinstance(value, str) or len(value) > 1024:
        raise ContractError(
            "CHATGPT_OAUTH_SCOPE: ChatGPT plan permissions were not confirmed"
        )
    items = value.split()
    if len(items) != len(SCOPES) or set(items) != set(SCOPES):
        raise ContractError(
            "CHATGPT_OAUTH_SCOPE: ChatGPT plan permissions were not confirmed"
        )
    return tuple(sorted(items))


def _refresh_time(value):
    if value is None:
        return None
    if isinstance(value, str) and len(value) <= 40:
        if re.fullmatch(r"[0-9]{1,12}", value):
            value = int(value)
        else:
            try:
                timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if timestamp.tzinfo is not None:
                    value = int(timestamp.timestamp())
            except (ValueError, OSError, OverflowError):
                pass
    if type(value) is not int or not 0 <= value <= MAX_UNIX_SECONDS:
        raise ContractError("CHATGPT_OAUTH_RESPONSE: invalid refresh advisory")
    return value or None


def _identity(id_token, client_id, nonce, jwks):
    jwt, algorithm, jwt_error = _oidc()
    bad = "CHATGPT_OAUTH_IDENTITY: the OpenAI identity could not be verified"
    if not _secret(id_token):
        raise ContractError(bad)
    try:
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        keys = jwks.get("keys")
        if (
            header.get("alg") != "RS256"
            or not isinstance(kid, str)
            or not PUBLIC_ID.fullmatch(kid)
            or not isinstance(keys, list)
            or not 1 <= len(keys) <= 64
        ):
            raise ContractError(bad)
        selected = [
            key for key in keys if isinstance(key, dict) and key.get("kid") == kid
        ]
        if len(selected) != 1:
            raise ContractError(bad)
        jwk = selected[0]
        n, e = jwk.get("n"), jwk.get("e")
        if (
            jwk.get("kty") != "RSA"
            or jwk.get("use") != "sig"
            or jwk.get("alg") != "RS256"
            or not isinstance(n, str)
            or not 342 <= len(n) <= 1366
            or not BASE64URL.fullmatch(n)
            or not isinstance(e, str)
            or not 1 <= len(e) <= 8
            or not BASE64URL.fullmatch(e)
        ):
            raise ContractError(bad)
        key = algorithm.from_jwk({"kty": "RSA", "n": n, "e": e})
        if not 2048 <= key.key_size <= 8192:
            raise ContractError(bad)
        required = ["iss", "aud", "exp", "iat", "sub"]
        if nonce is not None:
            required.append("nonce")
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=ISSUER,
            options={"require": required},
        )
        audiences = claims["aud"]
        authorized_party = claims.get("azp")
        if (
            not _secret(claims["sub"], 256)
            or type(claims["exp"]) is not int
            or type(claims["iat"]) is not int
            or "azp" in claims
            and authorized_party != client_id
            or audiences not in (client_id, [client_id])
            or nonce is not None
            and (
                not _secret(claims["nonce"], 256)
                or not compare_digest(claims["nonce"], nonce)
            )
        ):
            raise ContractError(bad)
        return claims["sub"]
    except (
        jwt_error,
        ValueError,
        TypeError,
        AttributeError,
        RecursionError,
        OverflowError,
    ):
        raise ContractError(bad) from None


class OAuthClient:
    """Keep OAuth credentials in the local broker and avoid replaying grants."""

    def __init__(self, transport=None):
        self.transport = transport if transport is not None else _OpenAITransport()

    @staticmethod
    def require_oidc():
        _oidc()

    def exchange(self, attempt, code, client_id):
        self.require_oidc()
        expected = attempt.issued_client_id
        selected = expected if client_id is None else client_id
        if (
            not _secret(code, 8192)
            or not _client_id(selected)
            or expected is not None
            and not compare_digest(expected, selected)
        ):
            raise ContractError(
                "CHATGPT_OAUTH_CALLBACK: invalid authorization code or client binding"
            )
        deadline = monotonic() + TOTAL_SECONDS
        value = self.transport.request(
            TOKEN_PATH,
            deadline=deadline,
            form={
                "grant_type": "authorization_code",
                "client_id": selected,
                "code": code,
                "code_verifier": attempt._verifier,
                "redirect_uri": attempt.redirect_uri,
                "resource": RESOURCE,
            },
        )
        return self._credentials(value, selected, deadline, nonce=attempt._nonce)

    def refresh(self, old):
        self.require_oidc()
        self._check_refresh_binding(old)
        deadline = monotonic() + TOTAL_SECONDS
        value = self.transport.request(
            TOKEN_PATH,
            deadline=deadline,
            form={
                "grant_type": "refresh_token",
                "client_id": old.client_id,
                "refresh_token": old.refresh_token,
                "resource": RESOURCE,
            },
        )
        return self._credentials(value, old.client_id, deadline, previous=old)

    def revoke(self, old):
        self._check_refresh_binding(old)
        deadline = monotonic() + TOTAL_SECONDS
        try:
            discovery = self.transport.request(DISCOVERY_PATH, deadline=deadline)
            if (
                not isinstance(discovery, dict)
                or discovery.get("issuer") != ISSUER
                or discovery.get("revocation_endpoint") != ISSUER + REVOKE_PATH
            ):
                raise ContractError(
                    "CHATGPT_OAUTH_ENDPOINT: unverified revocation endpoint"
                )
            self.transport.request(
                REVOKE_PATH,
                deadline=deadline,
                empty=True,
                form={
                    "token": old.refresh_token,
                    "token_type_hint": "refresh_token",
                    "client_id": old.client_id,
                },
            )
        except ContractError:
            raise ContractError(
                "CHATGPT_OAUTH_REVOCATION: remote disconnection was not confirmed"
            ) from None

    @staticmethod
    def _check_refresh_binding(old):
        if (
            old.issuer != ISSUER
            or not _client_id(old.client_id)
            or not _secret(old.subject, 256)
            or not _secret(old.refresh_token)
        ):
            raise ContractError(
                "CHATGPT_OAUTH_IDENTITY: incompatible local ChatGPT account"
            )

    def _credentials(self, value, client_id, deadline, *, nonce=None, previous=None):
        if not isinstance(value, dict):
            raise ContractError(
                "CHATGPT_OAUTH_RESPONSE: invalid authorization response"
            )
        received = int(time())
        scope = (
            " ".join(previous.scopes)
            if previous is not None and "scope" not in value
            else value.get("scope")
        )
        scopes = _scopes(scope)
        expires = value.get("expires_in")
        token_type = value.get("token_type")
        access, renewal = value.get("access_token"), value.get("refresh_token")
        if (
            not isinstance(token_type, str)
            or token_type.lower() != "bearer"
            or not _secret(access)
            or not _secret(renewal)
            or type(expires) is not int
            or not 0 < expires <= 3600
            or previous is not None
            and compare_digest(renewal, previous.refresh_token)
        ):
            raise ContractError(
                "CHATGPT_OAUTH_RESPONSE: invalid or incomplete OAuth credentials"
            )
        earliest = _refresh_time(value.get("earliest_refresh_at"))
        if previous is not None and "id_token" not in value:
            subject, id_token = previous.subject, previous.id_token
        else:
            id_token = value.get("id_token")
            if not _secret(id_token):
                raise ContractError(
                    "CHATGPT_OAUTH_IDENTITY: the OpenAI identity could not be verified"
                )
            jwks = self.transport.request(JWKS_PATH, deadline=deadline)
            subject = _identity(id_token, client_id, nonce, jwks)
            if previous is not None and not compare_digest(subject, previous.subject):
                raise ContractError(
                    "CHATGPT_OAUTH_IDENTITY: refreshed identity differs from the selected account"
                )
        return ChatGPTCredentials(
            issuer=ISSUER,
            subject=subject,
            client_id=client_id,
            scopes=scopes,
            access_token=access,
            refresh_token=renewal,
            id_token=id_token,
            expires_at=received + expires,
            earliest_refresh_at=earliest,
        )
