"""Bounded v1.2.1 minimal ZIP profile; no invented cross-export identities."""

from ..domain.contracts import canonical_json, digest_bytes, strict_json
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError
from ..domain.zip_package import member_path, read_zip, verify_inventory
from .archive_selection import attachment_selection


class LegacyConversationArchiveAdapter:
    adapter_id = "conversation-archive-v1"
    version = "1.0.0"
    supported_inputs = frozenset({("application/zip", "1.2.1")})

    def normalize(self, captured: bytes, metadata: dict) -> NormalizedBundle:
        try:
            return self._normalize(captured, metadata)
        except ContractError:
            raise
        except (KeyError, TypeError, ValueError, UnicodeError, AttributeError) as error:
            raise ContractError("ARCHIVE_STRUCTURE: malformed historical archive controls") from error

    def _normalize(self, captured: bytes, metadata: dict) -> NormalizedBundle:
        packaged = read_zip(captured)
        roots = [name.removesuffix("CONVERSATION.json") for name in packaged
                 if name == "CONVERSATION.json" or name.endswith("/CONVERSATION.json")]
        if len(roots) != 1 or any(not name.startswith(roots[0]) for name in packaged):
            raise ContractError("ARCHIVE_UNSUPPORTED: select one v1.2.1 archive unit")
        prefix = roots[0]
        members = {name[len(prefix):]: content for name, content in packaged.items()}
        required = {"README.md", "CHAT-SUMMARY.md", "CONVERSATION.json", "VISUAL-INSIGHTS.md"}
        if not required <= members.keys() or any(not members[name] for name in required):
            raise ContractError("ARCHIVE_REQUIRED: v1.2.1 minimal nonempty controls are required")
        if "ARCHIVE-MANIFEST.json" in members:
            raise ContractError("ARCHIVE_VERSION: this minimal legacy profile does not reinterpret newer envelopes")
        inventory = verify_inventory(members) if "MANIFEST.sha256" in members else None
        document = strict_json(members["CONVERSATION.json"])
        if (not isinstance(document, dict) or document.get("schema_version") != "1.0"
                or document.get("source") != "current-chatgpt-conversation"
                or document.get("coverage") not in {"complete", "partial", "limited"}
                or not isinstance(document.get("messages"), list) or len(document["messages"]) > 10000):
            raise ContractError("ARCHIVE_VERSION: expected the v1.2.1 minimal conversation schema 1.0")
        catalog = strict_json(members["ASSET-MANIFEST.json"]) if "ASSET-MANIFEST.json" in members else {"schema_version": "1.0", "assets": []}
        if not isinstance(catalog, dict) or catalog.get("schema_version") != "1.0" or not isinstance(catalog.get("assets"), list):
            raise ContractError("ARCHIVE_ASSETS: expected the v1 optional asset catalog")
        assets = {}
        for item in catalog["assets"]:
            path = member_path(item["archive_path"])
            if path in assets or item.get("status") not in {"archived", "missing", "external"}:
                raise ContractError("ARCHIVE_ASSETS: duplicate or unsupported legacy asset state")
            assets[path] = item
        # A minimal v1 package may have files without the optional asset manifest.
        for path in members:
            if path.startswith("files/") and path not in assets:
                assets[path] = {"archive_path": path, "status": "archived", "kind": "file"}
        _mode, selected = attachment_selection(metadata, set(assets))
        namespace = metadata["source_id"]
        snapshot_id = digest_bytes(members["CONVERSATION.json"])
        units, seen = [], set()
        for order, message in enumerate(document["messages"]):
            if (not isinstance(message, dict) or type(message.get("index")) is not int or message["index"] < 1
                    or message.get("role") not in {"user", "assistant"}
                    or not isinstance(message.get("text"), str) or not isinstance(message.get("assets"), list)
                    or "timestamp" not in message or message["timestamp"] is not None and not isinstance(message["timestamp"], str)):
                raise ContractError("ARCHIVE_MESSAGES: malformed v1 visible message")
            actual_id = message.get("id")
            if actual_id is not None and (not isinstance(actual_id, str) or not actual_id):
                raise ContractError("ARCHIVE_IDENTITY: optional observed IDs must be nonempty strings")
            key = "observed:" + actual_id if actual_id else "snapshot:" + snapshot_id + ":index:" + str(message["index"])
            if key in seen:
                raise ContractError("ARCHIVE_IDENTITY: duplicate legacy message identity")
            seen.add(key)
            for asset in message["assets"]:
                path = member_path(asset["archive_path"])
                if asset["status"] not in {"archived", "missing", "external"} or asset["status"] == "archived" and path not in members:
                    raise ContractError("ARCHIVE_REFERENCE: legacy archived attachment is missing")
            units.append(NormalizedUnit("legacy:" + namespace + ":message:" + key, canonical_json(message),
                "application/json", ("json:/text",), {"speaker": message["role"], "timestamp": message["timestamp"],
                "source_message_id": actual_id, "source_order": order, "identity_basis": "observed-id" if actual_id else "snapshot-local-index",
                "cross_export_identity": bool(actual_id), "original_selector": {"member": prefix + "CONVERSATION.json",
                "json_pointer": "/messages/" + str(order), "member_sha256": snapshot_id}}))
        for path, asset in sorted(assets.items()):
            archived = asset["status"] == "archived"
            if archived and (path not in members or asset.get("sha256") is not None and asset["sha256"] != digest_bytes(members[path])
                    or asset.get("bytes") is not None and asset["bytes"] != len(members[path])):
                raise ContractError("ARCHIVE_ASSETS: legacy asset bytes or declared checksum differ")
            # Machine locations remain only inside the preserved original ZIP.
            portable = {key: value for key, value in asset.items() if key != "original_path"}
            selected_bytes = archived and path in selected
            content = members[path] if selected_bytes else canonical_json(portable)
            units.append(NormalizedUnit("legacy:" + namespace + (":asset:" if selected_bytes else ":asset-catalog:") + path,
                content, "application/octet-stream" if selected_bytes else "application/json", metadata={
                "asset_status": asset["status"], "evidence_kind": "asset-bytes" if selected_bytes else "asset-catalog",
                "original_selector": {"member": prefix + path} if archived else {"member": prefix + "ASSET-MANIFEST.json", "asset_path": path}}))
        units.append(NormalizedUnit("legacy:" + namespace + ":main-summary", members["CHAT-SUMMARY.md"], "text/markdown",
                                   metadata={"summary_derived": True, "original_selector": {"member": prefix + "CHAT-SUMMARY.md"}}))
        return NormalizedBundle(tuple(units), ({"name": "normalize-legacy-archive", "version": self.version,
            "parameters": {"spec_version": "1.2.1", "preservation_schema": "1.0",
                           "attachment_selection": metadata.get("attachment_selection", {"mode": "all", "asset_ids": []})}},),
            {"spec_version": "1.2.1", "profile": "minimal-single-unit", "producer_coverage": document["coverage"],
             "inventory": "verified" if inventory is not None else "not-supplied-v1-optional",
             "full_producer_conformance": "not-claimed", "identity_limit": "Missing message IDs are snapshot-local; overlaps are not guessed."})
