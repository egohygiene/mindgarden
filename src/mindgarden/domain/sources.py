"""Captured-source normalization contract, independent of acquisition and models."""

from dataclasses import dataclass, field
from copy import deepcopy
import re
from typing import Protocol
from urllib.parse import parse_qsl, urlsplit

from .validation import ContractError
from .contracts import ContractRegistry, canonical_json, digest_bytes, strict_json


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


DEFAULT_LIMITS = {"capture_bytes": 100 * 1024 * 1024, "units": 20000,
                  "unit_bytes": 64 * 1024 * 1024, "normalized_bytes": 256 * 1024 * 1024,
                  "metadata_bytes": 2_000_000}


def describe_adapter(adapter: SourceAdapter) -> dict:
    """Versioned data declaration; old explicit adapters receive bounded defaults."""
    try:
        inputs = sorted(adapter.supported_inputs, key=lambda pair: (pair[0], pair[1] or ""))
        declaration = {"schema": "mindgarden.source-adapter/v1", "id": adapter.adapter_id,
                       "version": adapter.version, "protocol": "captured-bytes/v1",
                       "inputs": [{"media_type": media, "manifest_version": version}
                                  for media, version in inputs],
                       "limits": {**DEFAULT_LIMITS, **getattr(adapter, "limits", {})}}
        errors = ContractRegistry().errors(declaration, "source-adapter")
        if errors or not callable(adapter.normalize):
            raise ValueError()
        return declaration
    except (AttributeError, TypeError, ValueError) as error:
        raise ContractError("ADAPTER_DECLARATION: declare a version, supported pairs and positive bounded limits") from error


def _json_metadata(value: object, maximum: int) -> bytes:
    """Round-trip strict JSON, rejecting Python-only values and coerced keys."""
    try:
        content = canonical_json(value)
        if strict_json(content) != value or len(content) > maximum:
            raise ValueError()
        return content
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ContractError("ADAPTER_METADATA: output must be bounded portable JSON") from error


def normalize_source(adapter: SourceAdapter, captured: bytes, metadata: dict) -> NormalizedBundle:
    """Enforce the adapter boundary before any record or blob is written."""
    from .garden import evidence_bytes

    limits = describe_adapter(adapter)["limits"]
    if len(captured) > limits["capture_bytes"]:
        raise ContractError("SOURCE_OVERSIZED: captured bytes exceed declared adapter limit")
    supplied = deepcopy(metadata)
    try:
        bundle = adapter.normalize(captured, supplied)
    except ContractError:
        raise
    except Exception as error:
        raise ContractError("ADAPTER_FAILURE: normalization failed; no successful bundle produced") from error
    if supplied != metadata:
        raise ContractError("ADAPTER_MUTATION: adapters must not modify supplied metadata")
    if (not isinstance(bundle, NormalizedBundle) or not isinstance(bundle.units, tuple)
            or not isinstance(bundle.transformations, tuple) or not isinstance(bundle.metadata, dict)):
        raise ContractError("ADAPTER_OUTPUT: return a NormalizedBundle with explicit units and transformations")
    if len(bundle.units) > limits["units"]:
        raise ContractError("ADAPTER_LIMIT: normalized unit count exceeds declaration")
    _json_metadata(bundle.metadata, limits["metadata_bytes"])
    _json_metadata(list(bundle.transformations), limits["metadata_bytes"])
    for transform in bundle.transformations:
        if (not isinstance(transform, dict) or set(transform) != {"name", "version", "parameters"}
                or not isinstance(transform["name"], str) or not transform["name"]
                or not isinstance(transform["version"], str) or not transform["version"]
                or not isinstance(transform["parameters"], dict)):
            raise ContractError("ADAPTER_TRANSFORMATION: declare ordered named versioned transformations")
    seen, total = set(), 0
    for unit in bundle.units:
        if (not isinstance(unit, NormalizedUnit) or not isinstance(unit.identity, str)
                or not unit.identity or len(unit.identity) > 2048
                or unit.identity.startswith(("/", "\\", "file:", "./", "../"))
                or re.match(r"^[A-Za-z]:[\\/]", unit.identity)
                or any(ord(char) < 32 for char in unit.identity)
                or not isinstance(unit.content, bytes) or not isinstance(unit.metadata, dict)
                or not isinstance(unit.media_type, str) or not re.fullmatch(r"[\w.+-]+/[\w.+-]+", unit.media_type)
                or not isinstance(unit.locators, tuple) or not unit.locators
                or any(not isinstance(locator, str) for locator in unit.locators)):
            raise ContractError("ADAPTER_OUTPUT: units need portable identities, bytes, media types and evidence locators")
        if unit.identity in seen:
            raise ContractError("SOURCE_DUPLICATE: adapter emitted a duplicate normalized identity")
        seen.add(unit.identity)
        total += len(unit.content)
        if len(unit.content) > limits["unit_bytes"] or total > limits["normalized_bytes"]:
            raise ContractError("ADAPTER_LIMIT: normalized bytes exceed declaration")
        _json_metadata(unit.metadata, limits["metadata_bytes"])
        for locator in unit.locators:
            evidence_bytes(unit.content, locator)
    return bundle


def check_adapter_conformance(adapter: SourceAdapter, captured: bytes, metadata: dict) -> dict:
    """Consumer fixture harness; successful empty output differs from an exception.

    This calls trusted adapter code twice. It is not an operating-system sandbox.
    """
    first = normalize_source(adapter, captured, metadata)
    second = normalize_source(adapter, captured, metadata)
    if first != second:
        raise ContractError("ADAPTER_NONDETERMINISTIC: identical explicit inputs produced different evidence")
    return {"adapter": describe_adapter(adapter), "captured_sha256": digest_bytes(captured),
            "units": [{"identity": unit.identity, "sha256": digest_bytes(unit.content),
                       "locators": list(unit.locators)} for unit in sorted(first.units, key=lambda unit: unit.identity)],
            "status": "success"}


class AdapterRegistry:
    """Explicit registration only: no ambient entrypoint loading or network discovery."""

    def __init__(self, adapters: tuple[SourceAdapter, ...] = ()) -> None:
        self.adapters: dict[str, SourceAdapter] = {}
        self.declarations: dict[str, dict] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: SourceAdapter) -> None:
        declaration = describe_adapter(adapter)
        if adapter.adapter_id in self.adapters:
            raise ContractError("ADAPTER_DUPLICATE: adapter identity is already registered")
        self.adapters[adapter.adapter_id] = adapter
        self.declarations[adapter.adapter_id] = declaration

    def select(self, media_type: str, manifest_version: str | None,
               adapter_id: str | None = None) -> SourceAdapter:
        if any(describe_adapter(adapter) != self.declarations[identity]
               for identity, adapter in self.adapters.items()):
            raise ContractError("ADAPTER_CHANGED: re-register changed declarations in a new explicit registry")
        matches = [adapter for adapter in self.adapters.values()
                   if (media_type, manifest_version) in adapter.supported_inputs
                   and (adapter_id is None or adapter.adapter_id == adapter_id)]
        if len(matches) != 1:
            raise ContractError("ADAPTER_UNSUPPORTED: select one supported media/manifest adapter")
        return matches[0]
