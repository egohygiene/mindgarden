"""Private local OAuth setup; ordinary capture uses only a valid cached token."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import time

from ..domain.contracts import canonical_json, strict_json
from ..domain.validation import ContractError
from .registry_files import control_path, private_parent

READ_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def private_path(path):
    path = control_path(Path(path))
    if (
        os.name != "posix"
        or ".garden" in path.parts
        or any((parent / ".git").exists() for parent in path.parents)
    ):
        raise ContractError(
            "CAPTURE_AUTH_LOCATION: use verified private POSIX storage outside Git and garden records"
        )
    if path.exists() and (
        not path.is_file()
        or path.stat().st_mode & 0o077
        or path.stat().st_uid != os.getuid()
        or path.stat().st_size > 65536
    ):
        raise ContractError(
            "CAPTURE_AUTH_PERMISSIONS: credential files need owned mode-0600 storage"
        )
    return path


def credential_document(path):
    path = private_path(path)
    try:
        value = strict_json(path.read_bytes())
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (OSError, ContractError, ValueError):
        raise ContractError(
            "CAPTURE_AUTH_CONFIG: local credential configuration is missing or invalid"
        ) from None


def token_envelope(path):
    value = credential_document(path)
    if (
        value.get("schema") != "mindgarden.local-drive-credential/v1"
        or value.get("scopes") != [READ_SCOPE]
        or not isinstance(value.get("credentials"), dict)
        or value["credentials"].get("token_uri") != TOKEN_URI
    ):
        raise ContractError(
            "CAPTURE_AUTH_CONFIG: select the owned read-only Drive credential file"
        )
    return value


def cached_access_token(*, clock=lambda: datetime.now(timezone.utc)):
    bearer, filename = (
        os.environ.get("MINDGARDEN_DRIVE_ACCESS_TOKEN"),
        os.environ.get("MINDGARDEN_DRIVE_TOKEN_FILE"),
    )
    if bearer and filename:
        raise ContractError(
            "CAPTURE_AUTH_CONFIG: select one explicit local credential mode"
        )
    if bearer:
        return bearer
    if not filename:
        raise ContractError(
            "CAPTURE_AUTH: configure local Drive credentials outside portable records"
        )
    value = token_envelope(filename)["credentials"]
    try:
        expiry = datetime.fromisoformat(value["expiry"].replace("Z", "+00:00"))
        token = value["token"]
        if (
            expiry.tzinfo is None
            or expiry <= clock() + timedelta(seconds=30)
            or not isinstance(token, str)
            or not token
            or any(character in token for character in "\r\n")
        ):
            raise ValueError()
        return token
    except (KeyError, TypeError, ValueError):
        raise ContractError(
            "CAPTURE_AUTH_EXPIRED: refresh the private credential with capture authorize --refresh"
        ) from None


def authorize(
    client_file,
    token_file,
    *,
    refresh=False,
    flow_factory=None,
    credentials_factory=None,
    token_request=None,
):
    target = private_path(token_file)
    existing = token_envelope(target) if target.exists() else None
    try:
        if (
            flow_factory is None
            or refresh
            and (credentials_factory is None or token_request is None)
        ):
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            flow_factory = flow_factory or InstalledAppFlow.from_client_config
            credentials_factory = (
                credentials_factory or Credentials.from_authorized_user_info
            )
            token_request = token_request or Request()
    except ImportError:
        raise ContractError(
            "CAPTURE_AUTH_SDK: install the optional requirements/drive.txt setup dependency"
        ) from None
    if refresh:
        if existing is None:
            raise ContractError(
                "CAPTURE_AUTH_CONFIG: authorize the desktop application before refreshing"
            )
        credential = credentials_factory(existing["credentials"], scopes=[READ_SCOPE])
        started, attempts = time.monotonic(), 0

        def bounded_request(url, method="GET", **kwargs):
            nonlocal attempts
            attempts += 1
            remaining = 30 - (time.monotonic() - started)
            if url != TOKEN_URI or method != "POST" or attempts > 3 or remaining <= 0:
                raise ContractError(
                    "CAPTURE_AUTH_BUDGET: bounded Google token refresh is unavailable"
                )
            kwargs["timeout"] = min(10, remaining)
            kwargs["allow_redirects"] = False
            return token_request(url=url, method=method, **kwargs)

        try:
            credential.refresh(bounded_request)
        except Exception:
            raise ContractError(
                "CAPTURE_AUTH_REFRESH: local token refresh failed; reauthorize if necessary"
            ) from None
    else:
        if client_file is None:
            raise ContractError(
                "CAPTURE_AUTH_CONFIG: supply the downloaded private desktop OAuth client file"
            )
        client = credential_document(client_file)
        installed = client.get("installed", {})
        if (
            not isinstance(installed, dict)
            or installed.get("token_uri") != TOKEN_URI
            or installed.get("auth_uri")
            not in {
                "https://accounts.google.com/o/oauth2/auth",
                "https://accounts.google.com/o/oauth2/v2/auth",
            }
            or not isinstance(installed.get("client_id"), str)
            or not isinstance(installed.get("client_secret"), str)
        ):
            raise ContractError(
                "CAPTURE_AUTH_CONFIG: use an installed-app client with canonical Google OAuth endpoints"
            )
        if (
            existing is not None
            and existing["credentials"].get("client_id") != installed["client_id"]
        ):
            raise ContractError(
                "CAPTURE_AUTH_CONFIG: preserve another application's credential and select a new file"
            )
        try:
            flow = flow_factory(
                client, scopes=[READ_SCOPE], autogenerate_code_verifier=True
            )
            original_request = flow.oauth2session.request

            def bounded_exchange(method, url, *args, **kwargs):
                if url != TOKEN_URI or method.upper() != "POST":
                    raise ContractError(
                        "CAPTURE_AUTH_ENDPOINT: OAuth setup may call only the Google token endpoint"
                    )
                kwargs.update(timeout=10, allow_redirects=False)
                return original_request(method, url, *args, **kwargs)

            flow.oauth2session.request = bounded_exchange
            credential = flow.run_local_server(
                host="127.0.0.1", port=0, timeout_seconds=180, prompt="consent"
            )
        except Exception:
            raise ContractError(
                "CAPTURE_AUTH_SETUP: bounded desktop authorization did not complete"
            ) from None
    try:
        saved = strict_json(credential.to_json())
        if (
            not isinstance(saved, dict)
            or saved.get("token_uri") != TOKEN_URI
            or not isinstance(saved.get("token"), str)
            or not saved["token"]
            or not isinstance(saved.get("expiry"), str)
        ):
            raise ValueError()
        encoded = canonical_json(
            {
                "schema": "mindgarden.local-drive-credential/v1",
                "scopes": [READ_SCOPE],
                "credentials": saved,
            }
        )
        if len(encoded) > 65536:
            raise ValueError()
    except (ContractError, TypeError, ValueError):
        raise ContractError(
            "CAPTURE_AUTH_CONFIG: authorization returned invalid local credentials"
        ) from None
    private_parent(target)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".drive-credential-", dir=target.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {
        "status": "credential-refreshed" if refresh else "credential-created",
        "scopes": [READ_SCOPE],
        "source_capture": "not performed",
    }


def run_authorize(arguments):
    print(
        json.dumps(
            authorize(
                arguments.client_file, arguments.token_file, refresh=arguments.refresh
            ),
            sort_keys=True,
        )
    )
    return 0
