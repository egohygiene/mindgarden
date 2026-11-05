"""Deterministic record constructors shared by ingestion and authored curation."""

from ..domain.contracts import canonical_json, digest_bytes
from ..domain.scope import LEGACY_VISIBILITY

AUTHOR = {"kind": "agent", "id": "mindgarden", "version": "0.1.0"}
UNREVIEWED = {"state": "unreviewed", "reviewers": [], "reviewed_at": None, "rationale": None}


def artifact_reference(garden: str, artifact_id: str, digest: str | None = None) -> dict:
    return {"garden": garden, "id": artifact_id, "revision": "sha256:" + digest if digest else None}


def provenance_record(garden: str, record_id: str, artifact_id: str, artifact_digest: str,
                      *, inputs: list[dict], transformations: tuple[dict, ...] | list[dict],
                      created_at: str, rights: str, origin: str | None, scope: dict) -> dict:
    return {"schema": "mindgarden.provenance/v1", "id": record_id, "garden": garden,
            "artifact": artifact_reference(garden, artifact_id, artifact_digest),
            "artifact_sha256": artifact_digest, "origin": origin,
            "inputs": list({canonical_json(item): item for item in inputs}.values()),
            "transformations": [{"order": order, **operation, "performed_by": dict(AUTHOR)}
                                for order, operation in enumerate(transformations, 1)],
            "generator": {"name": "mindgarden", "version": "0.1.0"},
            "created_at": created_at, "rights": rights, "scope": scope}


def source_record(garden: str, record_id: str, content: bytes, *, vault_id: str,
                  kind: str, metadata: dict, scope: dict, provenance: dict,
                  inputs: list[dict], identity: str) -> dict:
    content_digest = digest_bytes(content)
    return {"schema": "mindgarden.source/v1", "id": record_id, "garden": garden,
            "title": metadata["title"], "kind": kind, "status": "active",
            "visibility": LEGACY_VISIBILITY[scope["visibility"]],
            "owners": [metadata["owner"]], "authors": [dict(AUTHOR)], "review": dict(UNREVIEWED),
            "origin": metadata["origin"], "captured_at": metadata["captured_at"],
            "media_type": metadata["media_type"], "rights": metadata["rights"],
            "artifact": {"vault": {"id": vault_id, "content_id": "sha256:" + content_digest},
                         "sha256": content_digest, "size_bytes": len(content)},
            "inputs": inputs, "provenance": [artifact_reference(
                garden, provenance["id"], digest_bytes(canonical_json(provenance)))],
            "publication": "excluded", "scope": scope,
            "x-source-identity": identity, "x-source-trust": "untrusted-evidence"}
