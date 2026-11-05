"""Private Linux filesystem control state; garden content is never a write target."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

from ..domain.contracts import canonical_json, digest_bytes
from ..domain.validation import ContractError

MAX_CONTROL_BYTES = 2_000_000
MAX_SNAPSHOTS = 1000
HISTORY_MARKER = ".mindgarden-registry-history.json"


def require_platform() -> None:
    if not sys.platform.startswith("linux"):
        raise ContractError("REGISTRY_PLATFORM: registry filesystem operations are supported on Linux only")


def control_path(path: Path) -> Path:
    require_platform()
    path = Path(path)
    if (not path.is_absolute() or ".." in path.parts or path == Path(path.anchor)
            or any(part in {".garden", ".git"} for part in path.parts)):
        raise ContractError("REGISTRY_PATH: use an absolute machine-local control path outside canonical records")
    try:
        for item in (path, *path.parents):
            if item.is_symlink():
                raise ContractError("REGISTRY_PATH: control paths must not cross symlinks")
        for parent in path.parents:
            try:
                marker = parent / ".git"
                info = marker.lstat()
            except FileNotFoundError:
                pass
            else:
                # Some sandboxes install a read-only .git policy stub in /tmp
                # and /workspace. A repository has a gitdir file/link or HEAD;
                # an empty policy directory does not make all /tmp Git-tracked.
                if (not stat.S_ISDIR(info.st_mode) or (marker / "HEAD").exists()
                        or (marker / "HEAD").is_symlink()):
                    raise ContractError("REGISTRY_TRACKED: control state belongs outside version-control workspaces")
            garden = parent / ".garden"
            if garden.is_symlink() or (garden / "garden.json").exists() or (garden / "garden.yaml").exists():
                raise ContractError("REGISTRY_LOCATION: control state belongs outside canonical garden roots, including unregistered ones")
        if path.parent.exists():
            info = path.parent.stat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise ContractError("REGISTRY_PERMISSIONS: use an owner-only configuration directory (0700)")
    except OSError as error:
        raise ContractError("REGISTRY_PATH: explicit control location cannot be verified") from error
    return path


def private_parent(path: Path) -> None:
    path = control_path(path)
    try:
        missing = []
        current = path.parent
        while not current.exists():
            missing.append(current)
            current = current.parent
        for directory in reversed(missing):
            try:
                directory.mkdir(mode=0o700)
            except FileExistsError:
                pass
    except OSError as error:
        raise ContractError("REGISTRY_IO: private control directory cannot be created safely") from error
    control_path(path)


def read_control(path: Path, *, missing_ok: bool = False) -> bytes | None:
    path = control_path(path)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError as error:
        if missing_ok:
            return None
        raise ContractError("REGISTRY_UNAVAILABLE: explicit control file is unavailable") from error
    except OSError as error:
        raise ContractError("REGISTRY_UNAVAILABLE: explicit control file cannot be opened safely") from error
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) & 0o077):
            raise ContractError("REGISTRY_PERMISSIONS: control files must be owner-only regular files (0600)")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            data = stream.read(MAX_CONTROL_BYTES + 1)
        if len(data) > MAX_CONTROL_BYTES:
            raise ContractError("REGISTRY_BUDGET: control file exceeds 2000000 bytes")
        return data
    except OSError as error:
        raise ContractError("REGISTRY_UNAVAILABLE: control file cannot be read safely") from error
    finally:
        if descriptor != -1:
            os.close(descriptor)


def create_control(path: Path, content: bytes) -> bool:
    path = control_path(path)
    if len(content) > MAX_CONTROL_BYTES:
        raise ContractError("REGISTRY_BUDGET: control file exceeds 2000000 bytes")
    private_parent(path)
    current = read_control(path, missing_ok=True)
    if current is not None:
        if current != content:
            raise ContractError("REGISTRY_CONFLICT: refusing to overwrite an existing control artifact")
        return False
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        return True
    except OSError as error:
        raise ContractError("REGISTRY_IO: control artifact creation failed; retain any partial artifact for inspection") from error


@contextmanager
def registry_writer(path: Path):
    """Kernel lease survives no process; leave the lock inode in place."""
    require_platform()
    import fcntl

    path = control_path(path)
    private_parent(path)
    lock = path.parent / ("." + path.name + ".lock")
    descriptor = None
    try:
        descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) & 0o077):
            raise ContractError("REGISTRY_PERMISSIONS: writer lease must be an owned private regular file")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ContractError("REGISTRY_LOCKED: another process owns this registry; retry after it finishes") from error
        yield
    except OSError as error:
        raise ContractError("REGISTRY_IO: registry writer lease is unavailable") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def history_directory(path: Path) -> Path:
    return path.parent / (path.name + ".history")


def history_marker(path: Path) -> bytes:
    return canonical_json({"schema": "mindgarden.registry-history-owner/v1",
                           "registry_location_sha256": digest_bytes(str(path).encode("utf8"))})


def preserve_snapshot(path: Path, content: bytes) -> str:
    directory = history_directory(path)
    marker = directory / HISTORY_MARKER
    if directory.exists():
        if read_control(marker) != history_marker(path):
            raise ContractError("REGISTRY_HISTORY: history ownership cannot be verified")
    else:
        create_control(marker, history_marker(path))
    try:
        members = list(directory.iterdir())
    except OSError as error:
        raise ContractError("REGISTRY_HISTORY: private history cannot be inspected safely") from error
    revision = digest_bytes(content)
    snapshot = directory / (revision + ".json")
    snapshots = [item for item in members if item.name != HISTORY_MARKER]
    if (any(item.name != HISTORY_MARKER and not re.fullmatch(r"[0-9a-f]{64}\.json", item.name) for item in members)
            or len(snapshots) > MAX_SNAPSHOTS
            or (len(snapshots) == MAX_SNAPSHOTS and snapshot not in snapshots)):
        raise ContractError("REGISTRY_HISTORY: preserve owned history; retention needs a separate reviewed action")
    create_control(snapshot, content)
    return revision


def read_snapshot(path: Path, revision: str) -> tuple[Path, bytes]:
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{64}", revision):
        raise ContractError("REGISTRY_SNAPSHOT: supply an exact owned snapshot SHA-256")
    directory = history_directory(path)
    if read_control(directory / HISTORY_MARKER) != history_marker(path):
        raise ContractError("REGISTRY_HISTORY: snapshot ownership cannot be verified")
    target = directory / (revision + ".json")
    content = read_control(target)
    if digest_bytes(content) != revision:
        raise ContractError("REGISTRY_SNAPSHOT: owned snapshot checksum differs")
    return target, content


def replace_registry(path: Path, content: bytes, *, expected_sha256: str | None, verify_inputs) -> None:
    if len(content) > MAX_CONTROL_BYTES:
        raise ContractError("REGISTRY_BUDGET: registry exceeds 2000000 bytes")
    temporary = None
    try:
        current = read_control(path, missing_ok=True)
        if (digest_bytes(current) if current is not None else None) != expected_sha256:
            raise ContractError("REGISTRY_PLAN_STALE: registry changed after preview")
        verify_inputs()
        if current is not None:
            preserve_snapshot(path, current)
        descriptor, temporary = tempfile.mkstemp(prefix=".mindgarden-registry-", dir=path.parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        verify_inputs()
        current = read_control(path, missing_ok=True)
        if (digest_bytes(current) if current is not None else None) != expected_sha256:
            raise ContractError("REGISTRY_PLAN_STALE: registry changed while staging")
        os.replace(temporary, path)
        temporary = None
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as error:
        raise ContractError("REGISTRY_IO: commit state is uncertain; inspect and repeat the exact reviewed plan to reconcile") from error
    finally:
        if temporary is not None:
            try:
                Path(temporary).unlink(missing_ok=True)
            except OSError:
                pass
