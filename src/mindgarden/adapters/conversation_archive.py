"""Tested single-unit v3.2.2/v3.2.3 evidence normalization, not a producer workflow."""

from __future__ import annotations

from datetime import datetime
import re
from urllib.parse import urlsplit

from ..domain.contracts import canonical_json, digest_bytes, strict_json
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError
from ..domain.zip_package import member_path, read_zip, verify_inventory
from .archive_selection import attachment_selection

VERSIONS = {"3.2.2", "3.2.3"}
BASE_FILES = {"README.md", "CHAT-SUMMARY.md", "ARCHIVE-MANIFEST.json", "ASSET-MANIFEST.json",
              "EXTRACTION-REPORT.md", "VALIDATION.json", "MANIFEST.sha256"}
MANIFEST_FIELDS = set("schema_version spec_version archive_id archive_revision created_at updated_at title "
                      "unit_kind source_inputs source_scope capabilities options disabled_layers warnings "
                      "content_mode package_profile transcript_preserved summary_paths compression "
                      "layer_status schema_registry routing execution freeze classification coverage_detail "
                      "counts provenance delivery".split())
MESSAGE_FIELDS = set("id source_id source_message_id source_locator index role role_raw timestamp timestamp_raw "
                     "parent_ids relationship_status branch_id content asset_ids citations fidelity "
                     "transformations provider_metadata".split())
ASSET_FIELDS = set("id original_names kind provenance source_refs status archive_path byte_fidelity "
                   "derived_from_asset_id bytes sha256 mime_type dimensions page_count duration_seconds "
                   "source_locator retrieved_at revision_label rights_status rights_evidence sensitivity "
                   "inspection_status missing_reason recovery_action notes".split())


def require_object(value: object, fields: set[str], code: str) -> dict:
    if not isinstance(value, dict) or not fields <= value.keys():
        raise ContractError(code + ": required structural fields are missing or malformed")
    return value


def require_array(value: object, code: str) -> list:
    if not isinstance(value, list) or len(value) > 10000:
        raise ContractError(code + ": expected a bounded record array")
    return value


def unique_records(value: object, code: str) -> dict[str, dict]:
    result = {}
    for item in require_array(value, code):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ContractError(code + ": records require explicit identities")
        if item["id"] in result:
            raise ContractError("ARCHIVE_IDENTITY: duplicate typed record identity")
        result[item["id"]] = item
    return result


