"""Bounded local immutable object storage without networking or credentials."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

from ..domain.contracts import canonical_json, digest_bytes, read_object, safe_path
from ..domain.storage import ContentState, content_digest
from ..domain.validation import ContractError


class FilesystemVault:
    def __init__(self, root: Path, vault_id: str) -> None:
        self.root, self.vault_id = root, vault_id

    def manifest(self) -> dict:
        return {"schema": "mindgarden.vault/v1", "id": self.vault_id,
                "adapter": "filesystem", "format_version": "1.0.0"}

    def capabilities(self) -> dict:
        return {"schema": "mindgarden.storage-capabilities/v1", "adapter": "filesystem",
                "immutable_put": True, "read": True, "checksum_verification": True,
                "audit": True, "export": False, "restore": False, "relocate": False,
                "encryption": False, "remote": False, "destructive_delete": False}

    def _check_root(self) -> None:
        if any(path.is_symlink() for path in (self.root, *self.root.parents)):
            raise ContractError("PATH_SYMLINK: vault root crosses a symlink")
        if not self.root.is_dir():
            raise ContractError("VAULT_UNAVAILABLE: configured storage is unavailable")
        try:
            observed = read_object(safe_path(self.root, "vault.json"))
        except (OSError, ContractError) as error:
            raise ContractError("VAULT_CORRUPTED: storage manifest cannot be verified") from error
        if observed != self.manifest():
            raise ContractError("VAULT_UNSUPPORTED: storage identity or format is incompatible")

    def plan_init(self, bindings_sha256: str) -> dict:
        payload = {"schema": "mindgarden.vault-plan/v1", "operation": "initialize",
                   "vault": self.vault_id, "bindings_sha256": bindings_sha256,
                   "files": [{"path": "vault.json", "sha256": digest_bytes(canonical_json(self.manifest()))}]}
        return {**payload, "plan_sha256": digest_bytes(canonical_json(payload))}

    def initialize(self, plan: dict, reviewed_digest: str) -> bool:
        if plan["plan_sha256"] != reviewed_digest:
            raise ContractError("PLAN_STALE: reviewed initialization digest does not match")
        if any(path.is_symlink() for path in (self.root, *self.root.parents)):
            raise ContractError("PATH_SYMLINK: vault root crosses a symlink")
        if self.root.exists() and any(self.root.iterdir()):
            self._check_root()
            return False
        self.root.mkdir(mode=0o700, parents=False, exist_ok=True)
        path = safe_path(self.root, "vault.json")
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "wb") as output:
            output.write(canonical_json(self.manifest()))
            output.flush()
            os.fsync(output.fileno())
        return True

    def _object_path(self, content_id: str) -> Path:
        digest = content_digest(content_id)
        return safe_path(self.root, f"objects/sha256/{digest[:2]}/{digest}")

    def _read(self, content_id: str) -> bytes:
        self._check_root()
        path = self._object_path(content_id)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as source:
            content = source.read()
        if digest_bytes(content) != content_digest(content_id):
            raise ContractError("VAULT_CORRUPTED: immutable content checksum differs")
        return content

    def state(self, content_id: str) -> ContentState:
        content_digest(content_id)
        if not self.root.exists():
            return ContentState.UNAVAILABLE
        try:
            self._read(content_id)
            return ContentState.AVAILABLE
        except FileNotFoundError:
            return ContentState.MISSING
        except ContractError as error:
            if str(error).startswith("VAULT_UNSUPPORTED"):
                return ContentState.UNSUPPORTED
            if str(error).startswith("VAULT_UNAVAILABLE"):
                return ContentState.UNAVAILABLE
            if str(error).startswith("PATH_SYMLINK"):
                raise
            return ContentState.CORRUPTED
        except OSError:
            return ContentState.UNAVAILABLE

    def get(self, content_id: str) -> bytes:
        state = self.state(content_id)
        if state != ContentState.AVAILABLE:
            raise ContractError("VAULT_" + state.value.upper() + ": source content cannot be verified")
        return self._read(content_id)

    def put(self, content: bytes) -> str:
        self._check_root()
        content_id = "sha256:" + digest_bytes(content)
        target = self._object_path(content_id)
        if target.exists():
            self.get(content_id)
            return content_id
        for directory in (target.parents[2], target.parents[1], target.parent):
            safe_path(self.root, directory.relative_to(self.root).as_posix())
            directory.mkdir(mode=0o700, exist_ok=True)
        safe_path(self.root, target.relative_to(self.root).as_posix())
        descriptor, temporary = tempfile.mkstemp(prefix=".put-", dir=target.parent)
        staged = Path(temporary)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            staged.chmod(0o400)
            try:
                os.link(staged, target)
            except FileExistsError:
                self.get(content_id)
        finally:
            staged.unlink(missing_ok=True)
        return content_id

    def audit(self) -> dict:
        self._check_root()
        objects = safe_path(self.root, "objects")
        results = []
        if objects.exists():
            for path in sorted(objects.rglob("*")):
                if path.is_symlink():
                    raise ContractError("PATH_SYMLINK: vault inventory contains a symlink")
                if not path.is_file():
                    continue
                content_id = "sha256:" + path.name
                try:
                    expected = self._object_path(content_id)
                except ContractError:
                    results.append({"content_id": None, "state": "unsupported"})
                    continue
                results.append({"content_id": content_id,
                                "state": self.state(content_id).value if path == expected else "corrupted"})
        return {"schema": "mindgarden.vault-audit/v1", "vault": self.vault_id,
                "status": "verified" if all(item["state"] == "available" for item in results) else "invalid",
                "objects": results}
