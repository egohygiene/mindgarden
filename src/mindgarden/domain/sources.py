"""Captured-source normalization contract, independent of acquisition and models."""

from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import parse_qsl, urlsplit

from .validation import ContractError


def validate_origin(value: str) -> str:
    """Portable logical origin; credentials and local acquisition paths stay local."""
    try:
        parsed = urlsplit(value)
    except (TypeError, ValueError) as error:
        raise ContractError("SOURCE_ORIGIN_UNSAFE: supply a durable credential-free source identity") from error
    credentials = {"access_token", "api_key", "key", "token", "signature", "x-amz-signature",
                   "x-goog-signature", "x-amz-credential", "x-goog-credential"}
    if (parsed.scheme not in {"https", "http", "urn"} or parsed.username is not None
            or parsed.password is not None or parsed.scheme in {"https", "http"} and not parsed.hostname
            or any(key.lower() in credentials for key, _value in parse_qsl(parsed.query))):
        raise ContractError("SOURCE_ORIGIN_UNSAFE: use a credential-free HTTP(S) or URN identity; keep physical locations in local bindings")
    return value


def normalize_text(value: str) -> str:
    normalized = value.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    return normalized.rstrip("\n") + "\n"


@dataclass(frozen=True)
class NormalizedUnit:
    identity: str
    content: bytes
    media_type: str = "text/plain"
    locators: tuple[str, ...] = ("artifact",)
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedBundle:
    units: tuple[NormalizedUnit, ...]
    transformations: tuple[dict, ...]
    metadata: dict = field(default_factory=dict)


class SourceAdapter(Protocol):
    adapter_id: str
    version: str
    supported_inputs: frozenset[tuple[str, str | None]]

    def normalize(self, captured: bytes, metadata: dict) -> NormalizedBundle: ...


class AdapterRegistry:
    """Explicit registration only: no ambient entrypoint loading or network discovery."""

    def __init__(self, adapters: tuple[SourceAdapter, ...] = ()) -> None:
        self.adapters: dict[str, SourceAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: SourceAdapter) -> None:
        if adapter.adapter_id in self.adapters:
            raise ContractError("ADAPTER_DUPLICATE: adapter identity is already registered")
        self.adapters[adapter.adapter_id] = adapter

    def select(self, media_type: str, manifest_version: str | None,
               adapter_id: str | None = None) -> SourceAdapter:
        matches = [adapter for adapter in self.adapters.values()
                   if (media_type, manifest_version) in adapter.supported_inputs
                   and (adapter_id is None or adapter.adapter_id == adapter_id)]
        if len(matches) != 1:
            raise ContractError("ADAPTER_UNSUPPORTED: select one supported media/manifest adapter")
        return matches[0]
