"""Version-aware captured-source plans and deterministic non-overwriting apply."""

from __future__ import annotations

from argparse import Namespace
from copy import deepcopy
from pathlib import Path

from ..adapters.text_source import TextSourceAdapter
from ..adapters.conversation_archive import ConversationArchiveAdapter
from ..adapters.legacy_archive import LegacyConversationArchiveAdapter
from ..adapters.media_source import OpaqueMediaAdapter
from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes
from ..domain.garden import evidence_bytes, inspect_garden
from ..domain.scope import inherit_scope, validate_scope
from ..domain.sources import AdapterRegistry, describe_adapter, normalize_source, validate_origin
from ..domain.validation import ContractError
from .bindings import LocalBindings, garden_fingerprint
from .changes import ChangePlan
from .records import artifact_reference, provenance_record, source_record
from .storage import content_resolver, open_vault


def default_registry() -> AdapterRegistry:
    return AdapterRegistry((TextSourceAdapter(), ConversationArchiveAdapter(), LegacyConversationArchiveAdapter(), OpaqueMediaAdapter()))


def captured_bytes(path: Path, maximum: int = 100 * 1024 * 1024) -> bytes:
    path = path.absolute()
    if any(item.is_symlink() for item in (path, *path.parents)) or not path.is_file():
        raise ContractError("SOURCE_PATH: supply an explicit regular captured file")
    if path.stat().st_size > maximum:
        raise ContractError("SOURCE_OVERSIZED: captured file exceeds the supported adapter limit")
    with path.open("rb") as source:
        content = source.read(maximum + 1)
    if len(content) > maximum:
        raise ContractError("SOURCE_OVERSIZED: captured file exceeds the supported adapter limit")
    return content


