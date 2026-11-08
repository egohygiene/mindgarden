"""Append-only canonical-home transitions carried by existing provenance records."""

from .contracts import ContractRegistry
from .validation import ContractError


def transition_event(record: dict) -> dict | None:
    event = record.get("x-routing-transition")
    if event is None:
        return None
    if (record.get("schema") != "mindgarden.provenance/v1"
            or ContractRegistry().errors(event, "routing-transition-event")
            or event["review"]["state"] != "approved" or event["authority"]["kind"] != "human"
            or event["authority"]["id"] not in event["review"]["reviewers"]
            or not event["review"]["rationale"] or event["from"] != record["artifact"]
            or event["from"]["garden"] != record["garden"]
            or event["from"]["revision"] != "sha256:" + record["artifact_sha256"]
            or not any(item["artifact"] == event["to"] for item in record["inputs"])):
        raise ContractError("ROUTE_TRANSITION_INVALID: canonical transitions require exact lineage and explicit human review")
    return event


def retired_references(records) -> dict[tuple[str, str], dict]:
    retired = {}
    for record in records:
        event = transition_event(record)
        if event is None:
            continue
        identity = (event["from"]["garden"], event["from"]["id"])
        if identity in retired and retired[identity] != event:
            raise ContractError("ROUTE_TRANSITION_CONFLICT: one represented unit has conflicting canonical transitions")
        retired[identity] = event
    finished = set()
    for identity in retired:
        visiting = set(); current = identity
        while current in retired and current not in finished:
            if current in visiting:
                raise ContractError("ROUTE_TRANSITION_CYCLE: canonical transitions must remain acyclic")
            visiting.add(current)
            target = retired[current]["to"]
            current = (target["garden"], target["id"])
        finished.update(visiting)
    return retired


def canonical_reference(reference: dict, records) -> dict:
    """Follow reviewed aliases; the caller separately authorizes target access."""
    transitions = retired_references(records)
    current = reference
    while (current["garden"], current["id"]) in transitions:
        event = transitions[(current["garden"], current["id"])]
        if current["revision"] != event["from"]["revision"]:
            raise ContractError("PLAN_STALE: alias requires the exact original represented revision")
        current = event["to"]
    return current
