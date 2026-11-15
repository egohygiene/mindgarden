"""Private packet currentness over explicit selected evidence, without discovery."""

from copy import deepcopy

from .contracts import ContractRegistry, canonical_json, digest_bytes
from .validation import ContractError


def packet_dependencies(request, verified, outputs):
    inputs = sorted(
        (
            {
                "evidence": deepcopy(citation),
                "metadata_sha256": digest_bytes(
                    canonical_json(
                        {
                            field: value[field]
                            for field in (
                                "source_identity",
                                "source_review",
                                "scope",
                                "origin",
                                "lineage",
                            )
                        }
                    )
                ),
            }
            for citation, value in zip(request["sources"], verified, strict=True)
        ),
        key=canonical_json,
    )
    manifest = {
        "schema": "mindgarden.packet-dependencies/v1",
        "id": request["id"],
        "scope": deepcopy(request["scope"]),
        "request_sha256": digest_bytes(canonical_json(request)),
        "inputs_sha256": digest_bytes(canonical_json(inputs)),
        "inputs": inputs,
        "outputs": outputs,
        "canonical_evidence": False,
    }
    manifest["fingerprint"] = digest_bytes(canonical_json(manifest))
    return validate_dependencies(manifest)


def validate_dependencies(manifest):
    if ContractRegistry().errors(manifest, "packet-dependencies"):
        raise ContractError(
            "PACKET_DEPENDENCIES: supply a compatible packet-dependencies.json"
        )
    payload = {key: value for key, value in manifest.items() if key != "fingerprint"}
    if (
        digest_bytes(canonical_json(payload)) != manifest["fingerprint"]
        or digest_bytes(canonical_json(manifest["inputs"])) != manifest["inputs_sha256"]
    ):
        raise ContractError(
            "PACKET_DEPENDENCIES: dependency metadata checksums differ; retain the prior bundle for inspection"
        )
    return manifest


def reconcile_packet(current, previous):
    """A supplied old manifest is comparison data, never source or authority."""
    current, previous = validate_dependencies(current), validate_dependencies(previous)
    if previous["scope"] != current["scope"]:
        raise ContractError(
            "PACKET_SCOPE: prior packet restrictions must match the current private output"
        )
    reasons = []
    if current["id"] != previous["id"]:
        reasons.append("no-matching-prior-packet")
    else:
        if current["inputs_sha256"] != previous["inputs_sha256"]:
            reasons.append("selected-evidence-changed")
        if current["request_sha256"] != previous["request_sha256"]:
            reasons.append("review-or-request-changed")
        if current["outputs"] != previous["outputs"]:
            reasons.append("calculation-or-output-changed")
    return {
        "schema": "mindgarden.packet-freshness/v1",
        "id": current["id"],
        "state": "stale" if reasons else "current",
        "reasons": reasons or ["explicit-inputs-unchanged"],
        "action": "review-and-build-new-packet"
        if reasons
        else "verify-existing-packet",
        "current_fingerprint": current["fingerprint"],
        "scope": deepcopy(current["scope"]),
        "coverage": "explicit-current-request-only",
        "prior_manifest": "comparison-data-only; not source authority or output integrity proof",
    }
