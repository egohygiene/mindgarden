"""Resolve only exact evidence citations already authorized by reviewed retrieval."""

from argparse import Namespace

from ..domain.contracts import canonical_json, digest_bytes
from ..domain.garden import evidence_bytes
from ..domain.validation import ContractError
from .query import QueryContext
from .retrieval import build_index


def resolve_evidence(context: QueryContext, source: dict, locator: str, content_sha256: str) -> dict:
    citation = {"source": source, "locator": locator, "content_sha256": content_sha256}
    index = build_index(context, projection="evidence")
    authorizers = [record for record in index["records"] if citation in record["sources"]]
    if not authorizers:
        raise ContractError("EVIDENCE_UNAVAILABLE: no permitted reviewed citation authorizes this exact selection")
    snapshots = context.snapshots()
    owner = snapshots[source["garden"]]
    record = owner.records[source["id"]]
    selected = evidence_bytes(owner.contents[source["id"]], locator)
    if digest_bytes(selected) != content_sha256:
        raise ContractError("QUERY_INTEGRITY: exact evidence checksum differs")
    try:
        text = selected.decode("utf8")
    except UnicodeError as error:
        raise ContractError("EVIDENCE_FORMAT: selected bytes are not readable UTF-8 evidence") from error
    result = {"schema": "mindgarden.evidence/v1", **citation, "trust": "untrusted-evidence", "text": text,
              "source_identity": record.get("x-source-identity", source["id"]), "source_review": record["review"],
              "scope": context.output_scope([context.scope_for(source["garden"], record),
                                               *[item["scope"] for item in authorizers]]),
              "origin": record.get("x-adapter", {}).get("metadata", {}), "lineage": record["inputs"],
              "authorized_by": [{"reference": item["reference"], "review": item["review"]} for item in authorizers]}
    if len(canonical_json(result)) > context.session["budgets"]["max_context_bytes"]:
        raise ContractError("CONTEXT_BUDGET: exact evidence and provenance exceed the session byte budget")
    return context.finalize(result)


def run_evidence(arguments: Namespace) -> int:
    context = QueryContext.load(arguments.local_config, arguments.scope)
    result = resolve_evidence(context, {"garden": arguments.garden_id, "id": arguments.source_id,
                                        "revision": arguments.revision}, arguments.locator, arguments.content_sha256)
    content = canonical_json(result)
    context.ensure_output(content)
    print(content.decode(), end="")
    return 0
