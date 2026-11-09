"""Consume the pinned Mindcap handoff as captured bytes, without provider imports."""

from ..domain.contracts import ContractRegistry, digest_bytes, strict_json
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError
from ..domain.zip_package import read_zip

MANIFEST = "CAPTURED-SOURCE.json"
CONTRACT = "urn:mindcap:captured-source-bundle:v1"


class CapturedSourceAdapter:
    adapter_id = "captured-source-bundle"
    version = "1.0.0"
    supported_inputs = frozenset({("application/vnd.mindcap.captured-source+zip", "1")})

    def normalize(self, captured, metadata):
        members = read_zip(captured)
        if MANIFEST not in members:
            raise ContractError(
                "CAPTURED_FORMAT: supported captured-source manifest required"
            )
        manifest = strict_json(members[MANIFEST])
        if (
            ContractRegistry().errors(manifest, CONTRACT)
            or manifest.get("schema") != "mindcap.captured-source-bundle/v1"
        ):
            raise ContractError(
                "CAPTURED_CONTRACT: supported explicit private handoff required"
            )
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        if (
            len(artifacts) != len(manifest["artifacts"])
            or set(artifacts) != set(members) - {MANIFEST}
            or not any(item["role"] == "raw" for item in artifacts.values())
            or sum(item["size_bytes"] for item in artifacts.values())
            > 100 * 1024 * 1024
        ):
            raise ContractError(
                "CAPTURED_MEMBERS: exact bounded payload membership required"
            )
        for path, artifact in artifacts.items():
            if (
                len(members[path]) != artifact["size_bytes"]
                or digest_bytes(members[path]) != artifact["sha256"]
            ):
                raise ContractError(
                    "CAPTURED_INTEGRITY: captured member bytes or checksum differ"
                )
        if len({unit["identity"] for unit in manifest["units"]}) != len(
            manifest["units"]
        ):
            raise ContractError("CAPTURED_IDENTITY: duplicate normalized identity")
        units = []
        for unit in manifest["units"]:
            artifact = artifacts.get(unit["member"])
            if (
                artifact is None
                or artifact["role"] != "normalized"
                or not all(
                    name in artifacts and artifacts[name]["role"] == "raw"
                    for name in unit["original_members"]
                )
            ):
                raise ContractError(
                    "CAPTURED_REFERENCE: exact normalized and raw lineage required"
                )
            units.append(
                NormalizedUnit(
                    "captured:" + manifest["source_id"] + ":" + unit["identity"],
                    members[unit["member"]],
                    unit["media_type"],
                    tuple(unit["locators"]),
                    {
                        "identity_basis": unit["identity_basis"],
                        "source_type": manifest["source_type"],
                        "original_selector": {
                            "member": unit["member"],
                            "member_sha256": artifact["sha256"],
                        },
                        "raw_members": [
                            {"member": name, "sha256": artifacts[name]["sha256"]}
                            for name in unit["original_members"]
                        ],
                    },
                )
            )
        return NormalizedBundle(
            tuple(units),
            (
                {
                    "name": "retain-captured-source-units",
                    "version": self.version,
                    "parameters": {
                        "contract": CONTRACT,
                        "producer": manifest["producer"],
                    },
                },
            ),
            {
                key: manifest[key]
                for key in (
                    "source_id",
                    "source_type",
                    "producer",
                    "captured_at",
                    "status",
                    "warnings",
                    "capabilities",
                    "previous_bundle_sha256",
                )
            },
        )