def build_ingestion_plan(bindings: LocalBindings, garden_id: str, vault_id: str,
                         input_path: Path, metadata: dict, *, registry: AdapterRegistry | None = None,
                         adapter_id: str | None = None, manifest_version: str | None = None,
                         storage_adapters=None) -> ChangePlan:
    binding = bindings.garden(garden_id)
    validate_origin(metadata["origin"])
    root, scope = binding["root"], validate_scope(binding["scope"])
    if "source_scope" in metadata:
        scope = inherit_scope([scope, validate_scope(metadata["source_scope"])])
        if scope["visibility"] != binding["scope"]["visibility"]:
            raise ContractError("SOURCE_BOUNDARY: source classification does not fit the destination")
    if scope["visibility"] == "public" or scope["persistence"] == "encrypted-vault":
        raise ContractError("SOURCE_BOUNDARY: this adapter requires an ordinary explicitly private vault")
    resolver = content_resolver(bindings, adapters=storage_adapters)
    snapshot = inspect_garden(root, content_resolver=resolver).require_valid()
    adapter = (registry or default_registry()).select(metadata["media_type"], manifest_version, adapter_id)
    declaration = describe_adapter(adapter)
    original = captured_bytes(input_path, declaration["limits"]["capture_bytes"])
    original_digest = digest_bytes(original)
    bundle = normalize_source(adapter, original, {**deepcopy(metadata), "manifest_version": manifest_version})
    files: dict[str, bytes] = {}
    blobs: dict[str, bytes] = {"sha256:" + original_digest: original}
    transforms = ({"name": "preserve-supplied-bytes", "version": "1.0.0", "parameters": {}},)
    capture_key = "supplied:" + metadata["source_id"] + ":" + metadata["origin"]
    capture_id = "capture-" + digest_bytes(capture_key.encode())[:24] + "-" + original_digest[:16]
    provenance = provenance_record(garden_id, "provenance-" + capture_id, capture_id,
                                   original_digest, inputs=[], transformations=transforms,
                                   created_at=metadata["captured_at"], rights=metadata["rights"],
                                   origin=metadata["origin"], scope=scope)
    captured = source_record(garden_id, capture_id, original, vault_id=vault_id, kind="captured",
                             metadata=metadata, scope=scope, provenance=provenance,
                             inputs=[], identity=capture_key)
    captured["x-adapter"] = {"id": adapter.adapter_id, "version": adapter.version,
                            "manifest_version": manifest_version, "metadata": bundle.metadata}
    captured["x-capture-tags"] = metadata.get("tags", [])
    def observation(record: dict) -> dict:
        existing = snapshot.records.get(record["id"])
        if existing is not None and existing != record:
            record["id"] += "-" + digest_bytes(canonical_json(record))[:24]
        return record

    provenance = observation(provenance)
    if capture_id not in snapshot.records:
        captured["provenance"] = [artifact_reference(garden_id, provenance["id"],
                                                    digest_bytes(canonical_json(provenance)))]
        files[f"sources/{capture_id}.json"] = canonical_json(captured)
    files[f"provenance/{provenance['id']}.json"] = canonical_json(provenance)
    normalized_sources = []
    seen: set[str] = set()
    for unit in sorted(bundle.units, key=lambda value: value.identity):
        if unit.identity in seen:
            raise ContractError("SOURCE_DUPLICATE: adapter emitted a duplicate normalized identity")
        seen.add(unit.identity)
        normalized_digest = digest_bytes(unit.content)
        key = {"adapter": adapter.adapter_id, "identity": unit.identity, "media_type": unit.media_type}
        normalized_id = "source-" + digest_bytes(canonical_json(key))[:24] + "-" + normalized_digest[:16]
        input_reference = artifact_reference(garden_id, capture_id, original_digest)
        normalized_provenance = provenance_record(
            garden_id, "provenance-" + normalized_id + "-" + original_digest[:16],
            normalized_id, normalized_digest,
            inputs=[{"artifact": input_reference, "sha256": original_digest, "role": "source"}],
            transformations=bundle.transformations, created_at=metadata["captured_at"],
            rights=metadata["rights"], origin=metadata["origin"], scope=scope)
        normalized_provenance = observation(normalized_provenance)
        normalized = source_record(
            garden_id, normalized_id, unit.content, vault_id=vault_id, kind="normalized",
            metadata={**metadata, "media_type": unit.media_type}, scope=scope,
            provenance=normalized_provenance, inputs=[input_reference], identity=unit.identity)
        normalized["x-adapter"] = {"id": adapter.adapter_id, "version": adapter.version,
                                  "manifest_version": manifest_version, "metadata": unit.metadata}
        existing = snapshot.records.get(normalized_id)
        if existing is not None:
            if (existing.get("x-source-identity") != unit.identity
                    or existing.get("artifact", {}).get("sha256") != normalized_digest
                    or existing.get("kind") != "normalized"):
                raise ContractError("SOURCE_ID_COLLISION: stable source identity conflicts")
            # Keep the original normalized record and first attribution. A new
            # observation below adds package lineage without rewriting evidence.
        else:
            files[f"sources/{normalized_id}.json"] = canonical_json(normalized)
        files[f"provenance/{normalized_provenance['id']}.json"] = canonical_json(normalized_provenance)
        blobs["sha256:" + normalized_digest] = unit.content
        locators = []
        for locator in unit.locators:
            locators.append({"source": artifact_reference(garden_id, normalized_id, normalized_digest),
                             "locator": locator, "content_sha256": digest_bytes(evidence_bytes(unit.content, locator))})
        normalized_sources.append({"source": artifact_reference(garden_id, normalized_id, normalized_digest),
                                   "evidence": locators, "metadata": unit.metadata})
    contract_registry = ContractRegistry()
    for content in files.values():
        if len(content) > 2_000_000:
            raise ContractError("SOURCE_METADATA_LIMIT: generated portable metadata exceeds the supported 2 MB bound")
        from ..domain.contracts import strict_json

        record = strict_json(content)
        errors = contract_registry.errors(record, record["schema"])
        if errors:
            raise ContractError(errors[0].code + ": supplied source metadata is invalid")
    inputs = {"garden_revision": garden_fingerprint(root),
              "scope": scope,
              "bindings_sha256": digest_bytes(bindings.path.read_bytes()),
              "original_sha256": original_digest, "metadata": metadata,
              "adapter": {"id": adapter.adapter_id, "version": adapter.version,
                          "manifest_version": manifest_version,
                          "declaration_sha256": digest_bytes(canonical_json(declaration))},
              "normalized_sources": normalized_sources}
    return ChangePlan("ingest", garden_id, root, inputs, files, blobs,
                      [(input_path.absolute(), original_digest),
                       (bindings.path, digest_bytes(bindings.path.read_bytes()))])


