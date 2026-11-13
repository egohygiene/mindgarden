"""Optional bounded read-only Drive v3 transport; no token acquisition or writes."""

import re
import time
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from ..domain.contracts import strict_json
from ..domain.validation import ContractError
from .drive_credentials import cached_access_token

FILE_FIELDS = "id,name,mimeType,version,modifiedTime,size,md5Checksum,sha256Checksum,parents,trashed,driveId,capabilities(canDownload)"


def file_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", value):
        raise ContractError(
            "CAPTURE_ID: supply an explicit provider file/folder identity"
        )
    return value


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GoogleDriveProvider:
    """Token supplied by the operator's local OAuth tooling, never portable JSON."""

    def __init__(
        self,
        limits,
        *,
        token=None,
        opener=None,
        clock=time.monotonic,
        check_live=lambda: None,
    ):
        credential = token if token is not None else cached_access_token()
        if (
            not isinstance(credential, str)
            or not credential
            or any(character in credential for character in "\r\n")
        ):
            raise ContractError(
                "CAPTURE_AUTH: configure the local read-only Drive credential outside portable records"
            )
        self._token = credential
        self._open = opener or build_opener(ProxyHandler({}), NoRedirect()).open
        self._clock = clock
        self._deadline = clock() + limits["max_seconds"]
        self._limits = dict(limits)
        self._requests = 0
        self._check_live = check_live

    def _get(self, suffix, parameters, maximum):
        self._check_live()
        self._requests += 1
        remaining = self._deadline - self._clock()
        if self._requests > self._limits["max_requests"] or remaining <= 0:
            raise ContractError(
                "CAPTURE_BUDGET: provider request/time budget exhausted"
            )
        request = Request(
            "https://www.googleapis.com/drive/v3/files"
            + suffix
            + "?"
            + urlencode(parameters),
            headers={
                "Authorization": "Bearer " + self._token,
                "Accept-Encoding": "identity",
            },
            method="GET",
        )
        try:
            with self._open(
                request, timeout=min(remaining, self._limits["timeout_seconds"])
            ) as response:
                if getattr(response, "status", 200) != 200:
                    raise ContractError(
                        "CAPTURE_UNAVAILABLE: provider response is not a complete successful result"
                    )
                chunks, size = [], 0
                headers = getattr(response, "headers", {})
                if headers.get("Content-Encoding", "identity") not in {"", "identity"}:
                    raise ContractError(
                        "CAPTURE_FORMAT: unexpected transport content encoding"
                    )
                declared = headers.get("Content-Length")
                if declared is not None and (
                    not declared.isascii()
                    or not declared.isdigit()
                    or int(declared) > maximum
                ):
                    raise ContractError(
                        "CAPTURE_BUDGET: provider response exceeds its declared byte ceiling"
                    )
                read = getattr(response, "read1", response.read)
                while True:
                    content = read(min(65536, maximum + 1 - size))
                    if self._clock() >= self._deadline:
                        raise ContractError(
                            "CAPTURE_BUDGET: provider request/time budget exhausted"
                        )
                    if not content:
                        break
                    chunks.append(content)
                    size += len(content)
                    if size > maximum:
                        raise ContractError(
                            "CAPTURE_BUDGET: provider content exceeds the byte ceiling"
                        )
                self._check_live()
                if declared is not None and size != int(declared):
                    raise ContractError(
                        "CAPTURE_CORRUPTED: provider response ended before its declared size"
                    )
                return b"".join(chunks)
        except HTTPError as error:
            code = {
                401: "CAPTURE_AUTH",
                403: "CAPTURE_DENIED",
                404: "CAPTURE_MISSING",
            }.get(error.code, "CAPTURE_UNAVAILABLE")
            raise ContractError(
                code + ": provider input is unavailable; no source was deleted"
            ) from None
        except (URLError, OSError, TimeoutError, HTTPException):
            raise ContractError(
                "CAPTURE_UNAVAILABLE: bounded provider read failed; retain the checkpoint"
            ) from None

    def stat(self, identity):
        result = strict_json(
            self._get("/" + file_id(identity), {"fields": FILE_FIELDS}, 1_000_000)
        )
        if not isinstance(result, dict) or result.get("id") != identity:
            raise ContractError("CAPTURE_PROVIDER: malformed provider metadata")
        return result

    def children(self, identity):
        token, seen, result = None, set(), []
        while True:
            query = {
                "q": "'" + file_id(identity) + "' in parents and trashed = false",
                "spaces": "drive",
                "corpora": "user",
                "pageSize": 100,
                "fields": "nextPageToken,incompleteSearch,files(" + FILE_FIELDS + ")",
            }
            if token is not None:
                query["pageToken"] = token
            page = strict_json(self._get("", query, 1_000_000))
            if (
                not isinstance(page, dict)
                or page.get("incompleteSearch", False)
                or not isinstance(page.get("files"), list)
            ):
                raise ContractError(
                    "CAPTURE_INCOMPLETE: provider listing does not prove complete selected coverage"
                )
            result.extend(page["files"])
            if len(result) > self._limits["max_files"]:
                raise ContractError(
                    "CAPTURE_BUDGET: selected listing exceeds the file/folder ceiling"
                )
            token = page.get("nextPageToken")
            if not token:
                return result
            if not isinstance(token, str) or token in seen:
                raise ContractError(
                    "CAPTURE_PROVIDER: repeated or malformed pagination token"
                )
            seen.add(token)

    def read(self, item, media_type):
        identity = file_id(item["id"])
        parameters = (
            {"mimeType": media_type}
            if media_type != item["mimeType"]
            else {"alt": "media"}
        )
        suffix = "/" + identity + ("/export" if "mimeType" in parameters else "")
        return self._get(suffix, parameters, self._limits["max_file_bytes"])


