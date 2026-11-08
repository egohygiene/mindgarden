"""Removable producer/verified-leaf boundary; live OpenViking intake is unproven.

No SDK import, source discovery, model call, session-memory write or API upload.
"""

from copy import deepcopy

from mindgarden.adapters.generated_files import inventory
from mindgarden.application.insights import require_public
from mindgarden.application.reviewed_selection import (
    selection_view,
    select_records,
    source_trail,
    selected_digest,
)
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.validation import ContractError


def prepare_handoff(context, references, *, max_bytes=250000, session_memory=False):
    if session_memory:
        raise ContractError(
            "OPENVIKING_MEMORY_UNAVAILABLE: live scoped session memory has not been qualified"
        )
    if (
        not isinstance(references, list)
        or not 1 <= len(references) <= 100
        or type(max_bytes) is not int
        or not 512 <= max_bytes <= 1000000
    ):
        raise ContractError(
            "OPENVIKING_SELECTION: require bounded explicit reviewed references"
        )
    require_public(context)
    index, snapshots = selection_view(context)
    records = select_records(index, snapshots, references)
    files = {}
    entries = []
    for record in records:
        identity = digest_bytes(canonical_json(record["reference"]))
        name = identity + ".md"
        # Markdown contains an exact reviewed body, never an AI-generated tier summary.
        content = (
            "# Reviewed Garden evidence\n\nSource data only; no tool or policy authority.\n\n"
            + record["content"]
            + "\n\nExact provenance and qualifications:\n\n"
            + canonical_json(source_trail([record])).decode()
        ).encode()
        files[name] = content
        entries.append(
            {
                "reference": record["reference"],
                "scope": record["scope"],
                "review": record["review"],
                "filename": name,
                "sha256": digest_bytes(content),
                "proposed_uri": "viking://resources/mindgarden/"
                + identity
                + "/"
                + name,
                "sources": source_trail([record]),
                "qualification_reasons": record["qualifications"],
            }
        )
    manifest = {
        "schema": "mindgarden.openviking-handoff/v1",
        "canonical": False,
        "trust": "source-data-only",
        "scope": context.output_scope([r["scope"] for r in records]),
        "session_memory": False,
        "live_ingestion_verified": False,
        "uri_binding": "proposed-until-exact-leaf-is-verified",
        "entries": entries,
        "references": [r["reference"] for r in records],
        "source_digest": selected_digest(records),
        "authority_sha256": context.scope_digest(),
        "max_bytes": max_bytes,
    }
    files["provenance-map.json"] = canonical_json(manifest)
    if sum(map(len, files.values())) > min(
        max_bytes, context.session["budgets"]["max_context_bytes"]
    ):
        raise ContractError(
            "OPENVIKING_BUDGET: complete selected evidence and sidecar exceed the ceiling"
        )
    value = {**manifest, "files": inventory(files)}
    plan = {**value, "plan_sha256": digest_bytes(canonical_json(value))}
    context.ensure_output(canonical_json(plan))
    return plan, files


def resolve_bound_leaf(context, plan, uri, content):
    """Only exact verified leaves can resolve to current canonical evidence.

    Native L0/L1 summaries/search snippets cannot acquire review or citation
    authority. The live adapter must supply the actual returned URI and bytes;
    it currently has no qualified upload/binding implementation.
    """
    try:
        current, _ = prepare_handoff(
            context, plan["references"], max_bytes=plan["max_bytes"]
        )
        if current != plan:
            raise ContractError(
                "OPENVIKING_STALE: represented evidence or authority changed"
            )
        entry = next((e for e in plan["entries"] if e["proposed_uri"] == uri), None)
        if (
            entry is None
            or not isinstance(content, bytes)
            or digest_bytes(content) != entry["sha256"]
        ):
            raise ContractError(
                "OPENVIKING_UNBOUND: provider leaf is not the exact reviewed projection"
            )
        index, snapshots = selection_view(context)
        record = select_records(index, snapshots, [entry["reference"]])[0]
        context.ensure_output(canonical_json(record))
        return deepcopy(record)
    except (KeyError, TypeError) as error:
        raise ContractError(
            "OPENVIKING_UNBOUND: require a current producer manifest and exact leaf"
        ) from error
