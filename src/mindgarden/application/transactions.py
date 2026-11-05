"""Single-writer multi-garden staging with a private, recoverable operation journal."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile

from ..domain.contracts import canonical_json, digest_bytes, read_object, safe_path
from ..domain.validation import ContractError
from .bindings import LocalBindings, garden_fingerprint
from .changes import ChangePlan


def atomic_journal(path: Path, document: dict) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".mindgarden-journal-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(canonical_json(document)); output.flush(); os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def journal_path(bindings: LocalBindings, digest: str) -> Path:
    if len(digest) != 64 or any(value not in "0123456789abcdef" for value in digest):
        raise ContractError("RECOVERY_DIGEST: supply the exact routing plan digest")
    return safe_path(bindings.path.parent, ".mindgarden-route-" + digest + ".json")


def recover_routing(bindings: LocalBindings, digest: str) -> dict:
    """Roll back an interrupted selection, or finalize an already committed journal."""
    path = journal_path(bindings, digest)
    journal = read_object(path)
    if (journal.get("schema") != "mindgarden.routing-journal/v1" or journal.get("plan_sha256") != digest
            or journal.get("bindings_sha256") != digest_bytes(bindings.path.read_bytes())
            or journal.get("state") not in {"prepared", "selecting", "committed", "rolled-back"}):
        raise ContractError("RECOVERY_INVALID: journal does not match the explicit bindings and operation")
    entries = journal.get("entries", [])
    if (not isinstance(entries, list) or not entries or len(entries) > 100
            or any(not isinstance(item, dict) or set(item) != {"garden", "stage", "backup", "before", "after"}
                   or not all(isinstance(item[field], str) for field in item) for item in entries)
            or len({item["garden"] for item in entries}) != len(entries)):
        raise ContractError("RECOVERY_INVALID: journal ownership entries are invalid")
    checked = []
    for entry in entries:
        root = bindings.garden(entry["garden"])["root"]
        paths = {}
        for field, prefix in (("stage", ".mindgarden-route-stage-"), ("backup", ".mindgarden-route-backup-")):
            name = entry[field]
            if not isinstance(name, str) or "/" in name or not name.startswith(prefix):
                raise ContractError("RECOVERY_PATH: journal contains an unowned temporary path")
            paths[field] = safe_path(root, name)
        lock = safe_path(root, ".mindgarden-write.lock")
        finished = journal["state"] in {"committed", "rolled-back"}
        if ((not lock.is_file() and not finished)
                or (lock.is_file() and read_object(lock).get("plan_sha256") != digest)):
            raise ContractError("RECOVERY_LOCK: this operation does not own every target lock")
        canonical = root / ".garden"
        current = garden_fingerprint(root) if canonical.exists() else None
        if current not in {None, entry["before"], entry["after"]}:
            raise ContractError("RECOVERY_CHANGED: retain the journal and backups; a target changed outside this operation")
        if paths["backup"].exists() and garden_fingerprint(root, garden_root=paths["backup"]) != entry["before"]:
            raise ContractError("RECOVERY_CORRUPTED: retain the last original and restore a verified backup")
        if journal["state"] == "committed" and current != entry["after"]:
            raise ContractError("RECOVERY_CHANGED: committed output cannot be verified")
        if journal["state"] != "committed" and not paths["backup"].exists() and current != entry["before"]:
            raise ContractError("RECOVERY_MISSING: the original tree is unavailable; preserve all recovery evidence")
        checked.append((entry, root, paths, lock))
    # Verify every owner before modifying any tree. Backups survive any failed
    # rollback; repeating recovery converges to the recorded original state.
    committed = journal["state"] == "committed"
    for entry, root, paths, _lock in reversed(checked):
        if not committed and paths["backup"].exists():
            canonical = root / ".garden"
            if canonical.exists():
                if paths["stage"].exists():
                    shutil.rmtree(paths["stage"])
                os.replace(canonical, paths["stage"])
            os.replace(paths["backup"], canonical)
    journal["state"] = "committed" if committed else "rolled-back"
    atomic_journal(path, journal)
    for _entry, _root, paths, lock in checked:
        for temporary in paths.values():
            if temporary.exists():
                shutil.rmtree(temporary)
        lock.unlink(missing_ok=True)
    path.unlink()
    return {"schema": "mindgarden.routing-recovery/v1", "plan_sha256": digest,
            "state": "committed" if committed else "rolled-back", "gardens": len(checked)}


def apply_group(plans: dict[str, ChangePlan], reviewed_digest: str, *, expected_digest: str,
                bindings: LocalBindings, validate) -> bool:
    if reviewed_digest != expected_digest:
        raise ContractError("PLAN_STALE: routing digest differs from the reviewed operation")
    if not plans:
        return False
    journal_file = journal_path(bindings, expected_digest)
    if journal_file.exists():
        raise ContractError("RECOVERY_REQUIRED: recover the recorded routing operation before applying again")
    locks: list[Path] = []
    temporaries: list[Path] = []
    journal = {"schema": "mindgarden.routing-journal/v1", "plan_sha256": expected_digest,
               "bindings_sha256": digest_bytes(bindings.path.read_bytes()), "state": "prepared", "entries": []}
    try:
        for _garden, plan in sorted(plans.items()):
            lock = safe_path(plan.root, ".mindgarden-write.lock")
            try:
                descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError as error:
                raise ContractError("WRITE_LOCKED: another operation or recovery owns a target") from error
            with os.fdopen(descriptor, "wb") as output:
                output.write(canonical_json({"schema": "mindgarden.routing-lock/v1", "plan_sha256": expected_digest}))
            locks.append(lock)
        completed = [plan.verify(plan.digest) for plan in plans.values()]
        if all(completed):
            validate({key: plan.root / ".garden" for key, plan in plans.items()})
            return False
        stages = {}
        for garden, plan in sorted(plans.items()):
            stage = Path(tempfile.mkdtemp(prefix=".mindgarden-route-stage-", dir=plan.root))
            temporaries.append(stage)
            shutil.copytree(plan.root / ".garden", stage, dirs_exist_ok=True)
            for relative, content in sorted(plan.files.items()):
                destination = safe_path(stage, relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    with destination.open("xb") as output:
                        output.write(content)
            stages[garden] = stage
            backup = Path(tempfile.mkdtemp(prefix=".mindgarden-route-backup-", dir=plan.root)); backup.rmdir()
            journal["entries"].append({"garden": garden, "stage": stage.name, "backup": backup.name,
                                       "before": garden_fingerprint(plan.root),
                                       "after": garden_fingerprint(plan.root, garden_root=stage)})
        validate(stages)
        for plan in plans.values():
            plan.verify(plan.digest)
        atomic_journal(journal_file, journal)
        journal["state"] = "selecting"; atomic_journal(journal_file, journal)
        for entry in journal["entries"]:
            root = plans[entry["garden"]].root
            os.replace(root / ".garden", root / entry["backup"])
            os.replace(root / entry["stage"], root / ".garden")
        journal["state"] = "committed"; atomic_journal(journal_file, journal)
        recover_routing(bindings, expected_digest)
        return True
    except BaseException:
        if journal_file.exists():
            # If this fails, the journal and locks intentionally remain. Never
            # delete a last original merely to make a failed operation look clean.
            recover_routing(bindings, expected_digest)
        raise
    finally:
        if not journal_file.exists():
            for path in temporaries:
                if path.exists():
                    shutil.rmtree(path)
            for lock in locks:
                lock.unlink(missing_ok=True)
