"""Verify exact Darwin path spelling without accepting case/Unicode aliases."""

import os
from pathlib import Path
import sys

from ..domain.validation import ContractError


def require_canonical_directory(path: Path, *, code: str) -> None:
    if sys.platform != "darwin": return
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        raise ContractError(code + ": explicit directory path cannot be verified") from error
    try:
        require_canonical_path(descriptor, path, code=code)
    finally:
        os.close(descriptor)


def require_canonical_path(descriptor: int, path: Path, *, code: str) -> None:
    if sys.platform != "darwin": return
    import fcntl

    # Darwin F_GETPATH = 50, PATH_MAX = 1024; verified against XNU
    # f6217f891ac0bb64f3d375211650a4c1ff8ca1ea public fcntl/syslimits headers.
    try:
        value = fcntl.fcntl(descriptor, 50, bytes(1024))
        if not isinstance(value, bytes) or b"\0" not in value:
            raise ValueError()
        actual = Path(os.fsdecode(value.split(b"\0", 1)[0]))
        if not actual.is_absolute() or actual != path:
            raise ValueError()
    except (OSError, ValueError, UnicodeError) as error:
        raise ContractError(code + ": supply the physical path with its exact on-disk spelling") from error
