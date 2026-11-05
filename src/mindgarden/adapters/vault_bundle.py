"""Deterministic bounded portable filesystem backup, independently reopened."""

from io import BytesIO
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, strict_json
from ..domain.storage import content_digest
from ..domain.validation import ContractError
from ..domain.zip_package import read_zip, verify_inventory

MAX_OBJECT_BYTES = 100 * 1024 * 1024
MAX_PAYLOAD_BYTES = 256 * 1024 * 1024
MAX_BUNDLE_BYTES = 264 * 1024 * 1024
MAX_OBJECTS = 4093


def unpack_bundle(content: bytes, manifest: dict) -> dict[str, bytes]:
    members = read_zip(content, captured_limit=MAX_BUNDLE_BYTES, member_limit=MAX_OBJECT_BYTES,
                       expanded_limit=MAX_PAYLOAD_BYTES + 2 * 1024 * 1024)
    verify_inventory(members)
    try:
        descriptor = strict_json(members["vault.json"])
        inventory = strict_json(members["EXPORT.json"])
    except (KeyError, ValueError) as error:
        raise ContractError("VAULT_EXPORT_INVALID: required portable backup controls are missing or malformed") from error
    if descriptor != manifest or ContractRegistry().errors(inventory, "vault-export") or inventory["vault"] != manifest["id"]:
        raise ContractError("VAULT_EXPORT_INVALID: backup identity or format does not match the explicit target")
    objects = {}
    payload_bytes = 0
    paths = {"vault.json", "EXPORT.json", "MANIFEST.sha256"}
    for item in inventory["objects"]:
        digest = content_digest(item["content_id"])
        path = f"objects/sha256/{digest[:2]}/{digest}"
        if item["content_id"] in objects or path not in members:
            raise ContractError("VAULT_EXPORT_INVALID: duplicate identity or missing backup object")
        data = members[path]
        payload_bytes += len(data)
        if len(data) != item["size_bytes"] or digest_bytes(data) != digest:
            raise ContractError("VAULT_EXPORT_CORRUPTED: object size or immutable checksum differs")
        objects[item["content_id"]] = data
        paths.add(path)
    if paths != members.keys() or payload_bytes > MAX_PAYLOAD_BYTES:
        raise ContractError("VAULT_EXPORT_INVALID: unexpected members or payload budget exceeded")
    return objects


def pack_bundle(manifest: dict, objects: dict[str, bytes]) -> bytes:
    if len(objects) > MAX_OBJECTS or sum(map(len, objects.values())) > MAX_PAYLOAD_BYTES:
        raise ContractError("VAULT_EXPORT_LIMIT: export exceeds the bounded local checkpoint")
    members = {"vault.json": canonical_json(manifest), "EXPORT.json": canonical_json({
        "schema": "mindgarden.vault-export/v1", "format_version": "1.0.0", "vault": manifest["id"],
        "objects": [{"content_id": key, "size_bytes": len(value)} for key, value in sorted(objects.items())]})}
    for content_id, data in sorted(objects.items()):
        digest = content_digest(content_id)
        if len(data) > MAX_OBJECT_BYTES or digest_bytes(data) != digest:
            raise ContractError("VAULT_EXPORT_CORRUPTED: object cannot be represented within the declared limits")
        members[f"objects/sha256/{digest[:2]}/{digest}"] = data
    members["MANIFEST.sha256"] = "".join(digest_bytes(data) + "  " + path + "\n"
                                         for path, data in sorted(members.items())).encode()
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        for path, data in sorted(members.items()):
            entry = ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            entry.external_attr = 0o100400 << 16
            archive.writestr(entry, data)
    result = output.getvalue()
    if unpack_bundle(result, manifest) != objects:
        raise ContractError("VAULT_EXPORT_CORRUPTED: independent backup reopen differed")
    return result
