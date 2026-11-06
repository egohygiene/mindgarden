"""Private ownership inventory for disposable scoped projections, never authority."""

from pathlib import Path
import re

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object, safe_path
from ..domain.validation import ContractError

CACHE_MARKER = ".mindgarden-scope-cache.json"
MAX_CACHE_FILES = 1000
MAX_CACHE_BYTES = 64 * 1024 * 1024


def cache_files(directory: Path) -> dict[str, bytes]:
    files = {}; total = 0
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        safe_path(directory, relative)
        if path.is_symlink() or not path.is_dir() and not path.is_file():
            raise ContractError("CACHE_PATH: owned cache contains an unsafe member")
        if not path.is_file() or relative == CACHE_MARKER:
            continue
        if path.stat().st_size > MAX_CACHE_BYTES:
            raise ContractError("CACHE_BUDGET: owned cache exceeds its byte bound")
        content = path.read_bytes(); total += len(content); files[relative] = content
        if total > MAX_CACHE_BYTES or len(files) > MAX_CACHE_FILES:
            raise ContractError("CACHE_BUDGET: owned cache exceeds its inventory bound")
    return files


def cache_manifest(garden: str, scope_sha256: str, files: dict[str, bytes]) -> dict:
    return {"schema":"mindgarden.scope-cache/v1", "garden":garden, "scope_sha256":scope_sha256,
            "classification":"machine-local-control", "publication":"never-exportable",
            "files":[{"path":name,"sha256":digest_bytes(content),"size_bytes":len(content)}
                     for name,content in sorted(files.items())]}


def verify_cache(directory: Path, garden: str, scope_sha256: str) -> dict | None:
    if not re.fullmatch(r"[0-9a-f]{64}",scope_sha256):
        raise ContractError("CACHE_IDENTITY: supply an exact owned scope digest")
    if not directory.exists(): return None
    marker = safe_path(directory,CACHE_MARKER)
    if not marker.is_file():
        if any(directory.iterdir()):
            raise ContractError("CACHE_UNOWNED: legacy or unowned cache is retained; use a fresh session or inspect locally")
        return None
    document = read_object(marker)
    if ContractRegistry().errors(document,"scope-cache"):
        raise ContractError("CACHE_INTEGRITY: cache ownership inventory is invalid")
    expected = cache_manifest(garden,scope_sha256,cache_files(directory))
    if document != expected:
        raise ContractError("CACHE_INTEGRITY: cache identity, members or checksums differ; retain it for inspection")
    return document
