"""Exact reviewed selections shared by derived learning and publishing plans."""

from copy import deepcopy

from ..domain.contracts import canonical_json, digest_bytes
from ..domain.validation import ContractError
from .retrieval import build_index, record_key


def selection_view(context):
    index = build_index(context, projection="context")
    snapshots = context.snapshots()
    return index, snapshots


def select_records(index, snapshots, references):
    available = {record_key(record["reference"]): record for record in index["records"]}
    selected = []
    seen = set()
    for reference in references:
        key = record_key(reference)
        record = available.get(key)
        if (
            key in seen
            or record is None
            or record["reference"] != reference
            or not record["sources"]
        ):
            raise ContractError(
                "SELECTION_UNAVAILABLE: exact reviewed records and verified evidence are required"
            )
        seen.add(key)
        item = deepcopy(record)
        original = snapshots[reference["garden"]].records[reference["id"]]
        if original["schema"] == "mindgarden.claim/v1":
            item["qualifications"]["epistemic_state"] = original["epistemic_state"]
            item["claim_relationships"] = sorted(
                {edge["relationship"] for edge in original["evidence"]}
            )
        else:
            item["claim_relationships"] = []
        selected.append(item)
    return sorted(selected, key=lambda record: record_key(record["reference"]))


def source_trail(records):
    return [
        {
            "reference": record["reference"],
            "scope": record["scope"],
            "review": record["review"],
            "confidence": record["confidence"],
            "evidence": record["sources"],
            "qualifications": record["qualifications"],
            "claim_relationships": record["claim_relationships"],
        }
        for record in records
    ]


def qualification_reasons(records):
    reasons = set()
    for record in records:
        qualifications = record["qualifications"]
        if record["confidence"] in {"low", "unknown"}:
            reasons.add("source-confidence")
        if qualifications["epistemic_state"] not in {"observed", "decided"}:
            reasons.add("source-epistemic-state")
        if qualifications["uncertainty"] or qualifications["caveats"]:
            reasons.add("source-uncertainty")
        if (
            qualifications["contradictions"]
            or "contradicts" in record["claim_relationships"]
        ):
            reasons.add("contradictory-source")
        if "uncertain" in record["claim_relationships"]:
            reasons.add("uncertain-support")
    return sorted(reasons)


def selected_digest(records):
    return digest_bytes(canonical_json(records))