def provider_metadata(item):
    if not isinstance(item, dict) or not all(
        isinstance(item.get(key), str) and item[key]
        for key in ("id", "name", "mimeType", "version")
    ):
        raise ContractError(
            "CAPTURE_PROVIDER: file metadata lacks explicit identity/type/version"
        )
    file_id(item["id"])
    if (
        len(item["name"]) > 1024
        or len(item["mimeType"]) > 200
        or len(item["version"]) > 32
        or not isinstance(item.get("parents", []), list)
        or len(item.get("parents", [])) > 16
        or any(not isinstance(parent, str) for parent in item.get("parents", []))
        or not isinstance(item.get("capabilities", {}), dict)
    ):
        raise ContractError(
            "CAPTURE_PROVIDER: bounded metadata fields have incompatible types"
        )
    for parent in item.get("parents", []):
        file_id(parent)
    for key, width in (("md5Checksum", 32), ("sha256Checksum", 64)):
        if key in item and (
            not isinstance(item[key], str)
            or not re.fullmatch("[0-9a-f]{" + str(width) + "}", item[key])
        ):
            raise ContractError("CAPTURE_PROVIDER: invalid declared checksum")
    if "size" in item and (
        not isinstance(item["size"], str)
        or not re.fullmatch(r"[0-9]{1,20}", item["size"])
        or len(item["size"]) > 20
    ):
        raise ContractError("CAPTURE_PROVIDER: invalid declared size")
    if (
        not re.fullmatch(r"[0-9]{1,32}", item["version"])
        or item.get("trashed")
        or item.get("driveId")
    ):
        raise ContractError(
            "CAPTURE_UNAVAILABLE: trashed/shared-drive or incompatible metadata is outside this checkpoint"
        )
    # No owner, description, arbitrary link or credential is copied into state.
    selected = {
        key: item[key]
        for key in (
            "id",
            "name",
            "mimeType",
            "version",
            "size",
            "md5Checksum",
            "sha256Checksum",
            "parents",
            "capabilities",
        )
        if key in item
    }
    if "capabilities" in selected:
        selected["capabilities"] = {
            "canDownload": selected["capabilities"].get("canDownload")
        }
    return selected
