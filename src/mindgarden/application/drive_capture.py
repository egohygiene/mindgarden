"""Reviewed acquisition into immutable storage; normalization/review stay separate."""

from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from ..adapters.generated_files import apply_generated, complete_generated
from ..adapters.google_drive import GoogleDriveProvider, provider_metadata
from ..adapters.registry_files import control_path, private_parent
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from ..domain.drive_capture import FOLDER, binding_digest, export_type, validate_binding
from ..domain.validation import ContractError
from .bindings import LocalBindings
from .federation import protected_export_destination
from .storage import open_vault


def selection_digest(binding):
    selected = deepcopy(binding)
    selected.pop("captured_at")
    return digest_bytes(canonical_json(selected))


def enumerate_files(binding, provider):
    pending = [(identity, 0) for identity in binding["folders"]]
    visited, selected = set(), {}
    while pending:
        folder, depth = pending.pop(0)
        if folder in visited:
            continue
        visited.add(folder)
        if len(visited) > binding["limits"]["max_files"]:
            raise ContractError(
                "CAPTURE_BUDGET: folder traversal exceeds the selected ceiling"
            )
        root = provider_metadata(provider.stat(folder))
        if root["mimeType"] != FOLDER:
            raise ContractError(
                "CAPTURE_FOLDER: selected root is not an available folder"
            )
        for raw in provider.children(folder):
            item = provider_metadata(raw)
            if folder not in item.get("parents", []):
                raise ContractError(
                    "CAPTURE_PROVIDER: listing returned an item outside the selected parent"
                )
            if item["mimeType"] == FOLDER:
                if binding["recursive"]:
                    if depth >= binding["limits"]["max_depth"]:
                        raise ContractError(
                            "CAPTURE_BUDGET: traversal reached the declared depth ceiling"
                        )
                    pending.append((item["id"], depth + 1))
                continue
            if binding["file_ids"] and item["id"] not in binding["file_ids"]:
                continue
            if export_type(binding, item) is None:
                continue
            old = selected.get(item["id"])
            if old is not None and old != item:
                raise ContractError(
                    "CAPTURE_CHANGED: provider listing changed during enumeration"
                )
            selected[item["id"]] = item
            if len(selected) > binding["limits"]["max_files"]:
                raise ContractError(
                    "CAPTURE_BUDGET: selected source count exceeds the ceiling"
                )
    if set(binding["file_ids"]) - set(selected):
        raise ContractError(
            "CAPTURE_MISSING: an explicitly selected source is absent or unavailable"
        )
    return selected


