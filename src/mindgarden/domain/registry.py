"""Machine-local management metadata over the existing binding/scope contracts."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import sys
from typing import Mapping

from .contracts import ContractRegistry, canonical_json, digest_bytes
from .scope import validate_scope
from .validation import ContractError

MAX_GARDENS = 100
MAX_VIEWS = 100
MAX_VIEW_EPOCHS = 1000


def registry_location(platform: str, user_home: str, environment: Mapping[str, str]) -> str:
    """Resolve only a configuration location, never discover garden contents."""
    if platform == "win32":
        base = PureWindowsPath(environment.get("LOCALAPPDATA") or environment.get("APPDATA") or user_home)
        if not base.is_absolute() or ".." in base.parts:
            raise ContractError("REGISTRY_LOCATION: supply an absolute platform configuration location")
        return str(base / "Mindgarden" / "registry.json")
    home_path = PurePosixPath(user_home)
    if platform == "darwin":
        base = home_path / "Library" / "Application Support"
    elif platform.startswith("linux"):
        base = PurePosixPath(environment.get("XDG_CONFIG_HOME") or str(home_path / ".config"))
    else:
        raise ContractError("REGISTRY_PLATFORM: the platform configuration convention is unsupported")
    if not base.is_absolute() or ".." in base.parts:
        raise ContractError("REGISTRY_LOCATION: supply an absolute platform configuration location")
    return str(base / "mindgarden" / "registry.json")


def default_registry_path() -> Path:
    import os

    return Path(registry_location(sys.platform, str(Path.home()), os.environ))


def empty_bindings() -> dict:
    return {"schema": "mindgarden.local-bindings/v1", "gardens": [], "vaults": [], "revoked_sessions": []}


def empty_metadata() -> dict:
    return {"schema": "mindgarden.registry/v1", "registrations": [], "views": [], "view_epochs": {}}


def validate_registry(document: dict, *, managed: bool = True) -> None:
    if ContractRegistry().errors(document, "local-bindings"):
        raise ContractError("REGISTRY_INVALID: registry or binding contract is unsupported")
    gardens = [item["id"] for item in document["gardens"]]
    vaults = [item["id"] for item in document["vaults"]]
    if (len(set(gardens)) != len(gardens) or len(set(vaults)) != len(vaults) or len(gardens) > MAX_GARDENS):
        raise ContractError("REGISTRY_CONFLICT: duplicate identities or registry budget exceeded")
    for item in document["gardens"]:
        validate_scope(item["scope"])
    if "registry" not in document:
        if managed:
            raise ContractError("REGISTRY_UNINITIALIZED: preview registry init to adopt explicit bindings")
        return
    metadata = document["registry"]
    registrations = [item["garden"] for item in metadata["registrations"]]
    view_ids = [view["id"] for view in metadata["views"]]
    if (len(set(registrations)) != len(registrations) or set(registrations) != set(gardens)
            or len(set(view_ids)) != len(view_ids) or len(view_ids) > MAX_VIEWS
            or len(metadata["view_epochs"]) > MAX_VIEW_EPOCHS):
        raise ContractError("REGISTRY_INVALID: management metadata differs from explicit bindings")
    for view in metadata["views"]:
        if (not set(view["gardens"]) <= set(gardens)
                or metadata["view_epochs"].get(view["id"]) != view["generation"]):
            raise ContractError("REGISTRY_VIEW: named view membership or generation is invalid")


def selected_view(document: dict, view_id: str) -> dict:
    """Read only the requested control view; unrelated denied metadata is inert."""
    metadata = document.get("registry")
    if not isinstance(metadata, dict) or metadata.get("schema") != "mindgarden.registry/v1":
        raise ContractError("REGISTRY_VIEW: a supported machine-local registry view is required")
    views = metadata.get("views")
    if not isinstance(views, list):
        raise ContractError("REGISTRY_VIEW: requested view is unavailable")
    matches = [view for view in views if isinstance(view, dict) and view.get("id") == view_id]
    if len(matches) != 1 or ContractRegistry().errors(matches[0], "registry-view"):
        raise ContractError("REGISTRY_VIEW: requested view is unavailable or ambiguous")
    view = matches[0]
    epochs = metadata.get("view_epochs")
    declared = {item.get("id") for item in document.get("gardens", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
    if (not isinstance(epochs, dict) or epochs.get(view_id) != view["generation"]
            or not set(view["gardens"]) <= declared):
        raise ContractError("REGISTRY_VIEW: requested view has stale or unavailable membership")
    return view


def view_reference(view: dict) -> dict:
    return {"id": view["id"], "revision": "sha256:" + digest_bytes(canonical_json(view))}


def verify_session_view(document: dict, session: dict) -> None:
    reference = session.get("registry_view")
    if reference is None:
        return
    try:
        view = selected_view(document, reference["id"])
        if (reference != view_reference(view)
                or {item["garden"] for item in session["readable"]} != set(view["gardens"])):
            raise ValueError()
    except (ContractError, KeyError, TypeError, ValueError) as error:
        raise ContractError("SESSION_VIEW_STALE: named view changed or was removed; refresh explicit session authority") from error


def require_registry_runtime(scope: dict) -> None:
    validate_scope(scope)
    if scope["visibility"] == "restricted" or scope["persistence"] == "encrypted-vault":
        raise ContractError("REGISTRY_RUNTIME: verified encrypted/restricted registration is unavailable")
