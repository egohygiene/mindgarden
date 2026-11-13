"""Explicit local capture selection; credentials and locations are not evidence."""

from .contracts import ContractRegistry, canonical_json, digest_bytes
from .scope import local_scope
from .validation import ContractError

FOLDER = "application/vnd.google-apps.folder"
EXPORTS = {
    "application/vnd.google-apps.document": {"text/plain"},
    "application/vnd.google-apps.spreadsheet": {"text/csv"},
}


def validate_binding(binding):
    if ContractRegistry().errors(binding, "drive-binding"):
        raise ContractError("CAPTURE_INPUT: use the versioned explicit Drive binding")
    review, authority = binding["review"], binding["review_authority"]
    if (
        review["state"] != "approved"
        or authority["kind"] != "human"
        or authority["id"] not in review["reviewers"]
        or not review["rationale"]
    ):
        raise ContractError(
            "CAPTURE_REVIEW: approve the exact source selection and initial classification"
        )
    if binding["scope"] == local_scope(publication="never-exportable"):
        raise ContractError(
            "CAPTURE_EXECUTION: an offline scope cannot authorize provider acquisition"
        )
    if binding["scope"] != local_scope(
        execution="controlled-import", publication="never-exportable"
    ):
        raise ContractError(
            "CAPTURE_RUNTIME_UNVERIFIED: this checkpoint supports only explicitly reviewed ordinary personal capture"
        )
    mappings = {}
    if not binding["media_types"] and not binding["exports"]:
        raise ContractError(
            "CAPTURE_FORMAT: select at least one supported media or native export type"
        )
    for item in binding["exports"]:
        if item["source_type"] in mappings or item["export_type"] not in EXPORTS.get(
            item["source_type"], set()
        ):
            raise ContractError(
                "CAPTURE_FORMAT: select a documented supported native export once"
            )
        mappings[item["source_type"]] = item["export_type"]
    return binding


def binding_digest(binding):
    return digest_bytes(canonical_json(validate_binding(binding)))


def export_type(binding, item):
    source_type = item["mimeType"]
    mapping = {
        value["source_type"]: value["export_type"] for value in binding["exports"]
    }
    if source_type in mapping:
        return mapping[source_type]
    return source_type if source_type in binding["media_types"] else None
