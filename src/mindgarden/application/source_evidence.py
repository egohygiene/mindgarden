"""First-pass evidence from exact session grants, independent of knowledge approval."""

from ..domain.contracts import canonical_json, digest_bytes
from ..domain.garden import evidence_bytes
from ..domain.source_access import source_grants
from ..domain.validation import ContractError
from .query import QueryContext


def resolve_source_evidence(
    context: QueryContext, source: dict, locator: str, content_sha256: str
) -> dict:
    context.require("source-evidence")
    grants = source_grants(context.session)
    if grants.get((source["garden"], source["id"])) != source["revision"]:
        raise ContractError("SOURCE_GRANT: exact selected evidence is unavailable")
    owner = context.snapshots().get(source["garden"])
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