def apply_ingestion(plan: ChangePlan, reviewed_digest: str, bindings: LocalBindings, vault_id: str, *, storage_adapters=None) -> bool:
    vault = open_vault(bindings, vault_id, adapters=storage_adapters)
    if not vault.capabilities()["immutable_put"]:
        raise ContractError("STORAGE_UNSUPPORTED: selected adapter cannot preserve immutable originals")
    resolver = content_resolver(bindings, adapters=storage_adapters)
    return plan.apply(reviewed_digest,
                      validate=lambda stage: inspect_garden(plan.root, garden_root=stage,
                                                           content_resolver=resolver).require_valid(),
                      put_blob=vault.put)


def run_ingest(arguments: Namespace) -> int:
    if not (arguments.repository_root / ".garden/garden.json").is_file():
        from .agent import run_ingest as run_v0_ingest

        if (arguments.apply or arguments.plan_digest or arguments.adapter or arguments.manifest_version
                or arguments.attachment_mode or arguments.asset_id):
            raise ContractError("V0_ARGUMENT: use v0 --write or migrate before using v1 adapter plans")
        return run_v0_ingest(arguments)
    if arguments.write:
        raise ContractError("PLAN_REQUIRED: v1 ingestion uses --apply with --plan-digest")
    if not arguments.local_config or not arguments.vault_id:
        raise ContractError("BINDINGS_REQUIRED: v1 ingestion needs --local-config and --vault-id")
    if arguments.related:
        raise ContractError("CURATION_REQUIRED: propose v1 relationships through a curation plan")
    bindings = LocalBindings.load(arguments.local_config)
    from ..domain.contracts import read_object

    manifest = read_object(arguments.repository_root / ".garden/garden.json")
    garden_id = manifest["id"]
    if bindings.garden(garden_id)["root"] != arguments.repository_root.absolute():
        raise ContractError("BINDING_IDENTITY: supplied workspace differs from the explicit binding")
    metadata = {"source_id": arguments.source_id, "title": arguments.title,
                "owner": arguments.owner, "origin": arguments.origin,
                "captured_at": arguments.captured, "rights": arguments.rights,
                "media_type": arguments.media_type, "tags": arguments.tag}
    if arguments.attachment_mode or arguments.asset_id:
        metadata["attachment_selection"] = {"mode": arguments.attachment_mode or "selected",
                                             "asset_ids": arguments.asset_id}
        if arguments.media_type != "application/zip":
            raise ContractError("ARCHIVE_SELECTION: attachment selection requires an archive adapter")
    plan = build_ingestion_plan(bindings, garden_id, arguments.vault_id, arguments.input, metadata,
                                adapter_id=arguments.adapter, manifest_version=arguments.manifest_version)
    result = plan.document()
    if arguments.apply:
        if not arguments.plan_digest:
            raise ContractError("PLAN_DIGEST: --plan-digest is required with --apply")
        result["applied"] = apply_ingestion(plan, arguments.plan_digest, bindings, arguments.vault_id)
    print(canonical_json(result).decode(), end="")
    return 0
