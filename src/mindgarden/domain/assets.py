"""Append-only human asset review; selection state is never deletion authority."""

from .contracts import ContractRegistry, canonical_json, digest_bytes
from .validation import ContractError


def asset_review(record: dict) -> dict | None:
    event = record.get("x-asset-review")
    if event is None: return None
    if (record.get("schema") != "mindgarden.provenance/v1"
            or ContractRegistry().errors(event, "asset-review")
            or event["authority"]["id"] not in event["review"]["reviewers"]
            or event["source"] != record["artifact"]
            or event["source"]["garden"] != record["garden"]
            or event["source"]["revision"] != "sha256:" + record["artifact_sha256"]
            or event["content_id"] != "sha256:" + record["artifact_sha256"]
            or event["copy_policy"] != "reference-only" or event["state"] == "restricted"
            or event["previous"] is not None and not any(item["artifact"] == event["previous"]
                                                       and item["role"] == "previous-version" for item in record["inputs"])):
        raise ContractError("ASSET_REVIEW_INVALID: asset review requires exact human authority and retained source lineage")
    return event


def asset_review_heads(records) -> dict[str, dict]:
    events = {}
    for record in records:
        event = asset_review(record)
        if event is not None: events[(record["garden"], record["id"])] = (record, event)
    successors, groups = {}, {}
    for identity, (record, event) in events.items():
        content_id = event["content_id"]; groups.setdefault(content_id, set()).add(identity)
        previous = event["previous"]
        if previous is None: previous_key = (content_id, None)
        else:
            previous_key = (previous["garden"], previous["id"])
            prior = events.get(previous_key)
            if (prior is None or prior[1]["content_id"] != content_id
                    or previous["revision"] != "sha256:" + digest_bytes(canonical_json(prior[0]))):
                raise ContractError("ASSET_REVIEW_INVALID: previous review evidence is unavailable or changed")
        if previous_key in successors:
            raise ContractError("ASSET_REVIEW_CONFLICT: review history forks; retain every event for explicit recovery")
        successors[previous_key] = identity
    heads = {}
    for content_id, identities in groups.items():
        roots = [identity for identity in identities if events[identity][1]["previous"] is None]
        tips = identities - successors.keys()
        if len(roots) != 1 or len(tips) != 1:
            raise ContractError("ASSET_REVIEW_CONFLICT: review history is cyclic or ambiguous")
        seen, current = set(), roots[0]
        while current is not None:
            if current in seen: raise ContractError("ASSET_REVIEW_CONFLICT: review history is cyclic")
            seen.add(current); current = successors.get(current)
        if seen != identities: raise ContractError("ASSET_REVIEW_CONFLICT: review history is disconnected")
        heads[content_id] = events[next(iter(tips))][0]
    return heads
