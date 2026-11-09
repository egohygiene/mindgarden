"""Provider-neutral immutable content port, separate from logical source records."""

from enum import StrEnum
import re
from typing import Callable, Protocol

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


class BackupStorage(BlobStorage, Protocol):
    """Optional capability: implementations must declare their bounds honestly."""

    def audit(self, expected: set[str] | None = None) -> dict: ...
    def export_bundle(self) -> bytes: ...
    def restore_bundle(self, content: bytes, reviewed_sha256: str) -> bool: ...


class StorageAdapters:
    """Explicit caller-owned factories. No entry-point, provider or credential discovery."""

    def __init__(self):
        self.factories: dict[str, Callable] = {}

    def register(self, adapter_id: str, factory: Callable) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,79}", adapter_id) or not callable(factory) or adapter_id in self.factories:
            raise ContractError("STORAGE_ADAPTER: supply a unique explicit adapter factory")
        self.factories[adapter_id] = factory

    def remove(self, adapter_id: str) -> None:
        self.factories.pop(adapter_id, None)

    def open(self, binding: dict, vault_id: str) -> BlobStorage:
        factory = self.factories.get(binding["adapter"])
        if factory is None:
            raise ContractError("STORAGE_UNSUPPORTED: selected storage adapter is not installed")
        from .contracts import ContractRegistry, canonical_json

        try:
            storage = factory(dict(binding), vault_id)
            capabilities = storage.capabilities()
            if (len(canonical_json(capabilities)) > 65536
                    or ContractRegistry().errors(capabilities, "storage-capabilities")
                    or capabilities["adapter"] != binding["adapter"]
                    or any(not callable(getattr(storage, name, None)) for name in ("state", "get", "put"))
                    or any(capabilities[capability] and not callable(getattr(storage, method, None))
                           for capability, method in (("audit", "audit"), ("export", "export_bundle"),
                                                      ("restore", "restore_bundle")))):
                raise ContractError("STORAGE_CAPABILITIES: adapter does not implement its declared port")
        except ContractError:
            raise
        except Exception as error:
            raise ContractError("STORAGE_ADAPTER_FAILURE: explicit adapter failed to open its declared port") from error
        return storage
