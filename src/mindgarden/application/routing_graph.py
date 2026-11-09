"""Exact outgoing graph copies for reviewed private moves; originals are retained."""

from copy import deepcopy

from ..domain.contracts import canonical_json, digest_bytes, strict_json
from ..domain.scope import record_scope
from ..domain.validation import ContractError
from .records import artifact_reference


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
