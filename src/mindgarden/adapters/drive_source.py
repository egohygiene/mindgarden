"""Normalize a verified supplied Drive capture; never acquire or run a model."""

from copy import deepcopy
import io
from zipfile import BadZipFile, ZIP_STORED, ZipFile

from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    strict_json,
)
from ..domain.scope import local_scope
from ..domain.drive_capture import EXPORTS
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError
from .ledger_csv import LedgerCSVAdapter
from .mapped_ledger_csv import MappedLedgerCSVAdapter, validate_mapping
from .text_source import TextSourceAdapter


def reviewed_mappings(metadata, files):
    if "drive_normalization" not in metadata:
        return {}, None
    configuration = deepcopy(metadata["drive_normalization"])
    if ContractRegistry().errors(configuration, "drive-normalization"):
        raise ContractError(
            "CAPTURE_MAPPING: supply the supported reviewed per-file normalization contract"
        )
    review = configuration["review"]
    if (
        configuration["review_authority"]["kind"] != "human"
        or review["state"] != "approved"
        or configuration["review_authority"]["id"] not in review["reviewers"]
        or not review["rationale"]
        or not review["reviewed_at"]
    ):
        raise ContractError(
            "CAPTURE_MAPPING_REVIEW: human review must approve the file-to-mapping selections"
        )
    selections = {
        item["file_id"]: item["mapping"] for item in configuration["mappings"]
    }
    available = {item["file_id"]: item for item in files}
    if len(selections) != len(configuration["mappings"]) or any(
        file_id not in available or available[file_id]["media_type"] != "text/csv"
        for file_id in selections
    ):
        raise ContractError(
            "CAPTURE_MAPPING_SELECTION: select each currently captured CSV provider identity once; review missing inputs separately"
        )
    for mapping in selections.values():
        validate_mapping(mapping)
    return selections, configuration


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
                mappings, configuration = reviewed_mappings(metadata, manifest["files"])
                units, states, transforms = {}, [], []
                occurrences = 0
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
                        MappedLedgerCSVAdapter()
                        if item["file_id"] in mappings
                        else LedgerCSVAdapter()
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
                            **(
                                {"ledger_mapping": mappings[item["file_id"]]}
                                if item["file_id"] in mappings
                                else {}
                            ),
                        },
                    )
                    for unit in bundle.units:
                        occurrences += 1
                        if (
                            configuration is not None
                            and occurrences > self.limits["units"]
                            or unit.identity not in units
                            and len(units) >= self.limits["units"]
                        ):
                            raise ContractError(
                                "CAPTURE_BUDGET: normalization exceeds the bounded unit/occurrence inventory"
                            )
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
                            if configuration is not None:
                                previous.metadata["provider_occurrences"].append(
                                    deepcopy(details)
                                )
                            continue
                        if configuration is not None:
                            # Each overlapping occurrence retains its own exact
                            # provider revision, member checksum and raw span.
                            details["provider_occurrences"] = [deepcopy(details)]
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
                extra = {}
                if configuration is not None:
                    revision = "sha256:" + digest_bytes(canonical_json(configuration))
                    extra = {
                        "normalization_configuration": configuration,
                        "normalization_revision": revision,
                    }
                    transforms.insert(
                        0,
                        {
                            "name": "reviewed-drive-normalization",
                            "version": "1.0.0",
                            "parameters": {
                                "configuration": configuration,
                                "revision": revision,
                            },
                        },
                    )
                return NormalizedBundle(
                    tuple(units.values()),
                    tuple(transforms),
                    {
                        "provider": manifest["provider"],
                        "captured_scope": manifest["scope"],
                        "normalization_states": states,
                        "unavailable_previous": manifest["unavailable_previous"],
                        **extra,
                    },
                )
        except ContractError:
            raise
        except (BadZipFile, KeyError, TypeError, ValueError, OSError) as error:
            raise ContractError(
                "CAPTURE_PACKAGE: captured manifest/membership/bytes are malformed or corrupted"
            ) from error
