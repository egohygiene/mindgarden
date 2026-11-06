"""A last-written public portal receipt; never replace caller-owned content."""

import os

from ..domain.contracts import canonical_json, safe_path
from ..domain.portal import PORTAL_MARKER
from ..domain.validation import ContractError
from .site_files import read_artifact


def check_receipt(parent, manifest, *, required=False):
    path = safe_path(parent, PORTAL_MARKER)
    if not path.exists():
        if required:
            raise ContractError("PORTAL_INCOMPLETE: final ownership receipt is unavailable")
        return False
    if read_artifact(path) != canonical_json(manifest):
        raise ContractError("PORTAL_CONFLICT: preserve the existing portal ownership receipt")
    return True


def create_receipt(parent, manifest):
    if check_receipt(parent, manifest):
        return False
    path = safe_path(parent, PORTAL_MARKER)
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(canonical_json(manifest)); stream.flush(); os.fsync(stream.fileno())
    return True
