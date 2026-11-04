"""Bounded ZIP inspection without filesystem extraction or active content."""

from __future__ import annotations

from io import BytesIO
from pathlib import PurePosixPath
import stat
import unicodedata
from zipfile import BadZipFile, ZIP_DEFLATED, ZIP_STORED, ZipFile
from zlib import error as CompressionError

from .validation import ContractError

MAX_MEMBERS = 4096
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200


def member_path(value: str) -> str:
    if (not isinstance(value, str) or not value or len(value) > 1024 or any(ord(character) < 32 for character in value)
            or "\\" in value or ":" in value or value.startswith("/")):
        raise ContractError("ARCHIVE_PATH: package member is not a portable relative path")
    parts = value.rstrip("/").split("/")
    reserved = {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)],
                *[f"LPT{i}" for i in range(1, 10)]}
    if (len(parts) > 16 or any(part in {"", ".", ".."} or part.endswith((".", " "))
                              or part.split(".", 1)[0].upper() in reserved for part in parts)):
        raise ContractError("ARCHIVE_PATH: member path has unsafe or ambiguous components")
    return PurePosixPath(*parts).as_posix()


def read_zip(captured: bytes, *, captured_limit: int = 100 * 1024 * 1024,
             member_limit: int = MAX_MEMBER_BYTES, expanded_limit: int = MAX_EXPANDED_BYTES) -> dict[str, bytes]:
    if len(captured) > captured_limit:
        raise ContractError("ARCHIVE_LIMIT: compressed package exceeds the supported bound")
    members: dict[str, bytes] = {}
    seen: set[str] = set()
    file_paths: set[str] = set()
    directory_paths: set[str] = set()
    total = 0
    try:
        with ZipFile(BytesIO(captured)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_MEMBERS:
                raise ContractError("ARCHIVE_LIMIT: too many package members")
            for entry in entries:
                path = member_path(entry.orig_filename)
                normalized = unicodedata.normalize("NFC", path).casefold()
                if normalized in seen:
                    raise ContractError("ARCHIVE_COLLISION: duplicate case/Unicode-normalized member path")
                seen.add(normalized)
                ancestors = {parent.as_posix() for parent in PurePosixPath(normalized).parents
                             if parent.as_posix() != "."}
                if ancestors & file_paths or not entry.is_dir() and normalized in directory_paths:
                    raise ContractError("ARCHIVE_COLLISION: file and directory ownership paths conflict")
                directory_paths.update(ancestors)
                if entry.is_dir():
                    directory_paths.add(normalized)
                else:
                    file_paths.add(normalized)
                kind = stat.S_IFMT(entry.external_attr >> 16)
                if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                    raise ContractError("ARCHIVE_LINK: links and special members are prohibited")
                if entry.flag_bits & 1:
                    raise ContractError("ARCHIVE_ENCRYPTED: encrypted packages are unsupported")
                if entry.compress_type not in {ZIP_STORED, ZIP_DEFLATED}:
                    raise ContractError("ARCHIVE_UNSUPPORTED: unsupported compression method")
                if entry.is_dir():
                    continue
                total += entry.file_size
                if (entry.file_size > member_limit or total > expanded_limit
                        or entry.file_size > MAX_COMPRESSION_RATIO * max(1, entry.compress_size)):
                    raise ContractError("ARCHIVE_LIMIT: member, expansion or compression-ratio budget exceeded")
                with archive.open(entry) as source:
                    content = source.read(member_limit + 1)
                if len(content) != entry.file_size or len(content) > member_limit:
                    raise ContractError("ARCHIVE_LIMIT: actual member bytes exceed declared bounds")
                members[path] = content
    except (BadZipFile, OSError, RuntimeError, EOFError, CompressionError) as error:
        raise ContractError("ARCHIVE_CORRUPTED: ZIP integrity verification failed") from error
    return members


def verify_inventory(members: dict[str, bytes]) -> dict[str, str]:
    """Exact portable SHA-256 inventory; never hash the inventory into itself."""
    import re

    try:
        lines = members["MANIFEST.sha256"].decode("utf8").splitlines()
    except (KeyError, UnicodeError) as error:
        raise ContractError("ARCHIVE_CHECKSUM: readable SHA-256 inventory is required") from error
    checksums = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-fA-F]{64})  (.+)", line)
        if not match:
            raise ContractError("ARCHIVE_CHECKSUM: malformed SHA-256 inventory")
        path = member_path(match[2])
        if path == "MANIFEST.sha256" or path in checksums:
            raise ContractError("ARCHIVE_CHECKSUM: duplicate or self-referential checksum")
        checksums[path] = match[1].lower()
    if set(checksums) != set(members) - {"MANIFEST.sha256"}:
        raise ContractError("ARCHIVE_MEMBERS: checksum inventory and actual payload members differ")
    from .contracts import digest_bytes

    if any(digest_bytes(members[path]) != digest for path, digest in checksums.items()):
        raise ContractError("ARCHIVE_CHECKSUM: payload bytes do not match the inventory")
    return checksums
