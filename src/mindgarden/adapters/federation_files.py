"""Immutable supplied-filesystem federation bundles; no remote acquisition."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from ..domain.contracts import digest_bytes
from ..domain.federation import BUNDLE_NAMES, MAX_FILE_BYTES, verify_bundle
from ..domain.validation import ContractError


def explicit_directory(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    try:
        if path == Path(path.anchor) or any(item.is_symlink() for item in (path, *path.parents)):
            raise ContractError("FEDERATION_PATH: use an explicit directory without symlinks")
    except OSError as error:
        raise ContractError("FEDERATION_PATH: explicit directory cannot be verified") from error
    return path


def read_bundle(directory: Path) -> dict[str, bytes]:
    directory = explicit_directory(directory)
    try:
        members = list(directory.iterdir())
        if {path.name for path in members} != BUNDLE_NAMES:
            raise ContractError("FEDERATION_INVALID: supplied directory has missing or unowned members")
        result = {}
        for path in members:
            if path.is_symlink() or not path.is_file():
                raise ContractError("FEDERATION_INVALID: bundle members must be regular files")
            with path.open("rb") as stream:
                content = stream.read(MAX_FILE_BYTES + 1)
            if len(content) > MAX_FILE_BYTES:
                raise ContractError("FEDERATION_BUDGET: supplied public artifact exceeds the byte limit")
            result[path.name] = content
        return result
    except OSError as error:
        raise ContractError("FEDERATION_UNAVAILABLE: explicitly supplied public bundle is unavailable") from error


def write_bundle(directory: Path, files: dict[str, bytes], *, check_live: Callable[[], None],
                 verify_inputs: Callable[[], object] | None = None) -> bool:
    """Create an immutable bundle; descriptor is the last commit marker.

    Single-writer baseline. Never replace an existing directory or artifact.
    Consumers verify complete membership/checksums before reading any index.
    """
    verify_bundle(files)
    directory = explicit_directory(directory)
    check_live()
    if verify_inputs is not None:
        verify_inputs()
    if directory.exists():
        if read_bundle(directory) != files:
            raise ContractError("FEDERATION_OUTPUT_CONFLICT: retain the existing output and select a fresh export directory")
        check_live()
        return False
    created = []
    selected = False
    try:
        directory.mkdir(mode=0o700)
        selected = True
        for name in sorted(set(files) - {"garden.json"}) + ["garden.json"]:
            check_live()
            if name == "garden.json" and verify_inputs is not None:
                verify_inputs()
            target = directory / name
            with target.open("xb") as stream:
                created.append((target, digest_bytes(files[name])))
                os.chmod(target, 0o600)
                stream.write(files[name])
                stream.flush()
                os.fsync(stream.fileno())
        check_live()
        if verify_inputs is not None:
            verify_inputs()
        return True
    except BaseException as error:
        # Remove only this attempt's newly created files. A crash may leave an
        # incomplete directory; read/verify rejects it, and retry never repairs
        # or overwrites it silently. Power-loss guarantees remain unclaimed.
        for path, expected in reversed(created):
            try:
                if path.is_file() and not path.is_symlink() and (digest_bytes(path.read_bytes()) == expected or path.stat().st_size == 0):
                    path.unlink()
            except OSError:
                pass
        if selected:
            try:
                directory.rmdir()
            except OSError:
                pass
        if isinstance(error, OSError):
            raise ContractError("FEDERATION_OUTPUT: immutable export failed; preserve any incomplete directory and select a fresh destination") from error
        raise
