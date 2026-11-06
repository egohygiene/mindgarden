"""Draft local single-user policy, independent of organization ratification."""

from __future__ import annotations

from functools import lru_cache

from .contracts import ContractRegistry, canonical_json, digest_bytes
from .validation import ContractError

LOCAL_POLICY = {
    "id": "mindgarden-local-single-user/v1",
    "rules": {"unknown": "deny", "mixed-organization-personal": "restricted",
              "derived": "all-input-restrictions", "publication": "explicit-human-review",
              "restricted-requirements": ["encrypted-vault", "offline", "never-exportable"],
              "legacy-private": "explicit-personal-or-restricted-mapping"},
}
POLICY_REFERENCE = {"id": LOCAL_POLICY["id"],
                    "revision": "sha256:" + digest_bytes(canonical_json(LOCAL_POLICY))}
LEGACY_VISIBILITY = {"public": "public", "organization": "internal",
                     "personal": "private", "restricted": "private"}
PUBLICATION_ORDER = {"publishable": 0, "review-required": 1, "never-exportable": 2}
EXECUTION_ORDER = {"networked": 0, "controlled-import": 1, "offline": 2}
PERSISTENCE_ORDER = {"git-tracked": 0, "machine-local": 1, "encrypted-vault": 2}


@lru_cache(maxsize=1)
def scope_contracts() -> ContractRegistry:
    """Reuse immutable shipped schemas; never cache user records or decisions."""
    return ContractRegistry()


def validate_scope(scope: dict, visibility: str | None = None) -> dict:
    errors = scope_contracts().errors(scope, "scope")
    if errors:
        raise ContractError("SCOPE_INVALID: supply a complete supported scope contract")
    if scope["policy"] != POLICY_REFERENCE:
        raise ContractError("POLICY_UNSUPPORTED: no supported local implementation for this policy revision")
    if visibility is not None and LEGACY_VISIBILITY[scope["visibility"]] != visibility:
        raise ContractError("SCOPE_CONFLICT: legacy visibility and explicit scope disagree")
    if scope["visibility"] == "restricted" and (
            scope["persistence"] != "encrypted-vault" or scope["execution"] != "offline"
            or scope["publication"] != "never-exportable"):
        raise ContractError("SCOPE_CONFLICT: restricted processing requirements are incomplete")
    return scope


def local_scope(visibility: str = "personal", *, persistence: str | None = None,
                execution: str = "offline", publication: str | None = None) -> dict:
    value = {"schema": "mindgarden.scope/v1", "visibility": visibility,
             "persistence": persistence or ("encrypted-vault" if visibility == "restricted" else "machine-local"),
             "execution": execution,
             "publication": publication or ("never-exportable" if visibility == "restricted" else "review-required"),
             "policy": dict(POLICY_REFERENCE)}
    return validate_scope(value)


def inherit_scope(scopes: list[dict]) -> dict:
    """Join restrictions; organization and personal are not an access ordering."""
    if not scopes:
        raise ContractError("SCOPE_MISSING: derived output needs explicit input policy")
    for scope in scopes:
        validate_scope(scope)
    visibility = {scope["visibility"] for scope in scopes} - {"public"}
    classification = next(iter(visibility)) if len(visibility) == 1 else (
        "public" if not visibility else "restricted")
    if classification == "restricted":
        return local_scope("restricted")
    return local_scope(classification,
                       persistence=max((item["persistence"] for item in scopes), key=PERSISTENCE_ORDER.get),
                       execution=max((item["execution"] for item in scopes), key=EXECUTION_ORDER.get),
                       publication=max((item["publication"] for item in scopes), key=PUBLICATION_ORDER.get))


def record_scope(record: dict, garden_scope: dict) -> dict:
    """Explicit garden mapping supplies missing legacy classification conservatively."""
    validate_scope(garden_scope)
    if "scope" in record:
        own = validate_scope(record["scope"], record.get("visibility"))
    elif record.get("visibility") == "public":
        own = local_scope("public", persistence=garden_scope["persistence"],
                          execution=garden_scope["execution"], publication=garden_scope["publication"])
    elif LEGACY_VISIBILITY[garden_scope["visibility"]] == record.get("visibility"):
        own = garden_scope
    else:
        raise ContractError("SCOPE_MISSING: legacy record requires an explicit classification mapping")
    return inherit_scope([garden_scope, own])
