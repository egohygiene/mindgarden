"""Reviewed backup, clean restore and non-destructive physical relocation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import os
from pathlib import Path
import tempfile

from ..adapters.filesystem import FilesystemVault
from ..adapters.vault_bundle import MAX_BUNDLE_BYTES, unpack_bundle
from ..domain.contracts import canonical_json, digest_bytes, read_object
from ..domain.garden import inspect_garden
from ..domain.validation import ContractError
from .bindings import LocalBindings, explicit_root, garden_fingerprint
from .ingestion import captured_bytes
from .storage import open_vault


def referenced_content(bindings: LocalBindings, vault_id: str) -> set[str]:
    identities = set()
    for binding in bindings.gardens.values():
        snapshot = inspect_garden(binding["root"], metadata_only=True)
        if snapshot.diagnostics:
            raise ContractError("VAULT_INVENTORY_INCOMPLETE: validate the explicit garden metadata before auditing its source references")
        for record in snapshot.records.values():
            if record["schema"] != "mindgarden.source/v1":
                continue
            artifact = record["artifact"]
            reference = artifact.get("vault")
            if reference and reference["id"] == vault_id:
                if reference["content_id"] != "sha256:" + artifact["sha256"]:
                    raise ContractError("CONTENT_ID: declared vault content identity and source checksum differ")
                identities.add(reference["content_id"])
    return identities


def destination_path(bindings: LocalBindings, vault_id: str, destination: Path, operation: str) -> Path:
    destination = destination.absolute()
    if ".." in destination.parts or any(path.is_symlink() for path in (destination, *destination.parents)):
        raise ContractError("VAULT_DESTINATION: use an explicit target without traversal or symlinks")
    explicit_root(str(destination.parent))
    if operation != "export":
        explicit_root(str(destination), must_exist=False)
    elif destination.exists() and not destination.is_file():
        raise ContractError("VAULT_DESTINATION: export target must be a regular new or identical backup file")
    if destination == bindings.path:
        raise ContractError("VAULT_DESTINATION: backup operations cannot replace local authority")
    for binding in bindings.gardens.values():
        root = binding["root"]
        if destination == root or destination in root.parents or root in destination.parents:
            raise ContractError("VAULT_DESTINATION: original sources and backups require a separate private boundary")
    for binding in bindings.vaults.values():
        root = binding["root"]
        if destination == root and binding["id"] == vault_id and operation in {"restore", "relocate"}:
            continue
        if destination == root or destination in root.parents or root in destination.parents:
            raise ContractError("VAULT_DESTINATION: target overlaps an owned source vault")
    return destination


def replace_bindings(path: Path, content: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".mindgarden-bindings-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(content); output.flush(); os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


@dataclass
class VaultRecoveryPlan:
    operation: str
    bindings: LocalBindings
    vault: FilesystemVault
    destination: Path
    bundle: bytes
    inputs: dict
    input_path: Path | None = None

    def payload(self) -> dict:
        return {"schema": "mindgarden.vault-recovery-plan/v1", "operation": self.operation,
                "vault": self.vault.vault_id, **self.inputs, "retains_original": True}

    @property
    def digest(self) -> str:
        return digest_bytes(canonical_json(self.payload()))

    def document(self) -> dict:
        return {**self.payload(), "plan_sha256": self.digest}

    def rebound_document(self) -> dict:
        document = deepcopy(self.bindings.document)
        for item in document["vaults"]:
            if item["id"] == self.vault.vault_id:
                item["root"] = str(self.destination)
        return document

    def verify(self, reviewed_digest: str) -> bool:
        if reviewed_digest != self.digest:
            raise ContractError("PLAN_STALE: reviewed vault operation digest differs")
        current = read_object(self.bindings.path)
        if self.operation == "relocate" and current == self.rebound_document():
            target = FilesystemVault(self.destination, self.vault.vault_id)
            if target.export_bundle() == self.bundle:
                return True
        if digest_bytes(self.bindings.path.read_bytes()) != self.inputs["bindings_sha256"]:
            raise ContractError("PLAN_STALE: local bindings changed after vault planning")
        for item in self.inputs["garden_revisions"]:
            root = self.bindings.garden(item["garden"])["root"]
            if (root / ".mindgarden-write.lock").exists() or garden_fingerprint(root) != item["revision"]:
                raise ContractError("PLAN_STALE: a source-reference garden changed or is being written")
        if self.input_path is not None and digest_bytes(captured_bytes(self.input_path, MAX_BUNDLE_BYTES)) != self.inputs["bundle_sha256"]:
            raise ContractError("PLAN_STALE: supplied backup bytes changed after planning")
        return False

    def apply(self, reviewed_digest: str) -> bool:
        if self.verify(reviewed_digest):
            return False
        destination_path(self.bindings, self.vault.vault_id, self.destination, self.operation)
        if self.operation == "restore":
            return FilesystemVault(self.destination, self.vault.vault_id).restore_bundle(self.bundle, self.inputs["bundle_sha256"])
        with self.vault.exclusive():
            if self.vault._export_bundle() != self.bundle:
                raise ContractError("PLAN_STALE: immutable vault inventory changed after planning")
            if self.operation == "export":
                if self.destination.exists():
                    if self.destination.read_bytes() == self.bundle:
                        return False
                    raise ContractError("VAULT_DESTINATION_CONFLICT: refusing to replace an existing backup")
                descriptor, temporary = tempfile.mkstemp(prefix=".mindgarden-export-", dir=self.destination.parent)
                try:
                    with os.fdopen(descriptor, "wb") as output:
                        output.write(self.bundle); output.flush(); os.fsync(output.fileno())
                    self.verify(reviewed_digest)
                    try:
                        os.link(temporary, self.destination)
                    except FileExistsError as error:
                        raise ContractError("VAULT_DESTINATION_CONFLICT: another operation created the backup target") from error
                finally:
                    Path(temporary).unlink(missing_ok=True)
                return True
            target = FilesystemVault(self.destination, self.vault.vault_id)
            target.restore_bundle(self.bundle, self.inputs["bundle_sha256"])
            if target.export_bundle() != self.bundle:
                raise ContractError("VAULT_CORRUPTED: relocation target differs after independent reopen")
            self.verify(reviewed_digest)
            replace_bindings(self.bindings.path, canonical_json(self.rebound_document()))
            return True


def build_vault_recovery_plan(bindings: LocalBindings, vault_id: str, operation: str,
                              destination: Path, *, input_path: Path | None = None) -> VaultRecoveryPlan:
    if operation not in {"export", "restore", "relocate"}:
        raise ContractError("VAULT_UNSUPPORTED: unsupported recovery operation")
    vault = open_vault(bindings, vault_id)
    if not isinstance(vault, FilesystemVault):
        raise ContractError("VAULT_UNSUPPORTED: this recovery checkpoint requires the filesystem adapter")
    destination = destination_path(bindings, vault_id, destination, operation)
    if any((item["root"] / ".mindgarden-write.lock").exists() for item in bindings.gardens.values()):
        raise ContractError("VAULT_BUSY: complete garden writes before planning vault recovery")
    references = referenced_content(bindings, vault_id)
    if operation == "restore":
        if input_path is None:
            raise ContractError("VAULT_INPUT: restore requires an explicit backup file")
        input_path = input_path.absolute()
        bundle = captured_bytes(input_path, MAX_BUNDLE_BYTES)
    else:
        if vault.audit(references)["status"] != "verified":
            raise ContractError("VAULT_INTEGRITY: restore missing/corrupted referenced objects before exporting or relocating")
        bundle = vault.export_bundle()
    objects = unpack_bundle(bundle, vault.manifest())
    if not references <= objects.keys():
        raise ContractError("VAULT_EXPORT_MISSING: backup cannot satisfy every supplied garden source reference")
    if operation in {"restore", "relocate"} and destination.exists() and any(destination.iterdir()):
        target = FilesystemVault(destination, vault_id)
        if target.export_bundle() != bundle:
            raise ContractError("VAULT_DESTINATION_CONFLICT: target is not a clean root or an identical owned backup")
    inputs = {"bindings_sha256": digest_bytes(bindings.path.read_bytes()),
              "destination_binding_sha256": digest_bytes(canonical_json({"operation": operation, "root": str(destination)})),
              "bundle_sha256": digest_bytes(bundle), "bundle_size_bytes": len(bundle),
              "objects": [{"content_id": key, "size_bytes": len(value)} for key, value in sorted(objects.items())],
              "garden_revisions": [{"garden": key, "revision": garden_fingerprint(value["root"])}
                                   for key, value in sorted(bindings.gardens.items())]}
    return VaultRecoveryPlan(operation, bindings, vault, destination, bundle, inputs, input_path)
