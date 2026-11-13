"""First-pass evidence from exact session grants, independent of knowledge approval."""

from copy import deepcopy

from ..domain.contracts import canonical_json, digest_bytes
from ..domain.garden import evidence_bytes
from ..domain.source_access import source_grants
from ..domain.validation import ContractError
from .query import QueryContext


def resolve_source_evidence(
    context: QueryContext, source: dict, locator: str, content_sha256: str
) -> dict:
    return resolve_source_evidence_batch(
        context,
        [{"source": source, "locator": locator, "content_sha256": content_sha256}],
    )[0]


def resolve_source_evidence_batch(context, citations):
    """One verified input snapshot; exact grants/live authority gate every row.

    Never cache across plans or sessions. Validate all explicit grants before
    opening any body; callers cannot supply their own supposedly verified view.
    """
    context.require("source-evidence")
    selected = deepcopy(citations)
    grants = source_grants(context.session)
    if not selected or len(selected) > context.session["budgets"]["max_candidates"]:
        raise ContractError("SOURCE_GRANT: source selection exceeds explicit authority")
    try:
        if any(
            set(item) != {"source", "locator", "content_sha256"}
            or item["source"]["revision"] is None
            or grants.get((item["source"]["garden"], item["source"]["id"]))
            != item["source"]["revision"]
            for item in selected
        ):
            raise ValueError()
    except (KeyError, TypeError, ValueError) as error:
        raise ContractError(
            "SOURCE_GRANT: exact selected evidence is unavailable"
        ) from error
    owners = context.snapshots()
    result = [_resolve_selected_evidence(context, owners, **item) for item in selected]
    context.check_live()
    return result


def _resolve_selected_evidence(context, owners, source, locator, content_sha256):
    context.require("source-evidence")
    grants = source_grants(context.session)
    if (
        source["revision"] is None
        or grants.get((source["garden"], source["id"])) != source["revision"]
    ):
        raise ContractError("SOURCE_GRANT: exact selected evidence is unavailable")
    owner = owners.get(source["garden"])
    record = owner.records.get(source["id"]) if owner is not None else None
    if (
        record is None
        or record["schema"] != "mindgarden.source/v1"
        or record["kind"] != "normalized"
        or "sha256:" + record["artifact"]["sha256"] != source["revision"]
    ):
        raise ContractError("SOURCE_GRANT: exact selected evidence is unavailable")
    selected = evidence_bytes(owner.contents[source["id"]], locator)
    if digest_bytes(selected) != content_sha256:
        raise ContractError("QUERY_INTEGRITY: exact source evidence checksum differs")
    try:
        text = selected.decode("utf8")
    except UnicodeError as error:
        raise ContractError("EVIDENCE_FORMAT: source evidence is not UTF-8") from error
    result = {
        "schema": "mindgarden.evidence/v1",
        "source": source,
        "locator": locator,
        "content_sha256": content_sha256,
        "trust": "untrusted-evidence",
        "authorization": "session-source-grant",
        "text": text,
        "source_identity": record.get("x-source-identity", source["id"]),
        "source_review": record["review"],
        "scope": context.output_scope([context.scope_for(source["garden"], record)]),
        "origin": record.get("x-adapter", {}).get("metadata", {}),
        "lineage": record["inputs"],
        "authorized_by": [{"reference": source, "review": record["review"]}],
    }
    if len(canonical_json(result)) > context.session["budgets"]["max_context_bytes"]:
        raise ContractError(
            "CONTEXT_BUDGET: source evidence exceeds the session budget"
        )
    return context.finalize(result)
