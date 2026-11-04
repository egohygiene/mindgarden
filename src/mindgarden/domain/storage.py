"""Provider-neutral immutable content port, separate from logical source records."""

from enum import StrEnum
import re
from typing import Protocol

from .validation import ContractError


class ContentState(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    UNAVAILABLE = "unavailable"
    CORRUPTED = "corrupted"
    UNSUPPORTED = "unsupported"


def content_digest(content_id: str) -> str:
    if not isinstance(content_id, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", content_id):
        raise ContractError("CONTENT_ID: use an immutable SHA-256 content identity")
    return content_id[7:]


class BlobStorage(Protocol):
    """Captured bytes cross this port; acquisition and semantic curation do not."""

    def capabilities(self) -> dict: ...
    def state(self, content_id: str) -> ContentState: ...
    def get(self, content_id: str) -> bytes: ...
    def put(self, content: bytes) -> str: ...
