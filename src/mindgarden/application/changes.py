"""Digest-bound, non-overwriting single-writer canonical file changes."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable

from ..domain.contracts import canonical_json, digest_bytes, safe_path
from ..domain.validation import ContractError
from .bindings import garden_fingerprint


@dataclass
class ChangePlan:
    operation: str
    garden_id: str
    root: Path
    inputs: dict
    files: dict[str, bytes]
    blobs: dict[str, bytes] = field(default_factory=dict)
    source_checks: list[tuple[Path, str]] = field(default_factory=list)

    def payload(self) -> dict:
        return {"schema": "mindgarden.change-plan/v1", "operation": self.operation,
                "garden": self.garden_id, "inputs": self.inputs,
                "files": [{"path": path, "action": "create-or-verify", "size_bytes": len(content),
                           "sha256": digest_bytes(content)} for path, content in sorted(self.files.items())],
                "blobs": [{"content_id": key, "size_bytes": len(value)}
                          for key, value in sorted(self.blobs.items())]}

    @property
    def digest(self) -> str:
        return digest_bytes(canonical_json(self.payload()))

    def document(self) -> dict:
        return {**self.payload(), "plan_sha256": self.digest}

    def verify(self, reviewed_digest: str) -> bool:
        if reviewed_digest != self.digest:
            raise ContractError("PLAN_STALE: reviewed digest differs from current inputs or outputs")
        for path, digest in self.source_checks:
            if path.is_symlink() or not path.is_file() or digest_bytes(path.read_bytes()) != digest:
                raise ContractError("PLAN_STALE: captured input or configuration changed")
        garden = safe_path(self.root, ".garden")
        current = []
        for relative, content in self.files.items():
            destination = safe_path(garden, relative)
            if destination.exists() and (not destination.is_file() or destination.read_bytes() != content):
                raise ContractError("PLAN_CONFLICT: refusing to overwrite an existing artifact")
            current.append(destination.is_file())
        already_applied = bool(current) and all(current)
        if not already_applied and garden_fingerprint(self.root) != self.inputs["garden_revision"]:
            raise ContractError("PLAN_STALE: canonical target changed after planning")
        return already_applied

    def apply(self, reviewed_digest: str, *, validate: Callable[[Path], None],
              put_blob: Callable[[bytes], str]) -> bool:
        lock = safe_path(self.root, ".mindgarden-write.lock")
        try:
            descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise ContractError("WRITE_LOCKED: another operation or recovery owns this garden") from error
        os.close(descriptor)
        stage: Path | None = None
        backup: Path | None = None
        selected = False
        garden = self.root / ".garden"
        try:
            already_applied = self.verify(reviewed_digest)
            if already_applied:
                validate(garden)
                return False
            for content_id, content in self.blobs.items():
                if put_blob(content) != content_id:
                    raise ContractError("STORAGE_IDENTITY: adapter returned a different immutable identity")
            stage = Path(tempfile.mkdtemp(prefix=".mindgarden-stage-", dir=self.root))
            shutil.copytree(garden, stage, dirs_exist_ok=True)
            for relative, content in sorted(self.files.items()):
                destination = safe_path(stage, relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    with destination.open("xb") as output:
                        output.write(content)
            validate(stage)
            if garden_fingerprint(self.root) != self.inputs["garden_revision"]:
                raise ContractError("PLAN_STALE: canonical target changed during staging")
            backup = Path(tempfile.mkdtemp(prefix=".mindgarden-backup-", dir=self.root))
            backup.rmdir()
            lock.write_bytes(canonical_json({"schema": "mindgarden.write-journal/v1",
                                            "plan_sha256": self.digest, "stage": stage.name,
                                            "backup": backup.name, "state": "prepared"}))
            os.replace(garden, backup)
            try:
                os.replace(stage, garden)
                stage = None
                selected = True
            except BaseException:
                os.replace(backup, garden)
                backup = None
                raise
            return True
        finally:
            if stage is not None:
                shutil.rmtree(stage)
            if backup is not None and backup.exists() and selected:
                shutil.rmtree(backup)
            if backup is None or not backup.exists() or selected:
                lock.unlink(missing_ok=True)
