"""Inspectable local information-flow decisions; no organization assurance claim."""

from .contracts import canonical_json, digest_bytes
from .scope import POLICY_REFERENCE, inherit_scope, validate_scope
from .validation import ContractError

OPERATIONS = ("read", "query", "write", "route", "export", "declassify")


def decide_scope(operation: str, scopes: list[dict], *, destination: dict | None = None,
                 review: dict | None = None, authority: dict | None = None) -> dict:
    """Join requirements and explain denials without returning supplied labels/text.

    A policy allow is not runtime, encryption or identity-provider evidence.
    Declassification requires an unavailable owning organization contract.
    """
    selected = None
    outcome, code = "allow", "SCOPE_JOIN"
    try:
        if operation not in OPERATIONS:
            raise ContractError("SCOPE_OPERATION: unsupported policy operation")
        selected = inherit_scope(scopes)
        if destination is not None:
            validate_scope(destination)
        if operation == "declassify":
            reviewed = (isinstance(review, dict) and review.get("state") == "approved"
                        and isinstance(authority, dict) and authority.get("kind") == "human"
                        and authority.get("id") in review.get("reviewers", [])
                        and review.get("rationale") and review.get("reviewed_at"))
            outcome, code = (("unavailable", "DECLASSIFICATION_UNAVAILABLE") if reviewed else
                             ("review-required", "REVIEW_AUTHORITY"))
        elif operation in {"write", "route", "export"}:
            if destination is None:
                raise ContractError("OUTPUT_SCOPE: an explicit destination is required")
            joined = inherit_scope([selected, destination])
            if joined["visibility"] != destination["visibility"]:
                raise ContractError("OUTPUT_SCOPE: destination cannot receive contributing restrictions")
            if joined["persistence"] == "encrypted-vault":
                outcome, code = "unavailable", "RUNTIME_UNVERIFIED"
            elif joined["persistence"] != destination["persistence"]:
                raise ContractError("OUTPUT_SCOPE: destination persistence would weaken restrictions")
            elif joined["execution"] != destination["execution"]:
                raise ContractError("EXECUTION_DENIED: destination execution would weaken restrictions")
            elif destination["visibility"] == "public" and joined["publication"] != "publishable":
                raise ContractError("PUBLICATION_DENIED: public output needs independent publication authority")
            else:
                code = "SCOPE_DESTINATION"
            selected = joined
    except ContractError as error:
        outcome, code = "deny", str(error).partition(":")[0]
    return {"schema":"mindgarden.scope-decision/v1", "operation":operation if operation in OPERATIONS else "unsupported",
            "policy":dict(POLICY_REFERENCE), "outcome":outcome, "code":code, "scope":selected,
            "assurance":"not-asserted", "inputs_sha256":digest_bytes(canonical_json({
                "operation":operation, "scopes":scopes, "destination":destination,
                "review":review, "authority":authority}))}


def require_destination(scopes: list[dict], destination: dict, *, operation: str = "write") -> dict:
    decision = decide_scope(operation, scopes, destination=destination)
    if decision["outcome"] != "allow":
        raise ContractError(decision["code"] + ": explicit output boundary cannot satisfy the contributing policy")
    return decision["scope"]


def policy_capabilities() -> dict:
    return {"schema":"mindgarden.policy-capabilities/v1", "policy":dict(POLICY_REFERENCE),
            "decision_status":"proposed-local-reference", "operations":list(OPERATIONS),
            "organization_policy":"unavailable", "runtime_assurance":"unavailable",
            "declassification":"unavailable", "identity_authentication":"not-implemented",
            "upstream":["https://github.com/egohygiene/hygiene/issues/39",
                        "https://github.com/egohygiene/hygiene/issues/40",
                        "https://github.com/egohygiene/realm/issues/25"]}
