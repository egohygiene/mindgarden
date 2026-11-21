"""Summarize verified local source lineage without probing providers."""

from ..adapters.drive_source import DriveCaptureAdapter
from ..domain.contracts import canonical_json, digest_bytes
from ..domain.sources import normalize_source
from ..domain.validation import ContractError


DRIVE_PROVIDER = "google-drive-v3"


def _scoped_record(snapshots, reference, schema):
    owner = snapshots.get(reference["garden"])
    record = owner.records.get(reference["id"]) if owner is not None else None
    if record is None or record["schema"] != schema:
        return None
    return owner, record


def _adapter_metadata(record, adapter):
    declaration = record.get("x-adapter")
    if (isinstance(declaration, dict) and declaration.get("id") == adapter.adapter_id
            and declaration.get("version") == adapter.version
            and any(version == declaration.get("manifest_version") for _, version in adapter.supported_inputs)
            and isinstance(declaration.get("metadata"), dict)):
        return declaration["metadata"]
    return None


def _capture_units(adapter, capture, content, mapping):
    declared = _adapter_metadata(capture, adapter)
    if (capture["kind"] != "captured" or declared is None or declared.get("provider") != DRIVE_PROVIDER
            or (capture["media_type"], capture["x-adapter"]["manifest_version"]) not in adapter.supported_inputs):
        return {}
    metadata = {"source_scope": declared.get("captured_scope")}
    if mapping is not None:
        metadata["drive_normalization"] = mapping
    try:
        bundle = normalize_source(adapter, content, metadata)
    except ContractError:
        return {}
    return {unit.identity: (unit.media_type, digest_bytes(unit.content), unit.metadata) for unit in bundle.units}


def _verified_drive_source(snapshots, source, adapter, replayed):
    declared = _adapter_metadata(source, adapter)
    if source["kind"] != "normalized" or declared is None or len(source["inputs"]) != 1:
        return False
    reference = source["inputs"][0]
    target = _scoped_record(snapshots, reference, "mindgarden.source/v1")
    if target is None:
        return False
    owner, capture = target
    content = owner.contents.get(capture["id"])
    digest = owner.hashes.get(capture["id"])
    if content is None or digest is None or reference.get("revision") != "sha256:" + digest:
        return False
    # The normalized artifact owns the chosen mapping. A newer mapping may have
    # been applied to the same immutable capture without rewriting its metadata.
    for provenance_ref in source["provenance"]:
        target = _scoped_record(snapshots, provenance_ref, "mindgarden.provenance/v1")
        if target is None:
            continue
        _, provenance = target
        if not any(item["role"] == "source" and item["artifact"] == reference for item in provenance["inputs"]):
            continue
        mapping = next((item["parameters"].get("configuration") for item in provenance["transformations"]
                        if item["name"] == "reviewed-drive-normalization"), None)
        key = (reference["garden"], reference["id"], digest_bytes(canonical_json(mapping)))
        if key not in replayed:
            replayed[key] = _capture_units(adapter, capture, content, mapping)
        identity = source.get("x-source-identity")
        signature = (source["media_type"], source["artifact"]["sha256"], declared)
        if isinstance(identity, str) and replayed[key].get(identity) == signature:
            return True
    return False


def connector_evidence(context, reviewed_records, *, demo):
    """Count distinct citations from the caller's bounded reviewed index view."""
    citations = {canonical_json(item): item for record in reviewed_records for item in record["sources"]}
    drive_count = vault_count = 0
    if citations:
        snapshots = context.snapshots()
        adapter = DriveCaptureAdapter()
        replayed = {}
        drive_sources = {}
        for citation in citations.values():
            reference = citation["source"]
            key = reference["garden"], reference["id"]
            target = _scoped_record(snapshots, reference, "mindgarden.source/v1")
            if target is None:
                continue
            owner, source = target
            if source["id"] not in owner.contents:
                continue
            if "vault" in source["artifact"]:
                vault_count += 1
            if key not in drive_sources:
                drive_sources[key] = _verified_drive_source(snapshots, source, adapter, replayed)
            if drive_sources[key]:
                drive_count += 1
    return {
        "google_drive": {
            "state": "demo" if demo else "captured" if drive_count else "setup-required",
            "citation_count": drive_count,
        },
        "local_vault": {
            "state": "visible-evidence" if vault_count else "no-visible-evidence",
            "citation_count": vault_count,
        },
    }
