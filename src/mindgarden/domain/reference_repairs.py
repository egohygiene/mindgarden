"""Exact reviewed reference replacements; historical relationship bytes survive."""

from .contracts import ContractRegistry, canonical_json, digest_bytes
from .routing_transitions import retired_references
from .validation import ContractError


def repair_pointer(record):
    reference = record.get("x-reference-repair-event")
    if reference is None:
        return None
    if (
        not isinstance(reference, dict)
        or set(reference) != {"garden", "id", "revision"}
        or reference["garden"] != record["garden"]
        or not isinstance(reference["id"], str)
        or not reference["id"]
        or reference["revision"] is not None
    ):
        raise ContractError("ROUTE_REPAIR_INVALID: malformed private repair pointer")
    return reference


def repair_event(record):
    event = record.get("x-reference-repair")
    if event is None:
        return None
    if (
        record.get("schema") != "mindgarden.provenance/v1"
        or ContractRegistry().errors(event, "reference-repair-event")
        or event["review"]["state"] != "approved"
        or event["authority"]["id"] not in event["review"]["reviewers"]
        or not event["review"]["rationale"]
        or record["artifact"] != event["replacement"]
        or event["replacement"]["garden"] != record["garden"]
        or event["replacement"]["revision"] != "sha256:" + record["artifact_sha256"]
        or not all(
            reference.get("revision") is not None
            for reference in (
                event["original"],
                event["replacement"],
                event["source"],
                event["historical_target"],
                event["canonical_target"],
            )
        )
        or not all(
            any(item["artifact"] == reference for item in record["inputs"])
            for reference in (
                event["original"],
                event["source"],
                event["historical_target"],
                event["canonical_target"],
            )
        )
    ):
        raise ContractError(
            "ROUTE_REPAIR_INVALID: repair needs exact lineage and human review"
        )
    return event


def verify_repair(record, records):
    """Verify already authorized metadata without opening source bodies."""
    event = repair_event(record)
    if event is None:
        return None

    def resolve(reference, schema):
        item = records.get((reference["garden"], reference["id"]))
        if item is None or item["schema"] != "mindgarden." + schema + "/v1":
            raise ContractError(
                "ROUTE_REPAIR_INVALID: exact repair dependency is unavailable"
            )
        represented = item.get("content", {}).get("sha256") or digest_bytes(
            canonical_json(item)
        )
        if reference["revision"] != "sha256:" + represented:
            raise ContractError(
                "ROUTE_REPAIR_INVALID: represented repair dependency changed"
            )
        return item

    old = resolve(event["original"], "synapse")
    new = resolve(event["replacement"], "synapse")
    for reference in (
        event["source"],
        event["historical_target"],
        event["canonical_target"],
    ):
        resolve(reference, "knowledge")
    stable = set(old) | set(new)
    stable -= {
        "id",
        "target",
        "review",
        "x-reference-repair-event",
        "x-repair-rationale",
    }
    if (
        any(old.get(field) != new.get(field) for field in stable)
        or old["source"] != event["source"]
        or old["target"] != event["historical_target"]
        or new["target"] != event["canonical_target"]
        or new["review"] != event["review"]
        or new.get("x-repair-rationale") != event["rationale"]
        or repair_pointer(new)
        != {"garden": record["garden"], "id": record["id"], "revision": None}
        or event["historical_target"] == event["canonical_target"]
        or not reviewed_successor(
            event["historical_target"], event["canonical_target"], records.values()
        )
    ):
        raise ContractError(
            "ROUTE_REPAIR_INVALID: repair must preserve the reviewed relationship and exact successor"
        )
    return event


def reviewed_successor(original, expected, records):
    """Historical repair remains valid when its represented successor moves later."""
    transitions = retired_references(records)
    current = original
    while current != expected:
        transition = transitions.get((current["garden"], current["id"]))
        if transition is None or current != transition["from"]:
            return False
        current = transition["to"]
    return True


def repair_history(records):
    result = {}
    for record in records:
        event = repair_event(record)
        if event is None:
            continue
        identity = event["original"]["garden"], event["original"]["id"]
        if identity in result and result[identity] != event:
            raise ContractError(
                "ROUTE_REPAIR_CONFLICT: relationship already has another reviewed repair"
            )
        result[identity] = event
    return result
