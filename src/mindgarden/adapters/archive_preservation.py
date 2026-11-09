"""Shared preservation-schema 2.0 evidence checks, independent of envelope version."""

from datetime import datetime
from urllib.parse import urlsplit

from ..domain.contracts import canonical_json, digest_bytes
from ..domain.sources import NormalizedUnit
from ..domain.validation import ContractError
from ..domain.zip_package import member_path
from .archive_selection import attachment_selection

MESSAGE_FIELDS = set(
    "id source_id source_message_id source_locator index role role_raw timestamp timestamp_raw "
    "parent_ids relationship_status branch_id content asset_ids citations fidelity "
    "transformations provider_metadata".split()
)
ASSET_FIELDS = set(
    "id original_names kind provenance source_refs status archive_path byte_fidelity "
    "derived_from_asset_id bytes sha256 mime_type dimensions page_count duration_seconds "
    "source_locator retrieved_at revision_label rights_status rights_evidence sensitivity "
    "inspection_status missing_reason recovery_action notes".split()
)


def require_object(value: object, fields: set[str], code: str) -> dict:
    if not isinstance(value, dict) or not fields <= value.keys():
        raise ContractError(
            code + ": required structural fields are missing or malformed"
        )
    return value


def require_array(value: object, code: str) -> list:
    if not isinstance(value, list) or len(value) > 10000:
        raise ContractError(code + ": expected a bounded record array")
    return value


def unique_records(value: object, code: str) -> dict[str, dict]:
    result = {}
    for item in require_array(value, code):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not item["id"]
        ):
            raise ContractError(code + ": records require explicit identities")
        if item["id"] in result:
            raise ContractError("ARCHIVE_IDENTITY: duplicate typed record identity")
        result[item["id"]] = item
    return result


def normalize_assets(documents, members, prefix, archive_id, metadata):
    asset_manifest = require_object(
        documents["ASSET-MANIFEST.json"],
        {"schema_version", "archive_id", "assets", "warnings"},
        "ARCHIVE_ASSETS",
    )
    assets = unique_records(asset_manifest["assets"], "ARCHIVE_ASSETS")
    selection_mode, selected_assets = attachment_selection(metadata, set(assets))
    units: list[NormalizedUnit] = []
    for asset_id, asset in assets.items():
        require_object(asset, ASSET_FIELDS, "ARCHIVE_ASSETS")
        if asset["sensitivity"] == "restricted":
            raise ContractError(
                "ARCHIVE_SCOPE: restricted attachments require an unavailable encrypted storage adapter"
            )
        if asset["status"] not in {
            "archived",
            "preview-only",
            "external-only",
            "missing",
            "excluded",
            "failed",
            "unreviewed",
        }:
            raise ContractError("ARCHIVE_ASSETS: unknown attachment state")
        path = asset["archive_path"]
        if (
            asset["derived_from_asset_id"] is not None
            and asset["derived_from_asset_id"] not in assets
        ):
            raise ContractError(
                "ARCHIVE_REFERENCE: original attachment identity does not resolve"
            )
        if path is None:
            if asset["status"] == "archived" or not asset["missing_reason"]:
                raise ContractError(
                    "ARCHIVE_ASSETS: missing attachment bytes need an explicit reason"
                )
            content, media_type = canonical_json(asset), "application/json"
            original_selector = {
                "member": prefix + "ASSET-MANIFEST.json",
                "asset_id": asset_id,
            }
        else:
            path = member_path(path)
            if (
                path not in members
                or type(asset["bytes"]) is not int
                or asset["bytes"] != len(members[path])
                or asset["sha256"] != digest_bytes(members[path])
            ):
                raise ContractError(
                    "ARCHIVE_ASSETS: attachment bytes, path or checksum differ"
                )
            content, media_type = members[path], asset["mime_type"]
            original_selector = {
                "member": prefix + path,
                "sha256": digest_bytes(content),
            }
        catalog_only = asset_id not in selected_assets and path is not None
        if catalog_only:
            content, media_type = canonical_json(asset), "application/json"
            original_selector = {
                "member": prefix + "ASSET-MANIFEST.json",
                "asset_id": asset_id,
            }
        units.append(
            NormalizedUnit(
                "archive:"
                + archive_id
                + (":asset-catalog:" if catalog_only else ":asset:")
                + asset_id,
                content,
                media_type,
                metadata={
                    "archive_id": archive_id,
                    "asset_id": asset_id,
                    "asset_status": asset["status"],
                    "asset": asset,
                    "original_selector": original_selector,
                    "evidence_kind": "asset-bytes"
                    if path and not catalog_only
                    else "asset-catalog",
                },
            )
        )
    return assets, units


