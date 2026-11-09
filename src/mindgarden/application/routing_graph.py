"""Exact outgoing graph copies for reviewed private moves; originals are retained."""

from copy import deepcopy

from ..domain.contracts import canonical_json, digest_bytes, strict_json
from ..domain.scope import record_scope
from ..domain.validation import ContractError
from .records import artifact_reference


def incoming_reference_inventory(
    snapshots, bindings, originals, destination, scope, retired
):
    """Report independently reviewed incoming edges without rewriting their intent."""
    targets = {(ref["garden"], ref["id"]) for ref in originals}
    result = []
    for garden, snapshot in sorted(snapshots.items()):
        if bindings.garden(garden)["scope"] != scope:
            continue
        for identity, record in sorted(snapshot.records.items()):
            if (
                record["schema"] != "mindgarden.synapse/v1"
                or record["status"] != "active"
                or record["review"]["state"] != "approved"
                or record_scope(record, scope) != scope
                or (record["target"]["garden"], record["target"]["id"]) not in targets
                or (record["source"]["garden"], record["source"]["id"]) in targets
            ):
                continue
            source_garden, source_id = (
                record["source"]["garden"],
                record["source"]["id"],
            )
            source_owner = snapshots.get(source_garden)
            source = source_owner.records.get(source_id) if source_owner else None
            if (
                source is None
                or (source_garden, source_id) in retired
                or bindings.garden(source_garden)["scope"] != scope
                or source["schema"] != "mindgarden.knowledge/v1"
                or source["status"] != "active"
                or source["review"]["state"] != "approved"
                or record_scope(source, scope) != scope
            ):
                continue
            if len(result) >= 128:
                raise ContractError(
                    "ROUTE_INCOMING_BUDGET: review incoming references in a smaller transition"
                )
            result.append(
                {
                    "reference": artifact_reference(
                        garden, identity, snapshot.hashes[identity]
                    ),
                    "source": record["source"],
                    "historical_target": record["target"],
                    "proposed_canonical_target": destination,
                    "type": record["type"],
                    "directed": record["directed"],
                    "review": record["review"],
                    "state": "separate-reviewed-reference-repair-required",
                    "reason": "exact-historical-reference-retained-no-automatic-retarget",
                }
            )
    return result


def retain_attached_graph(
    files, original, snapshots, destination, scope, request_digest
):
    references = original["claims"] + original["synapses"]
    if len(references) > 128:
        raise ContractError(
            "ROUTE_GRAPH_BUDGET: explicitly split a transfer with more than 128 outgoing attachments"
        )
    owner = snapshots[original["garden"]]
    original_reference = artifact_reference(
        original["garden"], original["id"], owner.hashes[original["id"]]
    )
    path = "knowledge/" + destination["id"] + ".json"
    knowledge = strict_json(files[path])
    knowledge["created"] = original["created"]
    if "x-curation" in original:
        knowledge["x-curation"] = deepcopy(original["x-curation"])
    for field, kind, endpoint in (
        ("claims", "claim", "subject"),
        ("synapses", "synapse", "source"),
    ):
        copied = []
        for reference in original[field]:
            snapshot = snapshots.get(reference["garden"])
            record = snapshot.records.get(reference["id"]) if snapshot else None
            if (
                record is None
                or record["schema"] != "mindgarden." + kind + "/v1"
                or reference["revision"] != "sha256:" + snapshot.hashes[reference["id"]]
                or record[endpoint] != original_reference
            ):
                raise ContractError(
                    "ROUTE_GRAPH_REFERENCE: exact outgoing graph references must resolve to the original subject"
                )
            binding_scope = scope  # routing already joined original and target policies
            if record_scope(record, binding_scope) != scope:
                raise ContractError(
                    "ROUTE_TRANSITION_SCOPE: attached graph cannot weaken the reviewed target policy"
                )
            moved = deepcopy(record)
            moved.update(
                id="transfer-"
                + digest_bytes(
                    canonical_json({"request": request_digest, "original": reference})
                )[:32],
                garden=destination["garden"],
                scope=scope,
            )
            moved[endpoint] = deepcopy(destination)
            moved["x-routing-transfer"] = {
                "from": reference,
                "request_sha256": request_digest,
                "preservation": "review-author-attribution-evidence-and-qualifications-retained",
            }
            content = canonical_json(moved)
            directory = "claims" if kind == "claim" else "synapses"
            files[directory + "/" + moved["id"] + ".json"] = content
            copied.append(
                artifact_reference(
                    destination["garden"], moved["id"], digest_bytes(content)
                )
            )
        knowledge[field] = copied
    files[path] = canonical_json(knowledge)
