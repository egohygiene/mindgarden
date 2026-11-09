"""Synthetic recipe for the pinned Mindcap v1 bookmark handoff; no capture SDK."""

from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_STORED

from mindgarden.domain.contracts import canonical_json, digest_bytes

FIXTURES = Path(__file__).parent / "fixtures"


def bundle_members(
    records=None, *, captured_at="2026-11-06T00:00:00Z", status="complete"
):
    if records is None:
        records = json.loads((FIXTURES / "bookmarks/normalized.json").read_bytes())[
            "bookmark_records"
        ]
    records = deepcopy(records)
    # Exact producer envelope from the already committed owner-generated fixture.
    with ZipFile(FIXTURES / "captured-source/synthetic-source.zip") as archive:
        manifest = json.loads(archive.read("CAPTURED-SOURCE.json"))
    members = {"capture/bookmarks.json": canonical_json({"bookmark_records": records})}
    units = []
    for record in records:
        identity = "bookmark-" + digest_bytes(
            canonical_json(
                [
                    record["profile_id"],
                    record.get("source_guid") or record["source_node_id"],
                ]
            )
        )
        stable = {
            k: v
            for k, v in record.items()
            if k not in {"captured_at", "profile_name", "profile_directory"}
        }
        member = "normalized/" + identity + ".json"
        members[member] = canonical_json(stable)
        units.append(
            {
                "identity": identity,
                "member": member,
                "media_type": "application/json",
                "locators": ["json:/title", "json:/url"],
                "identity_basis": "observed",
                "original_members": ["capture/bookmarks.json"],
            }
        )
    manifest.update(
        source_id="synthetic-bookmarks",
        source_type="bookmark-collection",
        captured_at=captured_at,
        status=status,
        warnings=[] if status == "complete" else ["CAPTURE_WARNINGS_PRESENT"],
        units=units,
        artifacts=[
            {
                "path": p,
                "sha256": digest_bytes(b),
                "size_bytes": len(b),
                "role": "normalized" if p.startswith("normalized/") else "raw",
            }
            for p, b in sorted(members.items())
        ],
    )
    members["CAPTURED-SOURCE.json"] = canonical_json(manifest)
    return members


def package(members):
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        for name, content in sorted(members.items()):
            info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100600 << 16
            archive.writestr(info, content)
    return output.getvalue()