def normalize_conversation(documents, prefix, archive_id, inputs, assets, checksums):
    units = []
    conversation = require_object(
        documents["CONVERSATION.json"],
        {
            "schema_version",
            "archive_id",
            "provider",
            "coverage",
            "messages",
            "source_records",
            "branches",
            "primary_view",
            "warnings",
        },
        "ARCHIVE_CONVERSATION",
    )
    messages = unique_records(conversation["messages"], "ARCHIVE_MESSAGES")
    records = unique_records(conversation["source_records"], "ARCHIVE_RECORDS")
    branches = unique_records(conversation["branches"], "ARCHIVE_BRANCHES")
    input_ids = set(inputs)
    for order, message in enumerate(conversation["messages"]):
        require_object(message, MESSAGE_FIELDS, "ARCHIVE_MESSAGES")
        if (
            message["source_id"] not in input_ids
            or type(message["index"]) is not int
            or message["index"] < 1
            or message["role"] not in {"user", "assistant", "tool", "unknown"}
            or message["relationship_status"]
            not in {"observed", "linear-source", "unknown"}
            or message["fidelity"] not in {"verbatim", "normalized", "ocr", "redacted"}
        ):
            raise ContractError(
                "ARCHIVE_MESSAGES: message attribution or source relationship is invalid"
            )
        if any(
            value not in messages
            for value in require_array(message["parent_ids"], "ARCHIVE_MESSAGES")
        ):
            raise ContractError("ARCHIVE_REFERENCE: parent message does not resolve")
        if message["branch_id"] is not None and message["branch_id"] not in branches:
            raise ContractError("ARCHIVE_REFERENCE: branch identity does not resolve")
        if any(
            value not in assets
            for value in require_array(message["asset_ids"], "ARCHIVE_MESSAGES")
        ):
            raise ContractError(
                "ARCHIVE_REFERENCE: attachment identity does not resolve"
            )
        if message["timestamp"] is not None:
            try:
                if (
                    datetime.fromisoformat(
                        message["timestamp"].replace("Z", "+00:00")
                    ).tzinfo
                    is None
                ):
                    raise ValueError()
            except (ValueError, TypeError, AttributeError) as error:
                raise ContractError(
                    "ARCHIVE_TIME: source timestamp needs an observed offset"
                ) from error
        locators = []
        for index, block in enumerate(
            require_array(message["content"], "ARCHIVE_BLOCK")
        ):
            if not isinstance(block, dict) or block.get("type") not in {
                "text",
                "code",
                "table",
                "math",
                "image",
                "audio",
                "video",
                "file",
                "link",
                "unknown",
            }:
                raise ContractError("ARCHIVE_BLOCK: unsupported content-bearing block")
            if "asset_id" in block and block["asset_id"] not in assets:
                raise ContractError(
                    "ARCHIVE_REFERENCE: content attachment does not resolve"
                )
            if "text" in block:
                if not isinstance(block["text"], str):
                    raise ContractError("ARCHIVE_BLOCK: text block is malformed")
                locators.append(f"json:/content/{index}/text")
            if block["type"] in {"text", "code"} and not isinstance(
                block.get("text"), str
            ):
                raise ContractError(
                    "ARCHIVE_BLOCK: text/code blocks require retained text"
                )
            if block["type"] == "code" and "language" not in block:
                raise ContractError(
                    "ARCHIVE_BLOCK: code language must be observed or explicitly null"
                )
            if (
                block["type"] == "link"
                and "url" not in block
                and "unavailable_reason" not in block
            ):
                raise ContractError(
                    "ARCHIVE_BLOCK: link needs a locator or explicit unavailable marker"
                )
        for citation in require_array(message["citations"], "ARCHIVE_CITATION"):
            require_object(
                citation,
                {
                    "label",
                    "url",
                    "title",
                    "source_refs",
                    "retrieval_status",
                    "verification_status",
                },
                "ARCHIVE_CITATION",
            )
            if citation["retrieval_status"] not in {
                "not-retrieved",
                "retrieved",
                "unavailable",
            } or citation["verification_status"] not in {
                "not-checked",
                "checked-in-source",
                "needs-verification",
                "not-applicable",
            }:
                raise ContractError(
                    "ARCHIVE_CITATION: citation retrieval/verification state is invalid"
                )
            if citation["url"] is not None and urlsplit(citation["url"]).scheme not in {
                "https",
                "http",
                "urn",
            }:
                raise ContractError("ARCHIVE_CITATION: active or unsafe citation URL")
        units.append(
            NormalizedUnit(
                "archive:" + archive_id + ":message:" + message["id"],
                canonical_json(message),
                "application/json",
                tuple(locators) or ("artifact",),
                {
                    "archive_id": archive_id,
                    "message_id": message["id"],
                    "speaker": message["role"],
                    "source_message_id": message["source_message_id"],
                    "timestamp": message["timestamp"],
                    "branch_id": message["branch_id"],
                    "summary_derived": False,
                    "source_order": order,
                    "original_selector": {
                        "member": prefix + "CONVERSATION.json",
                        "json_pointer": f"/messages/{order}",
                        "member_sha256": checksums["CONVERSATION.json"],
                    },
                },
            )
        )
    for order, record in enumerate(conversation["source_records"]):
        require_object(
            record,
            {
                "id",
                "source_id",
                "kind",
                "source_locator",
                "timestamp",
                "content",
                "fidelity",
                "warnings",
            },
            "ARCHIVE_RECORDS",
        )
        if record["source_id"] not in input_ids or record["kind"] not in {
            "summary",
            "activity",
            "artifact-text",
            "unparsed",
        }:
            raise ContractError(
                "ARCHIVE_RECORDS: unsupported source-record identity or kind"
            )
        units.append(
            NormalizedUnit(
                "archive:" + archive_id + ":record:" + record["id"],
                canonical_json(record),
                "application/json",
                metadata={
                    "summary_derived": record["kind"] == "summary",
                    "record_id": record["id"],
                    "original_selector": {
                        "member": prefix + "CONVERSATION.json",
                        "json_pointer": f"/source_records/{order}",
                    },
                },
            )
        )
    for branch in branches.values():
        require_object(
            branch,
            {"id", "source_branch_id", "message_ids", "selection_status", "evidence"},
            "ARCHIVE_BRANCHES",
        )
        if branch["selection_status"] not in {
            "selected",
            "alternative",
            "unknown",
        } or any(
            value not in messages
            for value in require_array(branch["message_ids"], "ARCHIVE_BRANCHES")
        ):
            raise ContractError("ARCHIVE_REFERENCE: branch message does not resolve")
    view = require_object(
        conversation["primary_view"], {"message_ids", "ordering_basis"}, "ARCHIVE_VIEW"
    )
    if view["ordering_basis"] not in {
        "source-order",
        "parent-graph",
        "timestamp",
        "unknown",
    } or any(
        value not in messages
        for value in require_array(view["message_ids"], "ARCHIVE_VIEW")
    ):
        raise ContractError("ARCHIVE_REFERENCE: reading-view message does not resolve")
    return units, messages, records


def validate_references(assets, messages, records):
    reference_targets = {"message": messages, "record": records, "asset": assets}
    reference_groups = [asset["source_refs"] for asset in assets.values()]
    reference_groups += [
        citation["source_refs"]
        for message in messages.values()
        for citation in message["citations"]
    ]
    for group in reference_groups:
        for reference in require_array(group, "ARCHIVE_REFERENCE"):
            require_object(reference, {"kind", "id", "locator"}, "ARCHIVE_REFERENCE")
            if (
                reference["kind"] not in reference_targets
                or reference["id"] not in reference_targets[reference["kind"]]
            ):
                raise ContractError(
                    "ARCHIVE_REFERENCE: typed evidence reference does not resolve inside this unit"
                )
