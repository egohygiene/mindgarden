"""Normalize a verified supplied Drive capture; never acquire or run a model."""

from copy import deepcopy
import io
from zipfile import BadZipFile, ZIP_STORED, ZipFile

from ..domain.contracts import ContractRegistry, digest_bytes, strict_json
from ..domain.scope import local_scope
from ..domain.drive_capture import EXPORTS
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError
from .ledger_csv import LedgerCSVAdapter
from .text_source import TextSourceAdapter


class DriveCaptureAdapter:
    adapter_id = "drive-capture"
    version = "1.0.0"
    supported_inputs = frozenset(
        {("application/vnd.mindgarden.drive-capture+zip", "1.0.0")}
    )
    limits = {"capture_bytes": 20_000_000, "units": 1000, "unit_bytes": 2_000_001}

    def normalize(self, captured, metadata):
        try:
            with ZipFile(io.BytesIO(captured)) as archive:
                infos = archive.infolist()
                names = [info.filename for info in infos]
                if (
                    len(names) != len(set(names))
                    or "manifest.json" not in names
                    or len(names) > 66
                    or any(
                        info.compress_type != ZIP_STORED
                        or info.flag_bits & 1
                        or info.file_size > 16_000_000
                        or info.external_attr >> 28 == 0xA
                        for info in infos
                    )
                ):
                    raise ValueError()
                if archive.getinfo("manifest.json").file_size > 1_000_000:
                    raise ValueError()
                manifest = strict_json(archive.read("manifest.json"))
                if ContractRegistry().errors(manifest, "drive-capture"):
                    raise ValueError()
                if (
                    manifest["scope"]
                    != local_scope(
                        execution="controlled-import", publication="never-exportable"
                    )
                    or metadata.get("source_scope") != manifest["scope"]
                ):
                    raise ContractError(
                        "CAPTURE_SCOPE: supply the exact reviewed captured scope; do not weaken its boundary"
                    )
                if len({item["file_id"] for item in manifest["files"]}) != len(
                    manifest["files"]
                ):
                    raise ValueError()
                expected = {
                    "manifest.json",
                    *("objects/" + item["sha256"] for item in manifest["files"]),
                }
                if set(names) != expected:
                    raise ValueError()
                units, states, transforms = {}, [], []
                for item in sorted(
                    manifest["files"], key=lambda value: value["file_id"]
                ):
                    member = "objects/" + item["sha256"]
                    raw = archive.read(member)
                    if (
                        len(raw) != item["size_bytes"]
                        or digest_bytes(raw) != item["sha256"]
                        or len(raw) > 2_000_000
                    ):
                        raise ValueError()
                    media = item["media_type"]
                    if media != item["source_mime_type"] and media not in EXPORTS.get(
                        item["source_mime_type"], set()
                    ):
                        raise ContractError(
                            "CAPTURE_FORMAT: captured native export mapping is unsupported"
                        )
                    adapter = (
                        LedgerCSVAdapter()
                        if media == "text/csv"
                        else TextSourceAdapter()
                        if media in {"text/plain", "text/markdown"}
                        else None
                    )
                    if adapter is None:
                        states.append(
                            {
                                "file_id": item["file_id"],
                                "state": "preserved-only",
                                "reason": "use a separately reviewed document/media adapter",
                            }
                        )
                        continue
                    bundle = adapter.normalize(
                        raw,
                        {
                            **deepcopy(metadata),
                            "source_id": "google-drive-"
                            + digest_bytes(item["file_id"].encode())[:24],
                            "media_type": media,
                        },
                    )
                    for unit in bundle.units:
                        details = {
                            **deepcopy(unit.metadata),
                            "provider_file_id": item["file_id"],
                            "provider_version": item["version"],
                            "original_member": member,
                            "member_sha256": item["sha256"],
                            "source_mime_type": item["source_mime_type"],
                            "export_mime_type": media,
                            "losses": item["losses"],
                        }
                        previous = units.get(unit.identity)
                        if previous is not None:
                            if previous.content != unit.content:
                                raise ContractError(
                                    "CAPTURE_CONFLICT: conflicting row revisions require separate explicit captures and reviewed reconciliation"
                                )
                            continue
                        units[unit.identity] = NormalizedUnit(
                            unit.identity,
                            unit.content,
                            unit.media_type,
                            unit.locators,
                            details,
                        )
                    states.append(
                        {
                            "file_id": item["file_id"],
                            "state": "normalized",
                            "adapter": adapter.adapter_id,
                        }
                    )
                    transforms.append(
                        {
                            "name": "normalize-verified-captured-file",
                            "version": "1.0.0",
                            "parameters": {
                                "file_id": item["file_id"],
                                "steps": list(bundle.transformations),
                            },
                        }
                    )
                return NormalizedBundle(
                    tuple(units.values()),
                    tuple(transforms),
                    {
                        "provider": manifest["provider"],
                        "captured_scope": manifest["scope"],
                        "normalization_states": states,
                        "unavailable_previous": manifest["unavailable_previous"],
                    },
                )
        except ContractError:
            raise
        except (BadZipFile, KeyError, TypeError, ValueError, OSError) as error:
            raise ContractError(
                "CAPTURE_PACKAGE: captured manifest/membership/bytes are malformed or corrupted"
            ) from error
