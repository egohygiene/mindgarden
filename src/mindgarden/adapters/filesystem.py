"""Bounded local immutable object storage without networking or credentials."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import re
import shutil
import tempfile

from ..domain.contracts import canonical_json, digest_bytes, read_object, safe_path
from ..domain.storage import ContentState, content_digest
from ..domain.validation import ContractError
from .vault_bundle import MAX_BUNDLE_BYTES, MAX_OBJECT_BYTES, MAX_OBJECTS, MAX_PAYLOAD_BYTES, pack_bundle, unpack_bundle


class FilesystemVault:
    def __init__(self, root: Path, vault_id: str) -> None:
        self.root, self.vault_id = root, vault_id

    def manifest(self) -> dict:
        return {"schema": "mindgarden.vault/v1", "id": self.vault_id,
                "adapter": "filesystem", "format_version": "1.0.0"}

    def capabilities(self) -> dict:
        return {"schema": "mindgarden.storage-capabilities/v1", "adapter": "filesystem",
                "immutable_put": True, "read": True, "checksum_verification": True,
                "audit": True, "export": True, "restore": True, "relocate": True,
                "encryption": False, "remote": False, "destructive_delete": False,
                "limits": {"max_object_bytes": MAX_OBJECT_BYTES, "max_export_payload_bytes": MAX_PAYLOAD_BYTES,
                           "max_export_objects": MAX_OBJECTS, "max_bundle_bytes": MAX_BUNDLE_BYTES},
                "verified_platforms": ["linux"], "relocation": "copy-verify-rebind-retain-original"}

    @contextmanager
    def exclusive(self):
        """A kernel-released single-writer lease; no stale PID or lock-file removal."""
        if any(path.is_symlink() for path in (self.root, *self.root.parents)):
            raise ContractError("PATH_SYMLINK: vault ownership crosses a symlink")
        name = ".mindgarden-vault-" + digest_bytes(str(self.root.absolute()).encode())[:24] + ".lock"
        path = safe_path(self.root.parent, name)
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        unlock = None
        try:
            if os.name == "posix":
                import fcntl

                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as error:
                    raise ContractError("VAULT_BUSY: another local operation owns the vault writer lease") from error
                unlock = lambda: fcntl.flock(descriptor, fcntl.LOCK_UN)
            elif os.name == "nt":  # Not part of the verified platform matrix.
                import msvcrt

                if os.fstat(descriptor).st_size == 0:
                    os.write(descriptor, b"0")
                os.lseek(descriptor, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                except OSError as error:
                    raise ContractError("VAULT_BUSY: another local operation owns the vault writer lease") from error
                unlock = lambda: (os.lseek(descriptor, 0, os.SEEK_SET), msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1))
            else:
                raise ContractError("VAULT_UNSUPPORTED: this platform has no implemented writer lease")
            yield
        finally:
            if unlock:
                unlock()
            os.close(descriptor)

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
        with self.exclusive():
            return self._initialize(plan, reviewed_digest)

    def _initialize(self, plan: dict, reviewed_digest: str) -> bool:
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
            if os.fstat(source.fileno()).st_size > MAX_OBJECT_BYTES:
                raise ContractError("VAULT_UNSUPPORTED: object exceeds the bounded filesystem format")
            content = source.read(MAX_OBJECT_BYTES + 1)
        if len(content) > MAX_OBJECT_BYTES:
            raise ContractError("VAULT_CORRUPTED: object exceeds its supported read budget")
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
        if len(content) > MAX_OBJECT_BYTES:
            raise ContractError("VAULT_LIMIT: immutable object exceeds 100 MiB")
        with self.exclusive():
            return self._put(content)

    def _put(self, content: bytes) -> str:
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

    def audit(self, expected: set[str] | None = None) -> dict:
        self._check_root()
        objects = safe_path(self.root, "objects")
        results = []
        for path in sorted(self.root.rglob("*")):
            relative = path.relative_to(self.root).as_posix()
            if path.is_symlink():
                raise ContractError("PATH_SYMLINK: vault inventory contains a symlink")
            if path.is_file() and relative != "vault.json" and not relative.startswith("objects/"):
                results.append({"content_id": None, "state": "unsupported"})
            if path.is_dir() and not (relative in {"objects", "objects/sha256"}
                                      or re.fullmatch(r"objects/sha256/[0-9a-f]{2}", relative)):
                results.append({"content_id": None, "state": "unsupported"})
        if objects.exists() and not objects.is_dir():
            raise ContractError("VAULT_CORRUPTED: object ownership root is not a directory")
        if objects.exists():
            for path in sorted(objects.rglob("*")):
                if path.is_symlink():
                    raise ContractError("PATH_SYMLINK: vault inventory contains a symlink")
                if not path.is_file():
                    continue
                content_id = "sha256:" + path.name
                try:
                    expected_path = self._object_path(content_id)
                except ContractError:
                    results.append({"content_id": None, "state": "unsupported"})
                    continue
                results.append({"content_id": content_id,
                                "state": self.state(content_id).value if path == expected_path else "corrupted"})
        represented = {item["content_id"] for item in results}
        for content_id in sorted(expected or set()):
            content_digest(content_id)
            if content_id not in represented:
                results.append({"content_id": content_id, "state": self.state(content_id).value})
        results.sort(key=lambda item: (item["content_id"] or "", item["state"]))
        return {"schema": "mindgarden.vault-audit/v1", "vault": self.vault_id,
                "status": "verified" if all(item["state"] == "available" for item in results) else "invalid",
                "coverage": "inventory-and-supplied-references" if expected is not None else "inventory-only", "objects": results}

    def export_bundle(self) -> bytes:
        with self.exclusive():
            return self._export_bundle()

    def _export_bundle(self) -> bytes:
        inventory = self.audit()
        if inventory["status"] != "verified":
            raise ContractError("VAULT_CORRUPTED: export requires a verified complete object inventory")
        objects = {item["content_id"]: self.get(item["content_id"]) for item in inventory["objects"]}
        bundle = pack_bundle(self.manifest(), objects)
        if self.audit() != inventory:
            raise ContractError("PLAN_STALE: vault changed during export verification")
        return bundle

    def restore_bundle(self, content: bytes, reviewed_sha256: str) -> bool:
        if digest_bytes(content) != reviewed_sha256:
            raise ContractError("PLAN_STALE: backup bytes differ from the reviewed immutable digest")
        objects = unpack_bundle(content, self.manifest())
        with self.exclusive():
            if self.root.exists() and any(self.root.iterdir()):
                if self._export_bundle() == content:
                    return False
                raise ContractError("VAULT_DESTINATION_CONFLICT: restore requires a clean target or identical owned backup")
            stage = Path(tempfile.mkdtemp(prefix=".mindgarden-vault-restore-", dir=self.root.parent))
            try:
                staged = FilesystemVault(stage, self.vault_id)
                initialization = staged.plan_init("0" * 64)
                staged.initialize(initialization, initialization["plan_sha256"])
                for content_id, data in sorted(objects.items()):
                    if staged.put(data) != content_id:
                        raise ContractError("VAULT_CORRUPTED: restored immutable identity differs")
                if staged.export_bundle() != content:
                    raise ContractError("VAULT_CORRUPTED: independently reopened restored backup differs")
                os.replace(stage, self.root)
                return True
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
