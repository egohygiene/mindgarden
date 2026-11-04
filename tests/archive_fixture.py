"""Deterministic ZIPs made solely from committed synthetic archive members."""

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from mindgarden.domain.contracts import canonical_json, digest_bytes, strict_json

FIXTURE_ROOT = Path(__file__).parent / "fixtures/conversation-archives"


def package_members(profile="full-source", version="3.2.3", revision=1, fallback=False):
    members = {path.relative_to(FIXTURE_ROOT / profile).as_posix(): path.read_bytes()
               for path in (FIXTURE_ROOT / profile).rglob("*") if path.is_file()}
    manifest = strict_json(members["ARCHIVE-MANIFEST.json"])
    manifest.update(spec_version=version, archive_revision=revision)
    if fallback:
        manifest["delivery"].update(method="fallback-local-packager", attempts=[
            {"path_id": "primary-file-runtime", "result": "failed-transient",
             "error_class": "transport-or-wrapper-error", "archive_created": False},
            {"path_id": "fallback-local-filesystem", "result": "success",
             "error_class": None, "archive_created": True}])
    members["ARCHIVE-MANIFEST.json"] = canonical_json(manifest)
    return members


def package_bytes(members, *, inventory=True, prefix=""):
    members = dict(members)
    if inventory:
        members["MANIFEST.sha256"] = "".join(digest_bytes(content) + "  " + name + "\n"
                                             for name, content in sorted(members.items())
                                             if name != "MANIFEST.sha256").encode()
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        for name, content in sorted(members.items()):
            entry = ZipInfo(prefix + name, date_time=(2026, 11, 4, 0, 0, 0))
            entry.external_attr = 0o100600 << 16
            archive.writestr(entry, content)
    return output.getvalue()