def checkpoint_write(path, state):
    content = canonical_json(state)
    if len(content) > 2_000_000:
        raise ContractError(
            "CAPTURE_BUDGET: retain prior capture state and narrow the selection"
        )
    private_parent(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".capture-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def load_checkpoint(path, binding, vault_id):
    state = read_object(control_path(path))
    if (
        set(state) != {"schema", "selection_sha256", "vault", "entries"}
        or state["schema"] != "mindgarden.drive-checkpoint/v1"
        or state["selection_sha256"] != selection_digest(binding)
        or state["vault"] != vault_id
        or not isinstance(state["entries"], dict)
    ):
        raise ContractError(
            "CAPTURE_CHECKPOINT: preserve unrelated/incompatible state and choose a new checkpoint"
        )
    return state


def collect(
    binding, provider, vault, checkpoint, *, previous=None, check_live=lambda: None
):
    """Partial objects stay immutable; only a stable complete selection is packaged."""
    binding = deepcopy(validate_binding(binding))
    checkpoint = control_path(checkpoint)
    state = {
        "schema": "mindgarden.drive-checkpoint/v1",
        "selection_sha256": selection_digest(binding),
        "vault": vault.vault_id,
        "entries": {},
    }
    if checkpoint.exists():
        state = load_checkpoint(checkpoint, binding, vault.vault_id)
    elif previous is not None:
        state = deepcopy(load_checkpoint(previous, binding, vault.vault_id))
    private_parent(checkpoint)
    lock = checkpoint.with_name(checkpoint.name + ".lock")
    try:
        handle = os.open(
            control_path(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
    except FileExistsError as error:
        raise ContractError(
            "CAPTURE_LOCKED: preserve the active/recovery capture lock"
        ) from error
    os.close(handle)
    try:
        check_live()
        current = enumerate_files(binding, provider)
        entries, blobs, total = [], {}, 0
        for identity, listed in sorted(current.items()):
            check_live()
            before = provider_metadata(provider.stat(identity))
            if before != listed:
                raise ContractError(
                    "CAPTURE_CHANGED: source metadata changed after enumeration"
                )
            if before.get("capabilities", {}).get("canDownload") is not True:
                raise ContractError(
                    "CAPTURE_DENIED: selected content is not explicitly downloadable"
                )
            media = export_type(binding, before)
            if (
                media == before["mimeType"]
                and "size" in before
                and int(before["size"]) > binding["limits"]["max_file_bytes"]
            ):
                raise ContractError(
                    "CAPTURE_BUDGET: selected file exceeds the byte ceiling"
                )
            old = state["entries"].get(identity)
            if (
                isinstance(old, dict)
                and old.get("metadata") == before
                and old.get("media_type") == media
            ):
                content = vault.get(old["content_id"])
            else:
                content = provider.read(before, media)
            if (
                not isinstance(content, bytes)
                or len(content) > binding["limits"]["max_file_bytes"]
            ):
                raise ContractError(
                    "CAPTURE_BUDGET: selected content exceeds the byte ceiling"
                )
            if media == before["mimeType"]:
                if "size" in before and len(content) != int(before["size"]):
                    raise ContractError(
                        "CAPTURE_CORRUPTED: source byte size differs from provider metadata"
                    )
                if (
                    before.get("sha256Checksum")
                    and digest_bytes(content) != before["sha256Checksum"]
                    or before.get("md5Checksum")
                    and hashlib.md5(content, usedforsecurity=False).hexdigest()
                    != before["md5Checksum"]
                ):
                    raise ContractError(
                        "CAPTURE_CORRUPTED: source checksum differs from provider metadata"
                    )
            if provider_metadata(provider.stat(identity)) != before:
                raise ContractError(
                    "CAPTURE_CHANGED: source version changed across the captured read/export"
                )
            total += len(content)
            if total > binding["limits"]["max_bytes"]:
                raise ContractError(
                    "CAPTURE_BUDGET: total selected bytes exceed the ceiling"
                )
            check_live()
            content_id = vault.put(content)
            if content_id != "sha256:" + digest_bytes(content):
                raise ContractError(
                    "CAPTURE_CORRUPTED: storage returned a different immutable identity"
                )
            entry = {"metadata": before, "media_type": media, "content_id": content_id}
            state["entries"][identity] = entry
            checkpoint_write(checkpoint, state)
            blobs[content_id] = content
            losses = (
                ["first-sheet-only"]
                if before["mimeType"] == "application/vnd.google-apps.spreadsheet"
                else ["plain-text-export-no-embedded-media"]
                if before["mimeType"] == "application/vnd.google-apps.document"
                else []
            )
            entries.append(
                {
                    "file_id": identity,
                    "name": before["name"],
                    "version": before["version"],
                    "source_mime_type": before["mimeType"],
                    "media_type": media,
                    "sha256": digest_bytes(content),
                    "size_bytes": len(content),
                    "losses": losses,
                }
            )
        if enumerate_files(binding, provider) != current:
            raise ContractError(
                "CAPTURE_CHANGED: collection changed; retain checkpoint and repeat a reviewed capture"
            )
        manifest = {
            "schema": "mindgarden.drive-capture/v1",
            "id": binding["id"],
            "captured_at": binding["captured_at"],
            "scope": binding["scope"],
            "provider": "google-drive-v3",
            "selection_sha256": selection_digest(binding),
            "coverage": "stable-selected-enumeration-and-per-file-versions",
            "files": entries,
            "unavailable_previous": sorted(set(state["entries"]) - set(current)),
        }
        if ContractRegistry().errors(manifest, "drive-capture"):
            raise ContractError(
                "CAPTURE_PROVIDER: complete captured metadata exceeds the declared contract"
            )
        check_live()
        output = io.BytesIO()
        with ZipFile(output, "w", compression=ZIP_STORED) as archive:
            for name, value in sorted(
                {
                    "manifest.json": canonical_json(manifest),
                    **{
                        "objects/" + identity.removeprefix("sha256:"): value
                        for identity, value in blobs.items()
                    },
                }.items()
            ):
                info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.external_attr = 0o100600 << 16
                archive.writestr(info, value)
        checkpoint_write(checkpoint, state)
        return output.getvalue(), manifest
    finally:
        lock.unlink(missing_ok=True)


def run_capture(arguments):
    binding = validate_binding(read_object(control_path(arguments.input)))
    bindings = LocalBindings.load(arguments.local_config)
    vault = open_vault(bindings, arguments.vault_id)
    directory = protected_export_destination(
        bindings,
        arguments.output_directory.absolute().parent,
        arguments.output_directory.name,
    )
    control_path(directory / ".mindgarden-generated.json")
    planned = {
        "schema": "mindgarden.drive-capture-plan/v1",
        "operation": "bounded-read-only-capture",
        "binding_sha256": binding_digest(binding),
        "configuration_sha256": digest_bytes(arguments.local_config.read_bytes()),
        "vault": arguments.vault_id,
        "destination": str(directory),
        "limits": binding["limits"],
        "normalization": "separate digest-bound supplied-artifact step",
    }
    digest = digest_bytes(canonical_json(planned))
    if not arguments.apply:
        print(canonical_json({**planned, "plan_sha256": digest}).decode(), end="")
        return 0
    if arguments.plan_digest != digest:
        raise ContractError(
            "CAPTURE_PLAN_STALE: review the current selection/location before acquisition"
        )
    if not arguments.allow_network:
        raise ContractError(
            "CAPTURE_NETWORK: explicit --allow-network is required for live provider acquisition"
        )

    def verify():
        if (
            binding_digest(read_object(arguments.input)) != planned["binding_sha256"]
            or digest_bytes(arguments.local_config.read_bytes())
            != planned["configuration_sha256"]
        ):
            raise ContractError(
                "CAPTURE_PLAN_STALE: capture selection or storage bindings changed"
            )

    provider = GoogleDriveProvider(binding["limits"], check_live=verify)
    checkpoint = directory.with_name(directory.name + ".capture-checkpoint.json")
    content, manifest = collect(
        binding,
        provider,
        vault,
        checkpoint,
        previous=arguments.previous_checkpoint,
        check_live=verify,
    )
    files = {
        "capture.zip": content,
        "manifest.json": canonical_json(manifest),
        "source-scope.json": canonical_json(binding["scope"]),
    }
    maximum = binding["limits"]["max_bytes"] + 1_000_000
    if sum(map(len, complete_generated(files, digest).values())) > maximum:
        raise ContractError(
            "CAPTURE_BUDGET: complete snapshot metadata exceeds the bounded output ceiling"
        )
    changed = apply_generated(
        directory, files, digest, digest, check_live=verify, verify_inputs=verify
    )
    print(
        json.dumps(
            {
                "status": "created" if changed else "verified-no-op",
                "capture_sha256": digest_bytes(content),
                "files": len(manifest["files"]),
                "normalization": "not performed",
            },
            sort_keys=True,
        )
    )
    return 0
