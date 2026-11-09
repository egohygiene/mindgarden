"""Source-preservation reader for reread v2.0.0–2.0.2 archive specifications.

This verifies the supported source profile, not the producer's editorial,
knowledge-generation, delivery execution or safety-scan conformance.
"""

from ..domain.contracts import digest_bytes
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError
from ..domain.zip_package import member_path
from .archive_preservation import (
    normalize_assets,
    normalize_conversation,
    require_array,
    require_object,
    validate_references,
)

V2_VERSIONS = {"2.0.0", "2.0.1", "2.0.2"}
MANIFEST_FIELDS = set(
    "schema_version spec_version archive_id archive_revision created_at updated_at title "
    "unit_kind source_inputs source_scope capabilities options disabled_layers warnings "
    "classification coverage_detail counts provenance delivery".split()
)


def normalize_v2(documents, members, prefix, checksums, metadata, adapter_version):
    manifest = require_object(
        documents["ARCHIVE-MANIFEST.json"], MANIFEST_FIELDS, "ARCHIVE_MANIFEST"
    )
    version = manifest["spec_version"]
    if version not in V2_VERSIONS or (
        metadata.get("manifest_version") is not None
        and metadata["manifest_version"] != version
    ):
        raise ContractError(
            "ARCHIVE_VERSION: untested or mismatching v2 specification version"
        )
    archive_id = manifest["archive_id"]
    if (
        not isinstance(archive_id, str)
        or not archive_id
        or type(manifest["archive_revision"]) is not int
        or manifest["archive_revision"] < 1
        or manifest["unit_kind"]
        not in {"conversation", "fragment", "unthreaded-records"}
    ):
        raise ContractError("ARCHIVE_MANIFEST: invalid unit identity, kind or revision")
    for name in ("CONVERSATION.json", "VISUAL-INSIGHTS.md"):
        if not members.get(name):
            raise ContractError(
                "ARCHIVE_REQUIRED: v2 requires conversation and visual candidate index"
            )
    for key in (
        "source_scope",
        "capabilities",
        "options",
        "coverage_detail",
        "counts",
        "provenance",
    ):
        require_object(manifest[key], set(), "ARCHIVE_MANIFEST")
    require_object(
        manifest["classification"],
        {"value", "coverage", "readiness", "reasons"},
        "ARCHIVE_MANIFEST",
    )
    require_array(manifest["disabled_layers"], "ARCHIVE_MANIFEST")
    require_array(manifest["warnings"], "ARCHIVE_MANIFEST")
    options = manifest["options"]
    # The consumer retains these handoffs as source, never as applied knowledge.
    if options.get("mindgarden") != "off":
        if (
            not {
                "knowledge/KNOWLEDGE.json",
                "knowledge/INDEX.md",
                "mindgarden/IMPORT.json",
            }
            <= members.keys()
        ):
            raise ContractError(
                "ARCHIVE_REQUIRED: enabled knowledge handoff is missing; explicitly disable absent layers"
            )
    if options.get("visuals") != "off" and "pinterest/INDEX.json" not in members:
        raise ContractError(
            "ARCHIVE_REQUIRED: enabled visual handoff is missing; explicitly disable absent layers"
        )
    inputs = {}
    for item in require_array(manifest["source_inputs"], "ARCHIVE_INPUTS"):
        require_object(
            item,
            {
                "source_id",
                "provider",
                "product",
                "format",
                "capture_method",
                "locator",
                "archive_path",
                "byte_fidelity",
                "adapter",
                "adapter_version",
            },
            "ARCHIVE_INPUTS",
        )
        identity = item["source_id"]
        if not isinstance(identity, str) or not identity or identity in inputs:
            raise ContractError(
                "ARCHIVE_IDENTITY: source input identities must be explicit and unique"
            )
        if (
            item["archive_path"] is not None
            and member_path(item["archive_path"]) not in members
        ):
            raise ContractError("ARCHIVE_INPUTS: a declared captured input is missing")
        inputs[identity] = item
    delivery = require_object(
        manifest["delivery"], {"type", "status", "limitations"}, "ARCHIVE_DELIVERY"
    )
    if delivery["type"] != "zip":
        raise ContractError("ARCHIVE_DELIVERY: this adapter requires actual ZIP bytes")
    require_array(delivery["limitations"], "ARCHIVE_DELIVERY")
    for attempt in require_array(delivery.get("attempts", []), "ARCHIVE_DELIVERY"):
        require_object(
            attempt,
            {"path_id", "result", "error_class", "archive_created"},
            "ARCHIVE_DELIVERY",
        )
        if type(attempt["archive_created"]) is not bool:
            raise ContractError(
                "ARCHIVE_DELIVERY: packaging attempts need observed creation state"
            )
    for name in (
        "CONVERSATION.json",
        "ASSET-MANIFEST.json",
        "VALIDATION.json",
        "knowledge/KNOWLEDGE.json",
        "mindgarden/IMPORT.json",
    ):
        if name in documents:
            item = require_object(
                documents[name], {"schema_version", "archive_id"}, "ARCHIVE_CONTROL"
            )
            if item["schema_version"] != "2.0" or item["archive_id"] != archive_id:
                raise ContractError(
                    "ARCHIVE_CONTROL: preservation version or unit identity differs"
                )
    validation = require_object(
        documents["VALIDATION.json"],
        {
            "schema_version",
            "archive_id",
            "validated_at",
            "overall",
            "checks",
            "limitations",
        },
        "ARCHIVE_VALIDATION",
    )
    if validation["overall"] not in {"pass", "incomplete"}:
        raise ContractError(
            "ARCHIVE_VALIDATION: producer reports failed or unknown validation"
        )
    for check in require_array(validation["checks"], "ARCHIVE_VALIDATION"):
        require_object(
            check, {"id", "status", "method", "evidence", "notes"}, "ARCHIVE_VALIDATION"
        )
        if check["status"] not in {"pass", "not-run"}:
            raise ContractError(
                "ARCHIVE_VALIDATION: producer reports a failed or invalid check"
            )
    assets, units = normalize_assets(documents, members, prefix, archive_id, metadata)
    message_units, messages, records = normalize_conversation(
        documents, prefix, archive_id, inputs, assets, checksums
    )
    units.extend(message_units)
    validate_references(assets, messages, records)
    for name, kind in (
        ("CHAT-SUMMARY.md", "main-summary"),
        ("CONTINUATION.md", "continuation-state"),
    ):
        if name in members:
            units.append(
                NormalizedUnit(
                    "archive:" + archive_id + ":" + kind,
                    members[name],
                    "text/markdown",
                    metadata={
                        "archive_id": archive_id,
                        "evidence_kind": kind,
                        "summary_derived": True,
                        "original_selector": {
                            "member": prefix + name,
                            "sha256": digest_bytes(members[name]),
                        },
                    },
                )
            )
    if len(units) > 10000:
        raise ContractError(
            "ARCHIVE_LIMIT: normalized unit count exceeds the supported budget"
        )
    parameters = {
        "spec_version": version,
        "envelope_schema": "2.0",
        "preservation_schema": "2.0",
        "profile": "v2-source-preservation",
    }
    if "attachment_selection" in metadata:
        parameters["attachment_selection"] = metadata["attachment_selection"]
    return NormalizedBundle(
        tuple(units),
        (
            {
                "name": "normalize-conversation-archive",
                "version": adapter_version,
                "parameters": parameters,
            },
        ),
        {
            "archive_id": archive_id,
            "archive_revision": manifest["archive_revision"],
            "spec_version": version,
            "profile": "v2-source-preservation",
            "delivery": delivery,
            "coverage_detail": manifest["coverage_detail"],
            "producer_validation": validation["overall"],
            "adapter_validation": "package-integrity-and-evidence-structure",
            "full_producer_conformance": "not-claimed",
            "unmapped_metadata": [
                "source_scope",
                "counts",
                "provenance",
                "knowledge/visual/editorial/follow-up handoffs",
            ],
            "branches": documents["CONVERSATION.json"]["branches"],
            "primary_view": documents["CONVERSATION.json"]["primary_view"],
        },
    )
