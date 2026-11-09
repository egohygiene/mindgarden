"""Tested single-unit v2.0.0–2.0.2/v3.2.2/v3.2.3 evidence normalization, not a producer workflow."""

from __future__ import annotations

import re

from ..domain.contracts import strict_json
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError
from ..domain.zip_package import member_path, read_zip, verify_inventory
from .archive_preservation import (normalize_assets, normalize_conversation, require_array,
                                   require_object, unique_records, validate_references)
from .archive_v2 import normalize_v2, V2_VERSIONS

VERSIONS = {"3.2.2", "3.2.3"}
BASE_FILES = {"README.md", "CHAT-SUMMARY.md", "ARCHIVE-MANIFEST.json", "ASSET-MANIFEST.json",
              "EXTRACTION-REPORT.md", "VALIDATION.json", "MANIFEST.sha256"}
MANIFEST_FIELDS = set("schema_version spec_version archive_id archive_revision created_at updated_at title "
                      "unit_kind source_inputs source_scope capabilities options disabled_layers warnings "
                      "content_mode package_profile transcript_preserved summary_paths compression "
                      "layer_status schema_registry routing execution freeze classification coverage_detail "
                      "counts provenance delivery".split())


class ConversationArchiveAdapter:
    adapter_id = "conversation-archive"
    version = "1.2.0"
    supported_inputs = frozenset(("application/zip", version) for version in VERSIONS | V2_VERSIONS)

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
        envelope = require_object(documents["ARCHIVE-MANIFEST.json"], {"schema_version"}, "ARCHIVE_MANIFEST")
        if envelope["schema_version"] == "2.0":
            return normalize_v2(documents, members, prefix, checksums, metadata, self.version)
        manifest = require_object(envelope, MANIFEST_FIELDS, "ARCHIVE_MANIFEST")
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
        assets, units = normalize_assets(documents, members, prefix, archive_id, metadata)
        if manifest["content_mode"] == "full-source":
            required = {"CONVERSATION.json", "routing/PLAN.json", "routing/PLAN.md", "VISUAL-INSIGHTS.md"}
            if not required <= members.keys() or any(not members[name] for name in required):
                raise ContractError("ARCHIVE_REQUIRED: full-source conversation/routing controls are missing")
            message_units, messages, records = normalize_conversation(
                documents, prefix, archive_id, inputs, assets, checksums)
            units.extend(message_units)
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
        validate_references(assets, messages, records)
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