class ConversationArchiveAdapter:
    adapter_id = "conversation-archive"
    version = "1.1.0"
    supported_inputs = frozenset(("application/zip", version) for version in VERSIONS)

    def normalize(self, captured: bytes, metadata: dict) -> NormalizedBundle:
        try:
            return self._normalize(captured, metadata)
        except ContractError:
            raise
        except (KeyError, TypeError, ValueError, UnicodeError, AttributeError, RecursionError) as error:
            raise ContractError("ARCHIVE_STRUCTURE: malformed package controls; no source was applied") from error

    def _normalize(self, captured: bytes, metadata: dict) -> NormalizedBundle:
        packaged = read_zip(captured)
        manifests = [name for name in packaged if name == "ARCHIVE-MANIFEST.json"
                     or name.endswith("/ARCHIVE-MANIFEST.json")]
        if len(manifests) != 1 or any(name.endswith("COLLECTION.json") for name in packaged):
            raise ContractError("ARCHIVE_UNSUPPORTED: select one supported archive unit; collections are not tested")
        prefix = manifests[0].removesuffix("ARCHIVE-MANIFEST.json")
        if any(not name.startswith(prefix) for name in packaged):
            raise ContractError("ARCHIVE_MEMBERS: files outside the selected archive unit")
        members = {name[len(prefix):]: content for name, content in packaged.items()}
        if not BASE_FILES <= members.keys() or any(not members[name] for name in BASE_FILES):
            raise ContractError("ARCHIVE_REQUIRED: required nonempty package controls are missing")
        checksums = verify_inventory(members)
        controls = {"ARCHIVE-MANIFEST.json", "ASSET-MANIFEST.json", "VALIDATION.json", "CONVERSATION.json",
                    "SUMMARY-TRAIL.json", "routing/PLAN.json", "creative/INDEX.json", "knowledge/KNOWLEDGE.json",
                    "mindgarden/IMPORT.json"}
        documents = {name: strict_json(content) for name, content in members.items() if name in controls}
        manifest = require_object(documents["ARCHIVE-MANIFEST.json"], MANIFEST_FIELDS, "ARCHIVE_MANIFEST")
        version = manifest["spec_version"]
        if manifest["schema_version"] != "3.2" or version not in VERSIONS:
            raise ContractError("ARCHIVE_VERSION: untested envelope/specification version")
        if metadata.get("manifest_version") is not None and version != metadata["manifest_version"]:
            raise ContractError("ARCHIVE_VERSION: declared and observed specification versions differ")
        archive_id = manifest["archive_id"]
        if (not isinstance(archive_id, str) or not archive_id
                or type(manifest["archive_revision"]) is not int or manifest["archive_revision"] < 1
                or manifest["unit_kind"] not in {"conversation", "fragment", "unthreaded-records"}):
            raise ContractError("ARCHIVE_MANIFEST: invalid unit identity or revision")
        profiles = {("full-source", "full-source", True), ("compact", "summary-journey", False)}
        if (manifest["content_mode"], manifest["package_profile"], manifest["transcript_preserved"]) not in profiles:
            raise ContractError("ARCHIVE_PROFILE: content mode, profile and transcript state disagree")
        inputs = {}
        for item in require_array(manifest["source_inputs"], "ARCHIVE_INPUTS"):
            require_object(item, {"source_id", "provider", "product", "format", "capture_method", "locator",
                                  "archive_path", "byte_fidelity", "adapter", "adapter_version"}, "ARCHIVE_INPUTS")
            identity = item["source_id"]
            if not isinstance(identity, str) or not identity or identity in inputs:
                raise ContractError("ARCHIVE_IDENTITY: source input identities must be explicit and unique")
            if item["archive_path"] is not None and member_path(item["archive_path"]) not in members:
                raise ContractError("ARCHIVE_INPUTS: a declared captured input is missing")
            inputs[identity] = item
        compression = require_object(manifest["compression"], {
            "strategy", "generated_word_limit", "generated_words_at_freeze", "reserved_post_freeze_words",
            "count_method", "checkpoint_limit", "checkpoint_count", "context_pressure", "omitted_categories",
            "predecessor_refs", "limitations"}, "ARCHIVE_COMPRESSION")
        expected_strategy = "summary-and-journey" if manifest["content_mode"] == "compact" else "full-source-with-summary"
        if compression["strategy"] != expected_strategy or compression["count_method"] not in {"measured-whitespace", "estimated"}:
            raise ContractError("ARCHIVE_COMPRESSION: profile and declared summary strategy disagree")
        for key in ("generated_word_limit", "checkpoint_limit"):
            if type(compression[key]) is not int or compression[key] < 1:
                raise ContractError("ARCHIVE_COMPRESSION: limits must be positive integers")
        for key in ("generated_words_at_freeze", "reserved_post_freeze_words", "checkpoint_count"):
            if compression[key] is None:
                if not compression["limitations"]:
                    raise ContractError("ARCHIVE_COMPRESSION: unknown counts need a limitation")
            elif type(compression[key]) is not int or compression[key] < 0:
                raise ContractError("ARCHIVE_COMPRESSION: counts must be nonnegative integers or explicitly unknown")
        execution = require_object(manifest["execution"], {"order", "routing_scope", "source_capture_id", "fallback_reason"},
                                   "ARCHIVE_EXECUTION")
        if execution["order"] not in {"route-before-package", "preserve-existing-before-route", "preserve-first-fallback", "extract-only"}:
            raise ContractError("ARCHIVE_EXECUTION: unknown producer execution order")
        delivery = require_object(manifest["delivery"], {"type", "status", "limitations"}, "ARCHIVE_DELIVERY")
        if delivery["type"] != "zip":
            raise ContractError("ARCHIVE_DELIVERY: this adapter consumes actual ZIP artifacts")
        for attempt in require_array(delivery.get("attempts", []), "ARCHIVE_DELIVERY"):
            require_object(attempt, {"path_id", "result", "error_class", "archive_created"}, "ARCHIVE_DELIVERY")
            if type(attempt["archive_created"]) is not bool:
                raise ContractError("ARCHIVE_DELIVERY: packaging attempts require observed creation state")
        summary_paths = require_object(manifest["summary_paths"], {"main", "journey", "machine_trail", "continuation"},
                                       "ARCHIVE_SUMMARY")
        if summary_paths["main"] != "CHAT-SUMMARY.md":
            raise ContractError("ARCHIVE_SUMMARY: main summary path is incompatible")
        for value in summary_paths.values():
            if value is not None and (not isinstance(value, str) or member_path(value) not in members):
                raise ContractError("ARCHIVE_SUMMARY: a declared summary artifact is missing")
        for name, expected in (("ASSET-MANIFEST.json", "2.0"), ("VALIDATION.json", "2.0"),
                               ("CONVERSATION.json", "2.0"), ("SUMMARY-TRAIL.json", "3.2"),
                               ("routing/PLAN.json", "3.0"), ("creative/INDEX.json", "3.0"),
                               ("knowledge/KNOWLEDGE.json", "2.0"), ("mindgarden/IMPORT.json", "2.0")):
            if name in documents:
                item = require_object(documents[name], {"schema_version", "archive_id"}, "ARCHIVE_CONTROL")
                if item["schema_version"] != expected or item["archive_id"] != archive_id:
                    raise ContractError("ARCHIVE_CONTROL: declared control version or unit identity differs")
        validation = require_object(documents["VALIDATION.json"],
                                    {"schema_version", "archive_id", "validated_at", "overall", "checks", "limitations"},
                                    "ARCHIVE_VALIDATION")
        if validation["overall"] not in {"pass", "incomplete"}:
            raise ContractError("ARCHIVE_VALIDATION: producer reports failed or unknown validation")
        for check in require_array(validation["checks"], "ARCHIVE_VALIDATION"):
            require_object(check, {"id", "status", "method", "evidence", "notes"}, "ARCHIVE_VALIDATION")
            if check["status"] not in {"pass", "not-run"}:
                raise ContractError("ARCHIVE_VALIDATION: producer reports a failed or invalid check")
        asset_manifest = require_object(documents["ASSET-MANIFEST.json"],
                                        {"schema_version", "archive_id", "assets", "warnings"}, "ARCHIVE_ASSETS")
        assets = unique_records(asset_manifest["assets"], "ARCHIVE_ASSETS")
        selection_mode, selected_assets = attachment_selection(metadata, set(assets))
        units: list[NormalizedUnit] = []
        for asset_id, asset in assets.items():
            require_object(asset, ASSET_FIELDS, "ARCHIVE_ASSETS")
            if asset["sensitivity"] == "restricted":
                raise ContractError("ARCHIVE_SCOPE: restricted attachments require an unavailable encrypted storage adapter")
            if asset["status"] not in {"archived", "preview-only", "external-only", "missing", "excluded", "failed", "unreviewed"}:
                raise ContractError("ARCHIVE_ASSETS: unknown attachment state")
            path = asset["archive_path"]
            if asset["derived_from_asset_id"] is not None and asset["derived_from_asset_id"] not in assets:
                raise ContractError("ARCHIVE_REFERENCE: original attachment identity does not resolve")
            if path is None:
                if asset["status"] == "archived" or not asset["missing_reason"]:
                    raise ContractError("ARCHIVE_ASSETS: missing attachment bytes need an explicit reason")
                content, media_type = canonical_json(asset), "application/json"
                original_selector = {"member": prefix + "ASSET-MANIFEST.json", "asset_id": asset_id}
            else:
                path = member_path(path)
                if (path not in members or type(asset["bytes"]) is not int
                        or asset["bytes"] != len(members[path]) or asset["sha256"] != digest_bytes(members[path])):
                    raise ContractError("ARCHIVE_ASSETS: attachment bytes, path or checksum differ")
                content, media_type = members[path], asset["mime_type"]
                original_selector = {"member": prefix + path, "sha256": digest_bytes(content)}
            catalog_only = asset_id not in selected_assets and path is not None
            if catalog_only:
                content, media_type = canonical_json(asset), "application/json"
                original_selector = {"member": prefix + "ASSET-MANIFEST.json", "asset_id": asset_id}
            units.append(NormalizedUnit("archive:" + archive_id + (":asset-catalog:" if catalog_only else ":asset:") + asset_id, content, media_type,
                                        metadata={"archive_id": archive_id, "asset_id": asset_id,
                                                  "asset_status": asset["status"], "asset": asset,
                                                  "original_selector": original_selector,
                                                  "evidence_kind": "asset-bytes" if path and not catalog_only else "asset-catalog"}))
        if manifest["content_mode"] == "full-source":
            required = {"CONVERSATION.json", "routing/PLAN.json", "routing/PLAN.md", "VISUAL-INSIGHTS.md"}
            if not required <= members.keys() or any(not members[name] for name in required):
                raise ContractError("ARCHIVE_REQUIRED: full-source conversation/routing controls are missing")
            conversation = require_object(documents["CONVERSATION.json"],
                                           {"schema_version", "archive_id", "provider", "coverage", "messages",
                                            "source_records", "branches", "primary_view", "warnings"}, "ARCHIVE_CONVERSATION")
            messages = unique_records(conversation["messages"], "ARCHIVE_MESSAGES")
            records = unique_records(conversation["source_records"], "ARCHIVE_RECORDS")
            branches = unique_records(conversation["branches"], "ARCHIVE_BRANCHES")
            input_ids = set(inputs)
            for order, message in enumerate(conversation["messages"]):
                require_object(message, MESSAGE_FIELDS, "ARCHIVE_MESSAGES")
                if (message["source_id"] not in input_ids or type(message["index"]) is not int
                        or message["index"] < 1 or message["role"] not in {"user", "assistant", "tool", "unknown"}
                        or message["relationship_status"] not in {"observed", "linear-source", "unknown"}
                        or message["fidelity"] not in {"verbatim", "normalized", "ocr", "redacted"}):
                    raise ContractError("ARCHIVE_MESSAGES: message attribution or source relationship is invalid")
                if any(value not in messages for value in require_array(message["parent_ids"], "ARCHIVE_MESSAGES")):
                    raise ContractError("ARCHIVE_REFERENCE: parent message does not resolve")
                if message["branch_id"] is not None and message["branch_id"] not in branches:
                    raise ContractError("ARCHIVE_REFERENCE: branch identity does not resolve")
                if any(value not in assets for value in require_array(message["asset_ids"], "ARCHIVE_MESSAGES")):
                    raise ContractError("ARCHIVE_REFERENCE: attachment identity does not resolve")
                if message["timestamp"] is not None:
                    try:
                        if datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00")).tzinfo is None:
                            raise ValueError()
                    except (ValueError, TypeError, AttributeError) as error:
                        raise ContractError("ARCHIVE_TIME: source timestamp needs an observed offset") from error
                locators = []
                for index, block in enumerate(require_array(message["content"], "ARCHIVE_BLOCK")):
                    if not isinstance(block, dict) or block.get("type") not in {
                            "text", "code", "table", "math", "image", "audio", "video", "file", "link", "unknown"}:
                        raise ContractError("ARCHIVE_BLOCK: unsupported content-bearing block")
                    if "asset_id" in block and block["asset_id"] not in assets:
                        raise ContractError("ARCHIVE_REFERENCE: content attachment does not resolve")
                    if "text" in block:
                        if not isinstance(block["text"], str):
                            raise ContractError("ARCHIVE_BLOCK: text block is malformed")
                        locators.append(f"json:/content/{index}/text")
                    if block["type"] in {"text", "code"} and not isinstance(block.get("text"), str):
                        raise ContractError("ARCHIVE_BLOCK: text/code blocks require retained text")
                    if block["type"] == "code" and "language" not in block:
                        raise ContractError("ARCHIVE_BLOCK: code language must be observed or explicitly null")
                    if block["type"] == "link" and "url" not in block and "unavailable_reason" not in block:
                        raise ContractError("ARCHIVE_BLOCK: link needs a locator or explicit unavailable marker")
                for citation in require_array(message["citations"], "ARCHIVE_CITATION"):
                    require_object(citation, {"label", "url", "title", "source_refs", "retrieval_status", "verification_status"},
                                   "ARCHIVE_CITATION")
                    if (citation["retrieval_status"] not in {"not-retrieved", "retrieved", "unavailable"}
                            or citation["verification_status"] not in {"not-checked", "checked-in-source", "needs-verification", "not-applicable"}):
                        raise ContractError("ARCHIVE_CITATION: citation retrieval/verification state is invalid")
                    if citation["url"] is not None and urlsplit(citation["url"]).scheme not in {"https", "http", "urn"}:
                        raise ContractError("ARCHIVE_CITATION: active or unsafe citation URL")
                units.append(NormalizedUnit("archive:" + archive_id + ":message:" + message["id"],
                                            canonical_json(message), "application/json", tuple(locators) or ("artifact",),
                                            {"archive_id": archive_id, "message_id": message["id"],
                                             "speaker": message["role"], "source_message_id": message["source_message_id"],
                                             "timestamp": message["timestamp"], "branch_id": message["branch_id"],
                                             "summary_derived": False, "source_order": order,
                                             "original_selector": {"member": prefix + "CONVERSATION.json",
                                                                   "json_pointer": f"/messages/{order}",
                                                                   "member_sha256": checksums["CONVERSATION.json"]}}))
            for order, record in enumerate(conversation["source_records"]):
                require_object(record, {"id", "source_id", "kind", "source_locator", "timestamp", "content", "fidelity", "warnings"},
                               "ARCHIVE_RECORDS")
                if record["source_id"] not in input_ids or record["kind"] not in {"summary", "activity", "artifact-text", "unparsed"}:
                    raise ContractError("ARCHIVE_RECORDS: unsupported source-record identity or kind")
                units.append(NormalizedUnit("archive:" + archive_id + ":record:" + record["id"],
                                            canonical_json(record), "application/json", metadata={
                                                "summary_derived": record["kind"] == "summary", "record_id": record["id"],
                                                "original_selector": {"member": prefix + "CONVERSATION.json",
                                                                      "json_pointer": f"/source_records/{order}"}}))
            for branch in branches.values():
                require_object(branch, {"id", "source_branch_id", "message_ids", "selection_status", "evidence"}, "ARCHIVE_BRANCHES")
                if (branch["selection_status"] not in {"selected", "alternative", "unknown"}
                        or any(value not in messages for value in require_array(branch["message_ids"], "ARCHIVE_BRANCHES"))):
                    raise ContractError("ARCHIVE_REFERENCE: branch message does not resolve")
            view = require_object(conversation["primary_view"], {"message_ids", "ordering_basis"}, "ARCHIVE_VIEW")
            if (view["ordering_basis"] not in {"source-order", "parent-graph", "timestamp", "unknown"}
                    or any(value not in messages for value in require_array(view["message_ids"], "ARCHIVE_VIEW"))):
                raise ContractError("ARCHIVE_REFERENCE: reading-view message does not resolve")
        else:
            if "CONVERSATION.json" in members or summary_paths["journey"] != "JOURNEY.md":
                raise ContractError("ARCHIVE_PROFILE: compact summary/journey must not be relabeled as a transcript")
            if "JOURNEY.md" not in members:
                raise ContractError("ARCHIVE_REQUIRED: compact journey is missing")
            journey = members["JOURNEY.md"].decode("utf8")
            matches = list(re.finditer(r"^### (journey-[A-Za-z0-9-]+)[ \t]*\r?$", journey, re.MULTILINE))
            identities = [match[1] for match in matches]
            if len(identities) != len(set(identities)):
                raise ContractError("ARCHIVE_IDENTITY: compact journey anchors are duplicated")
            if compression["checkpoint_count"] is not None and compression["checkpoint_count"] != len(identities):
                raise ContractError("ARCHIVE_TRAIL: declared checkpoint count and Markdown phases disagree")
            trail = documents.get("SUMMARY-TRAIL.json")
            checkpoints = {}
            if trail is not None:
                require_object(trail, {"schema_version", "archive_id", "source_scope", "journey_path", "checkpoints",
                                       "omitted_categories", "known_gaps", "predecessor_refs", "warnings"}, "ARCHIVE_TRAIL")
                checkpoints = unique_records(trail["checkpoints"], "ARCHIVE_TRAIL")
                if list(checkpoints) != identities or trail["journey_path"] != "JOURNEY.md":
                    raise ContractError("ARCHIVE_TRAIL: machine index and Markdown anchors disagree")
                for order, checkpoint in enumerate(checkpoints.values(), 1):
                    require_object(checkpoint, {"id", "order", "journey_ref", "source_id", "source_locator", "source_range",
                                                "source_time", "time_basis", "summary_origin", "basis_refs", "asset_ids",
                                                "supersedes_ids", "limitations"}, "ARCHIVE_TRAIL")
                    if (checkpoint["order"] != order or checkpoint["source_id"] not in inputs
                            or checkpoint["summary_origin"] not in {"extractor-compaction", "supplied-summary", "provider-compaction", "mixed"}
                            or any(value not in assets for value in require_array(checkpoint["asset_ids"], "ARCHIVE_TRAIL"))):
                        raise ContractError("ARCHIVE_TRAIL: checkpoint order, attribution or attachment does not resolve")
            for index, match in enumerate(matches):
                start = len(journey[:match.start()].encode("utf8"))
                end = len(journey[:matches[index + 1].start()].encode("utf8")) if index + 1 < len(matches) else len(members["JOURNEY.md"])
                units.append(NormalizedUnit("archive:" + archive_id + ":record:" + match[1],
                                            members["JOURNEY.md"][start:end], "text/markdown", metadata={
                                                "record_id": match[1], "summary_derived": True, "speaker": None,
                                                "timestamp": None, "checkpoint": checkpoints.get(match[1]), "original_selector": {
                                                    "member": prefix + "JOURNEY.md", "anchor": match[1],
                                                    "byte_start": start, "byte_end": end}}))
            messages, records = {}, dict.fromkeys(identities)
        reference_targets = {"message": messages, "record": records, "asset": assets}
        reference_groups = [asset["source_refs"] for asset in assets.values()]
        reference_groups += [citation["source_refs"] for message in messages.values() for citation in message["citations"]]
        for group in reference_groups:
            for reference in require_array(group, "ARCHIVE_REFERENCE"):
                require_object(reference, {"kind", "id", "locator"}, "ARCHIVE_REFERENCE")
                if reference["kind"] not in reference_targets or reference["id"] not in reference_targets[reference["kind"]]:
                    raise ContractError("ARCHIVE_REFERENCE: typed evidence reference does not resolve inside this unit")
        for name, kind in (("CHAT-SUMMARY.md", "main-summary"), ("CONTINUATION.md", "continuation-state")):
            if name in members:
                units.append(NormalizedUnit("archive:" + archive_id + ":" + kind, members[name], "text/markdown",
                                            metadata={"archive_id": archive_id, "evidence_kind": kind,
                                                      "summary_derived": True,
                                                      "original_selector": {"member": prefix + name,
                                                                            "sha256": checksums[name]}}))
        if len(units) > 10000:
            raise ContractError("ARCHIVE_LIMIT: normalized unit count exceeds the supported budget")
        return NormalizedBundle(tuple(units), ({"name": "normalize-conversation-archive", "version": self.version,
                                                "parameters": {"spec_version": version, "envelope_schema": "3.2",
                                                               "preservation_schema": "2.0", "profile": manifest["package_profile"],
                                                               **({"attachment_selection": metadata["attachment_selection"]}
                                                                  if "attachment_selection" in metadata else {})}},),
                                {"archive_id": archive_id, "archive_revision": manifest["archive_revision"],
                                 "spec_version": version, "profile": manifest["package_profile"],
                                 "delivery": manifest["delivery"], "execution": manifest["execution"],
                                 "coverage_detail": manifest["coverage_detail"],
                                 "producer_validation": validation["overall"],
                                 "adapter_validation": "package-integrity-and-evidence-structure",
                                 "full_producer_conformance": "not-claimed",
                                 "unmapped_metadata": ["source_scope", "schema_registry", "counts", "creative/editorial/knowledge handoffs"],
                                 "branches": documents.get("CONVERSATION.json", {}).get("branches", []),
                                 "primary_view": documents.get("CONVERSATION.json", {}).get("primary_view")})
