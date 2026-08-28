"""Deterministic, review-gated garden initialization and v0 to v1 migration."""

from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlparse

from .. import __version__
from ..domain.validation import (
    ContractError,
    discover_note_paths,
    parse_manifest,
    parse_note,
    require_string,
    require_string_list,
    validate_repository,
)

IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
V1_CONTRACTS = (
    "mindgarden.claim/v1",
    "mindgarden.garden/v1",
    "mindgarden.knowledge/v1",
    "mindgarden.migration/v1",
    "mindgarden.projection/v1",
    "mindgarden.provenance/v1",
    "mindgarden.source/v1",
    "mindgarden.synapse/v1",
)
GARDEN_DIRECTORIES = (
    "context-packs",
    "knowledge",
    "provenance",
    "publishing",
    "sources",
    "synapses",
    "templates",
)
MIGRATOR = {
    "kind": "agent",
    "id": "mindgarden-migrator",
    "version": __version__,
}
INITIALIZER_TEMPLATES = {
    "templates/knowledge.md": """# Knowledge template

`knowledge/` holds durable, human-readable understanding. A record's stable
identity, domains, topics, review state, and visibility live in its v1 metadata;
its folder is only an authoring convenience and is never the taxonomy.

Start new agent-authored knowledge as proposed, unreviewed, excluded from
publication, and private unless an explicit garden policy says otherwise.
""",
    "templates/source.md": """# Source template

`sources/` holds faithfully captured or deterministically normalized evidence.
A source is not automatically durable knowledge. Preserve its exact origin,
rights, byte hash, capture time, and provenance before drawing conclusions.

Raw captured sources are excluded from publication by default.
""",
    "templates/synapse.md": """# Synapse template

`synapses/` holds typed relationships between stable artifact identities, such
as `related`, `supersedes`, or `derived-from`. Relationships are reviewable
records; directory proximity and wiki links do not silently create them.
""",
    "templates/publishing.md": """# Publishing template

`publishing/` holds reviewed projection policy and adapter configuration.
Published sites, indexes, graphs, context packs, and agent entrypoints are
disposable views. They never replace canonical sources or knowledge.

Publication is deny-by-default and requires explicit public visibility,
approval, and eligibility.
""",
}


@dataclass(frozen=True)
class PlannedFile:
    """One immutable file in a lifecycle plan."""

    path: str
    content: bytes

    def summary(self) -> dict[str, object]:
        """Return the reviewable representation without embedding file bytes."""
        return {
            "path": self.path,
            "action": "create",
            "size_bytes": len(self.content),
            "sha256": sha256_bytes(self.content),
        }


@dataclass(frozen=True)
class FilePlan:
    """A deterministic complete-tree plan bound to its inputs and outputs."""

    operation: str
    inputs: Mapping[str, object]
    source_sha256: str | None
    files: tuple[PlannedFile, ...]

    @property
    def directories(self) -> tuple[str, ...]:
        """List every directory created by the plan."""
        values = {".garden"}
        for planned in self.files:
            path = PurePosixPath(planned.path)
            for parent in path.parents:
                if str(parent) != ".":
                    values.add(str(parent))
        return tuple(sorted(values))

    def payload(self) -> dict[str, object]:
        """Build the canonical plan payload before its digest is attached."""
        return {
            "schema": "mindgarden.file-plan/v1",
            "operation": self.operation,
            "generator": {"name": "mindgarden", "version": __version__},
            "inputs": dict(self.inputs),
            "source_sha256": self.source_sha256,
            "directories": list(self.directories),
            "files": [planned.summary() for planned in self.files],
        }

    @property
    def digest(self) -> str:
        """Return the canonical review digest for the complete plan."""
        return sha256_bytes(canonical_json(self.payload()))

    def document(self) -> dict[str, object]:
        """Return the printable plan with its digest."""
        return {**self.payload(), "plan_sha256": self.digest}


@dataclass(frozen=True)
class GardenIdentity:
    """Configuration shared by every garden identity kind."""

    garden_id: str
    title: str
    kind: str
    visibility: str
    owners: tuple[str, ...]
    canonical_uri: str
    repository: str | None
    domains: tuple[str, ...]
    topics: tuple[str, ...]

    def plan_inputs(self) -> dict[str, object]:
        """Return stable explicit and derived plan inputs."""
        return {
            "garden_id": self.garden_id,
            "title": self.title,
            "kind": self.kind,
            "visibility": self.visibility,
            "owners": list(self.owners),
            "canonical_uri": self.canonical_uri,
            "repository": self.repository,
            "domains": list(self.domains),
            "topics": list(self.topics),
        }


def canonical_json(value: object) -> bytes:
    """Serialize JSON reproducibly for storage and hashing."""
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf8")


def sha256_bytes(value: bytes) -> str:
    """Hash exact bytes with lowercase SHA-256."""
    return hashlib.sha256(value).hexdigest()


def require_identifier(value: str, field: str) -> str:
    """Require one portable stable identifier."""
    if IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ContractError(f"{field} must be a stable lowercase identifier")
    return value


def normalized_identifier(value: str, field: str) -> str:
    """Derive an identifier from a stable local value."""
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not normalized:
        raise ContractError(f"{field} cannot produce a stable garden identifier")
    return require_identifier(normalized, field)


def identifier_set(
    values: Iterable[str],
    field: str,
    *,
    default: str | None = None,
) -> tuple[str, ...]:
    """Normalize a repeatable option as a sorted unique identifier set."""
    observed = list(values)
    if not observed and default is not None:
        observed = [default]
    for value in observed:
        require_identifier(value, field)
    return tuple(sorted(set(observed)))


def require_uri(value: str, field: str, *, https_only: bool = False) -> str:
    """Require one whitespace-free absolute URI, optionally restricted to HTTPS."""
    parsed = urlparse(value)
    if not parsed.scheme or any(character.isspace() for character in value):
        raise ContractError(f"{field} must be an absolute URI")
    if https_only and (parsed.scheme != "https" or not parsed.netloc):
        raise ContractError(f"{field} must be an HTTPS URI")
    return value


def require_title(value: str) -> str:
    """Require a stable single-line title."""
    if not value.strip() or value != value.strip() or any(
        character in value for character in ("\r", "\n", "\x00")
    ):
        raise ContractError("title must be a trimmed, non-empty single line")
    return value


def repository_root(path: Path) -> Path:
    """Resolve the working repository without accepting a symlink target."""
    absolute = path.absolute()
    if absolute.is_symlink():
        raise ContractError(f"repository root must not be a symlink: {absolute}")
    if not absolute.is_dir():
        raise ContractError(f"repository root must be an existing directory: {absolute}")
    return absolute


def reject_symlinks(root: Path) -> None:
    """Reject every symlink in a canonical or staged garden tree."""
    if root.is_symlink():
        raise ContractError(f"garden path must not be a symlink: {root}")
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ContractError(f"garden tree contains a symlink: {path}")


def safe_relative_path(root: Path, value: str, field: str) -> Path:
    """Join one portable contract path without traversal or symlinks."""
    portable = PurePosixPath(value)
    if portable.is_absolute() or ".." in portable.parts or "\\" in value:
        raise ContractError(f"{field} is not a portable contained path: {value}")
    target = root.joinpath(*portable.parts)
    current = root
    for part in portable.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ContractError(f"{field} crosses a symlink: {value}")
    return target


def source_tree_digest(root: Path) -> str:
    """Hash a tree by sorted relative paths and exact bytes."""
    reject_symlinks(root)
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def garden_manifest(
    identity: GardenIdentity,
    migrations: Sequence[dict[str, object]],
) -> dict[str, object]:
    """Build one v1 manifest shared by all identity kinds."""
    return {
        "schema": "mindgarden.garden/v1",
        "id": identity.garden_id,
        "title": identity.title,
        "version": "1.0.0",
        "kind": identity.kind,
        "status": "incubating",
        "visibility": identity.visibility,
        "owners": list(identity.owners),
        "canonical_uri": identity.canonical_uri,
        "repository": identity.repository,
        "classification": {
            "domains": list(identity.domains),
            "topics": list(identity.topics),
        },
        "contracts": {"reads": list(V1_CONTRACTS), "writes": list(V1_CONTRACTS)},
        "roots": {
            "sources": "sources",
            "knowledge": "knowledge",
            "provenance": "provenance",
            "context_packs": "context-packs",
            "generated": [".generated"],
        },
        "private_overlay": "../.garden.local",
        "publication": {
            "default_action": "deny",
            "allowed_visibilities": ["public"],
            "required_review_states": ["approved"],
            "raw_sources": "exclude",
            "allow": {"kinds": [], "domains": [], "topics": []},
        },
        "routing": {
            "domains": list(identity.domains),
            "topics": list(identity.topics),
            "private_fallback": None,
        },
        "migrations": list(migrations),
    }


def base_files(identity: GardenIdentity) -> dict[str, bytes]:
    """Render the deterministic, initially empty garden skeleton."""
    files = {
        ".garden/.gitignore": b"# Disposable projections\n.generated/\n",
        ".garden/README.md": (
            "# Garden roles\n\n"
            "This is a Mindgarden v1 canonical tree. `sources/` preserves evidence; "
            "`knowledge/` stores durable understanding; `synapses/` records typed "
            "relationships; and `publishing/` governs disposable projections.\n\n"
            "Domains and topics in metadata are authoritative. Folder placement is "
            "only an authoring convenience and never defines the taxonomy. Private "
            "overlays live at `../.garden.local`, outside this committed tree.\n"
        ).encode("utf8"),
        ".garden/garden.json": canonical_json(garden_manifest(identity, [])),
        ".garden/home.md": (
            f"# {identity.title}\n\n"
            "This map starts empty. Add reviewed durable records under `knowledge/` "
            "and connect them with typed records under `synapses/`.\n"
        ).encode("utf8"),
    }
    for directory in GARDEN_DIRECTORIES:
        if directory != "templates":
            files[f".garden/{directory}/.gitkeep"] = b""
    for path, content in INITIALIZER_TEMPLATES.items():
        files[f".garden/{path}"] = content.encode("utf8")
    return files


def planned_files(files: Mapping[str, bytes]) -> tuple[PlannedFile, ...]:
    """Validate and order a complete file mapping."""
    planned = []
    for path, content in sorted(files.items()):
        portable = PurePosixPath(path)
        if portable.is_absolute() or ".." in portable.parts or "\\" in path:
            raise ContractError(f"planned path is not portable and contained: {path}")
        if not portable.parts or portable.parts[0] != ".garden":
            raise ContractError(f"planned path must remain under .garden: {path}")
        planned.append(PlannedFile(path, content))
    return tuple(planned)


def build_init_plan(identity: GardenIdentity) -> FilePlan:
    """Build the complete deterministic initialization plan."""
    return FilePlan(
        operation="init",
        inputs=identity.plan_inputs(),
        source_sha256=None,
        files=planned_files(base_files(identity)),
    )


def unreviewed_review(reviewed: bool) -> dict[str, object]:
    """Preserve a v0 review flag without inventing reviewer authority."""
    if reviewed:
        return {
            "state": "in-review",
            "reviewers": [],
            "reviewed_at": None,
            "rationale": (
                "v0 recorded reviewed: true; reviewer identity and review time "
                "were unavailable."
            ),
        }
    return {
        "state": "unreviewed",
        "reviewers": [],
        "reviewed_at": None,
        "rationale": None,
    }


def artifact_reference(
    garden: str,
    artifact_id: str,
    digest: str | None = None,
) -> dict[str, object]:
    """Build one stable artifact reference."""
    return {
        "garden": garden,
        "id": artifact_id,
        "revision": f"sha256:{digest}" if digest is not None else None,
    }


def timestamp_for_date(value: str) -> str:
    """Represent a preserved v0 date deterministically at UTC day precision."""
    return f"{value}T00:00:00Z"


def migration_provenance(
    *,
    garden_id: str,
    record_id: str,
    artifact_id: str,
    artifact_digest: str,
    created_at: str,
    origin: str | None,
    inputs: Sequence[dict[str, object]],
    transformations: Sequence[dict[str, object]],
    rights: str,
) -> dict[str, object]:
    """Build ordered v1 provenance from observed migration evidence."""
    return {
        "schema": "mindgarden.provenance/v1",
        "id": record_id,
        "garden": garden_id,
        "artifact": artifact_reference(garden_id, artifact_id, artifact_digest),
        "artifact_sha256": artifact_digest,
        "origin": origin,
        "inputs": list(inputs),
        "transformations": list(transformations),
        "generator": {"name": "mindgarden-migrator", "version": __version__},
        "created_at": created_at,
        "rights": rights,
    }


def migration_transformation(name: str, parameters: Mapping[str, object]) -> dict[str, object]:
    """Describe one deterministic migration transformation."""
    return {
        "order": 1,
        "name": name,
        "version": "1",
        "parameters": dict(parameters),
        "performed_by": MIGRATOR,
    }


def v0_extensions(metadata: Mapping[str, object]) -> dict[str, object]:
    """Carry forward valid v0 extension fields unchanged."""
    return {key: value for key, value in metadata.items() if key.startswith("x-")}


def migrate_identity(
    manifest: Mapping[str, object],
    domains: Iterable[str],
    topics: Iterable[str],
) -> GardenIdentity:
    """Preserve a v0 garden identity while adding explicit v1 configuration."""
    garden_id = require_string(manifest, "id", Path(".garden/garden.yaml"))
    return GardenIdentity(
        garden_id=garden_id,
        title=require_string(manifest, "title", Path(".garden/garden.yaml")),
        kind="repository",
        visibility=require_string(manifest, "visibility", Path(".garden/garden.yaml")),
        owners=tuple(
            require_string_list(
                manifest,
                "owners",
                Path(".garden/garden.yaml"),
                non_empty=True,
            )
        ),
        canonical_uri=f"urn:mindgarden:garden:{garden_id}",
        repository=require_string(manifest, "repository", Path(".garden/garden.yaml")),
        domains=identifier_set(domains, "domain", default="general"),
        topics=identifier_set(topics, "topic"),
    )


def v0_provenance_by_note(
    garden_root: Path,
    manifest: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    """Load validated v0 provenance records by source-note identity."""
    root_value = require_string(manifest, "provenance_root", garden_root / "garden.yaml")
    root = safe_relative_path(garden_root, root_value, "provenance_root")
    records: dict[str, dict[str, object]] = {}
    for path in sorted(root.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf8"))
        if not isinstance(value, dict) or not isinstance(value.get("noteId"), str):
            raise ContractError(f"{path}: invalid validated v0 provenance record")
        records[str(value["noteId"])] = value
    return records


def source_v1_records(
    *,
    identity: GardenIdentity,
    note_path: Path,
    metadata: Mapping[str, object],
    v0_record: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object], bytes]:
    """Map one validated v0 source note and provenance record to v1."""
    source_id = require_string(metadata, "id", note_path)
    content = note_path.read_bytes()
    content_digest = sha256_bytes(content)
    captured = require_string(v0_record, "captured", note_path)
    transformations_value = v0_record.get("transformations")
    if not isinstance(transformations_value, list):
        raise ContractError(f"{note_path}: v0 transformations must be a list")
    transformations = []
    for order, value in enumerate(transformations_value, start=1):
        if not isinstance(value, str) or not value:
            raise ContractError(f"{note_path}: invalid v0 transformation")
        transformation_name = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        transformations.append(
            {
                "order": order,
                "name": transformation_name or "v0-transformation",
                "version": "v0",
                "parameters": {"v0_value": value},
                "performed_by": MIGRATOR,
            }
        )
    provenance_id = f"provenance-{source_id}"
    provenance = migration_provenance(
        garden_id=identity.garden_id,
        record_id=provenance_id,
        artifact_id=source_id,
        artifact_digest=content_digest,
        created_at=timestamp_for_date(captured),
        origin=require_string(v0_record, "origin", note_path),
        inputs=[],
        transformations=transformations,
        rights=require_string(v0_record, "rights", note_path),
    )
    provenance_digest = sha256_bytes(canonical_json(provenance))
    status = require_string(metadata, "status", note_path)
    source = {
        "schema": "mindgarden.source/v1",
        "id": source_id,
        "garden": identity.garden_id,
        "title": require_string(metadata, "title", note_path),
        "kind": "captured",
        "status": (
            "proposed"
            if status in {"draft", "proposed"}
            else status.replace("reviewed", "active")
        ),
        "visibility": require_string(metadata, "visibility", note_path),
        "owners": require_string_list(metadata, "owners", note_path, non_empty=True),
        "authors": [MIGRATOR],
        "review": unreviewed_review(bool(metadata.get("reviewed"))),
        "origin": require_string(v0_record, "origin", note_path),
        "captured_at": timestamp_for_date(captured),
        "media_type": "text/markdown",
        "rights": require_string(v0_record, "rights", note_path),
        "artifact": {
            "path": f"sources/{source_id}.md",
            "size_bytes": len(content),
            "sha256": content_digest,
        },
        "inputs": [],
        "provenance": [artifact_reference(identity.garden_id, provenance_id, provenance_digest)],
        "publication": "excluded",
        "x-v0-kind": "source",
        "x-v0-content-sha256": require_string(
            v0_record,
            "contentSha256",
            note_path,
        ),
        "x-v0-generator": require_string(v0_record, "generator", note_path),
        "x-v0-media-type": require_string(v0_record, "mediaType", note_path),
        "x-v0-path": note_path.name,
        "x-v0-reviewed": bool(metadata.get("reviewed")),
        **v0_extensions(metadata),
    }
    return source, provenance, content


def knowledge_v1_records(
    *,
    identity: GardenIdentity,
    note_path: Path,
    metadata: Mapping[str, object],
    source_paths: Mapping[Path, tuple[str, str]],
) -> tuple[dict[str, object], dict[str, object], bytes, list[str]]:
    """Map one validated v0 knowledge note to v1 plus observed provenance."""
    note_id = require_string(metadata, "id", note_path)
    content = note_path.read_bytes()
    content_digest = sha256_bytes(content)
    updated = require_string(metadata, "updated", note_path)
    provenance_id = f"provenance-{note_id}"
    provenance = migration_provenance(
        garden_id=identity.garden_id,
        record_id=provenance_id,
        artifact_id=note_id,
        artifact_digest=content_digest,
        created_at=timestamp_for_date(updated),
        origin=None,
        inputs=[
            {
                "artifact": artifact_reference(identity.garden_id, note_id, content_digest),
                "sha256": content_digest,
                "role": "previous-version",
            }
        ],
        transformations=[
            migration_transformation(
                "preserve-v0-note",
                {"v0_path": note_path.name, "content_changed": False},
            )
        ],
        rights="Preserved v0 knowledge; original repository rights remain authoritative.",
    )
    provenance_digest = sha256_bytes(canonical_json(provenance))
    verified_sources = []
    deferred_sources = []
    for value in require_string_list(metadata, "sources", note_path):
        candidate = (note_path.parent / value).resolve()
        matched = source_paths.get(candidate)
        if matched is None:
            deferred_sources.append(value)
            continue
        source_id, source_digest = matched
        verified_sources.append(
            {
                "source": artifact_reference(
                    identity.garden_id,
                    source_id,
                    source_digest,
                ),
                "locator": "artifact",
                "content_sha256": source_digest,
            }
        )

    status = require_string(metadata, "status", note_path)
    mapped_status = (
        "proposed"
        if status in {"draft", "proposed"}
        else status.replace("reviewed", "active")
    )
    kind = require_string(metadata, "kind", note_path)
    if kind not in {"map", "concept", "decision", "project", "procedure", "note"}:
        kind = "note"
    knowledge = {
        "schema": "mindgarden.knowledge/v1",
        "id": note_id,
        "garden": identity.garden_id,
        "title": require_string(metadata, "title", note_path),
        "kind": kind,
        "status": mapped_status,
        "confidence": require_string(metadata, "confidence", note_path).replace(
            "uncertain",
            "unknown",
        ),
        "visibility": require_string(metadata, "visibility", note_path),
        "owners": require_string_list(metadata, "owners", note_path, non_empty=True),
        "authors": [MIGRATOR],
        "review": unreviewed_review(bool(metadata.get("reviewed"))),
        "created": require_string(metadata, "created", note_path),
        "updated": updated,
        "domains": list(identity.domains),
        "topics": list(identity.topics),
        "aliases": (
            require_string_list(metadata, "aliases", note_path)
            if "aliases" in metadata
            else []
        ),
        "tags": (
            require_string_list(metadata, "tags", note_path)
            if "tags" in metadata
            else []
        ),
        "content": {"path": f"knowledge/{note_id}.md", "sha256": content_digest},
        "sources": verified_sources,
        "claims": [],
        "synapses": [],
        "provenance": [
            artifact_reference(identity.garden_id, provenance_id, provenance_digest)
        ],
        "supersedes": [
            artifact_reference(identity.garden_id, target)
            for target in require_string_list(metadata, "supersedes", note_path)
        ],
        "publication": "excluded",
        "x-v0-kind": require_string(metadata, "kind", note_path),
        "x-v0-path": note_path.name,
        "x-v0-reviewed": bool(metadata.get("reviewed")),
        **v0_extensions(metadata),
    }
    if deferred_sources:
        knowledge["x-v0-deferred-sources"] = deferred_sources
    return knowledge, provenance, content, deferred_sources


def synapse_v1(
    identity: GardenIdentity,
    source_id: str,
    target_id: str,
    relationship: str,
    visibility: str,
) -> dict[str, object]:
    """Create one typed, unreviewed relationship without promoting authority."""
    synapse_id = f"{source_id}-{relationship}-{target_id}"
    return {
        "schema": "mindgarden.synapse/v1",
        "id": synapse_id,
        "garden": identity.garden_id,
        "type": relationship,
        "source": artifact_reference(identity.garden_id, source_id),
        "target": artifact_reference(identity.garden_id, target_id),
        "directed": relationship == "supersedes",
        "status": "proposed",
        "confidence": "unknown",
        "visibility": visibility,
        "owners": list(identity.owners),
        "authors": [MIGRATOR],
        "review": unreviewed_review(False),
        "evidence": [],
        "x-v0-relationship": True,
    }


def build_migration_plan(root: Path, domains: Iterable[str], topics: Iterable[str]) -> FilePlan:
    """Build a complete v1 tree from validated, unchanged v0 input."""
    canonical = root / ".garden"
    reject_symlinks(canonical)
    validate_repository(root)
    manifest_path = canonical / "garden.yaml"
    manifest = parse_manifest(manifest_path)
    identity = migrate_identity(manifest, domains, topics)
    source_digest = source_tree_digest(canonical)
    note_paths = discover_note_paths(
        canonical,
        require_string_list(manifest, "content_roots", manifest_path, non_empty=True),
        manifest_path,
    )
    notes = [(path, parse_note(path)) for path in note_paths]
    v0_provenance = v0_provenance_by_note(canonical, manifest)
    source_paths: dict[Path, tuple[str, str]] = {}
    for path, metadata in notes:
        if metadata.get("kind") == "source":
            source_paths[path.resolve()] = (
                require_string(metadata, "id", path),
                sha256_bytes(path.read_bytes()),
            )

    files = base_files(identity)
    mappings: list[dict[str, object]] = []
    preserved_ids = []
    max_updated = "1970-01-01"
    knowledge_records: dict[str, dict[str, object]] = {}
    for path, metadata in notes:
        note_id = require_string(metadata, "id", path)
        preserved_ids.append(note_id)
        max_updated = max(max_updated, require_string(metadata, "updated", path))
        revision = sha256_bytes(path.read_bytes())
        mappings.append(
            {
                "kind": "preserve",
                "from": [artifact_reference(identity.garden_id, note_id, revision)],
                "to": [artifact_reference(identity.garden_id, note_id)],
                "reason": "Stable identity and exact content bytes are preserved.",
            }
        )
        if metadata.get("kind") == "source":
            source, provenance, content = source_v1_records(
                identity=identity,
                note_path=path,
                metadata=metadata,
                v0_record=v0_provenance[note_id],
            )
            files[f".garden/sources/{note_id}.md"] = content
            files[f".garden/sources/{note_id}.json"] = canonical_json(source)
            files[f".garden/provenance/provenance-{note_id}.json"] = canonical_json(provenance)
            continue

        knowledge, provenance, content, deferred = knowledge_v1_records(
            identity=identity,
            note_path=path,
            metadata=metadata,
            source_paths=source_paths,
        )
        knowledge_records[note_id] = knowledge
        files[f".garden/knowledge/{note_id}.md"] = content
        files[f".garden/provenance/provenance-{note_id}.json"] = canonical_json(provenance)
        for value in deferred:
            mappings.append(
                {
                    "kind": "defer",
                    "from": [artifact_reference(identity.garden_id, note_id, revision)],
                    "to": [],
                    "reason": f"v0 source locator could not be verified mechanically: {value}",
                }
            )

    for path, metadata in notes:
        source_id = require_string(metadata, "id", path)
        references: list[dict[str, object]] = []
        for relationship in ("related", "supersedes"):
            for target_id in require_string_list(metadata, relationship, path):
                synapse = synapse_v1(
                    identity,
                    source_id,
                    target_id,
                    relationship,
                    require_string(metadata, "visibility", path),
                )
                synapse_id = str(synapse["id"])
                files[f".garden/synapses/{synapse_id}.json"] = canonical_json(synapse)
                references.append(artifact_reference(identity.garden_id, synapse_id))
        if source_id in knowledge_records:
            knowledge_records[source_id]["synapses"] = references

    for note_id, knowledge in knowledge_records.items():
        files[f".garden/knowledge/{note_id}.json"] = canonical_json(knowledge)

    history_seed = {
        "generator": __version__,
        "inputs": identity.plan_inputs(),
        "source_sha256": source_digest,
    }
    history_digest = sha256_bytes(canonical_json(history_seed))
    migration_id = "migration-v0-v1"
    migration = {
        "schema": "mindgarden.migration/v1",
        "id": migration_id,
        "garden": identity.garden_id,
        "from_contract": "mindgarden.note/v0",
        "to_contract": "mindgarden.knowledge/v1",
        "status": "applied",
        "plan_sha256": history_digest,
        "created_at": timestamp_for_date(max_updated),
        "applied_at": timestamp_for_date(max_updated),
        "preserved_ids": sorted(preserved_ids),
        "mappings": mappings,
        "provenance": artifact_reference(
            identity.garden_id,
            "provenance-migration-v0-v1",
        ),
        "x-timestamp-precision": "v0-date",
    }
    migration_content = canonical_json(migration)
    migration_digest = sha256_bytes(migration_content)
    manifest_digest = sha256_bytes(manifest_path.read_bytes())
    migration_provenance_record = migration_provenance(
        garden_id=identity.garden_id,
        record_id="provenance-migration-v0-v1",
        artifact_id=migration_id,
        artifact_digest=migration_digest,
        created_at=timestamp_for_date(max_updated),
        origin=None,
        inputs=[
            {
                "artifact": artifact_reference(
                    identity.garden_id,
                    identity.garden_id,
                    manifest_digest,
                ),
                "sha256": manifest_digest,
                "role": "configuration",
            }
        ],
        transformations=[
            migration_transformation(
                "migrate-v0-v1",
                {"source_sha256": source_digest, "content_changed": False},
            )
        ],
        rights="Migration history for preserved v0 knowledge.",
    )
    files[".garden/migrations/migration-v0-v1.json"] = migration_content
    files[".garden/provenance/provenance-migration-v0-v1.json"] = canonical_json(
        migration_provenance_record
    )
    manifest_v1 = garden_manifest(
        identity,
        [artifact_reference(identity.garden_id, migration_id, migration_digest)],
    )
    manifest_v1["status"] = require_string(manifest, "status", manifest_path)
    manifest_v1["x-v0-entrypoint"] = require_string(manifest, "entrypoint", manifest_path)
    manifest_v1["x-v0-version"] = require_string(manifest, "version", manifest_path)
    files[".garden/garden.json"] = canonical_json(manifest_v1)
    files[".garden/ROLLBACK.md"] = (
        "# Rollback\n\n"
        "The untouched v0 canonical tree is retained at `../.garden.v0`. To roll "
        "back, review both trees, move the v1 tree aside, and atomically rename "
        "`.garden.v0` back to `.garden`. Never merge the two trees in place.\n"
    ).encode("utf8")
    files.pop(".garden/home.md", None)
    return FilePlan(
        operation="migrate-v0-v1",
        inputs=identity.plan_inputs(),
        source_sha256=source_digest,
        files=planned_files(files),
    )


def write_staged_tree(root: Path, plan: FilePlan) -> Path:
    """Write and fsync a complete plan into a private sibling staging tree."""
    stage = Path(tempfile.mkdtemp(prefix=".mindgarden-stage-", dir=root))
    try:
        for planned in plan.files:
            relative = PurePosixPath(planned.path)
            target = stage.joinpath(*relative.parts[1:])
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(planned.content)
                stream.flush()
                os.fsync(stream.fileno())
        check_v1_tree(stage)
    except Exception:
        shutil.rmtree(stage)
        raise
    return stage


def expected_file_map(plan: FilePlan) -> dict[str, bytes]:
    """Index planned content relative to the garden root."""
    return {
        str(PurePosixPath(planned.path).relative_to(".garden")): planned.content
        for planned in plan.files
    }


def check_plan_files(garden: Path, plan: FilePlan) -> None:
    """Verify that every planned baseline file exists with exact bytes."""
    reject_symlinks(garden)
    for relative, expected in expected_file_map(plan).items():
        path = safe_relative_path(garden, relative, "planned file")
        if not path.is_file():
            raise ContractError(f"planned file is missing: .garden/{relative}")
        if path.read_bytes() != expected:
            raise ContractError(f"planned file conflicts: .garden/{relative}")


def load_json_object(path: Path) -> dict[str, object]:
    """Load a JSON object with a stable contract diagnostic."""
    value = json.loads(path.read_text(encoding="utf8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path}: expected a JSON object")
    return value


def check_v1_tree(garden: Path) -> int:
    """Check lifecycle-produced v1 layout and byte integrity.

    This deliberately checks only issue #7's initialization and migration
    invariants. The hardened, general v1 validator remains issue #10.
    """
    reject_symlinks(garden)
    manifest_path = garden / "garden.json"
    if not manifest_path.is_file():
        raise ContractError(f"{manifest_path}: missing v1 garden manifest")
    manifest = load_json_object(manifest_path)
    if manifest.get("schema") != "mindgarden.garden/v1":
        raise ContractError(f"{manifest_path}: unsupported garden schema")
    garden_id = manifest.get("id")
    if not isinstance(garden_id, str):
        raise ContractError(f"{manifest_path}: id must be a string")
    require_identifier(garden_id, "garden id")
    roots = manifest.get("roots")
    if not isinstance(roots, dict):
        raise ContractError(f"{manifest_path}: roots must be an object")
    for field in ("sources", "knowledge", "provenance", "context_packs"):
        value = roots.get(field)
        if not isinstance(value, str):
            raise ContractError(f"{manifest_path}: roots.{field} must be a string")
        target = safe_relative_path(garden, value, f"roots.{field}")
        if not target.is_dir():
            raise ContractError(f"{manifest_path}: roots.{field} does not exist")
    overlay = manifest.get("private_overlay")
    if overlay is not None and (
        not isinstance(overlay, str)
        or not overlay.startswith("../")
        or ".." in PurePosixPath(overlay).parts[1:]
    ):
        raise ContractError(f"{manifest_path}: private overlay must remain outside .garden")

    records = 0
    artifacts: dict[tuple[str, str], str] = {}
    for path in sorted(garden.rglob("*.json")):
        value = load_json_object(path)
        schema = value.get("schema")
        visibility = value.get("visibility")
        if manifest.get("visibility") == "public" and visibility not in {None, "public"}:
            raise ContractError(f"{path}: public garden contains {visibility} committed content")
        if schema == "mindgarden.knowledge/v1":
            content = value.get("content")
            if not isinstance(content, dict):
                raise ContractError(f"{path}: knowledge content must be an object")
            content_path = content.get("path")
            digest = content.get("sha256")
            if not isinstance(content_path, str) or not isinstance(digest, str):
                raise ContractError(f"{path}: invalid knowledge content reference")
            artifact = safe_relative_path(garden, content_path, "knowledge content")
            if not artifact.is_file() or sha256_bytes(artifact.read_bytes()) != digest:
                raise ContractError(f"{path}: knowledge content hash does not match")
            artifact_id = value.get("id")
            if isinstance(artifact_id, str):
                artifacts[(garden_id, artifact_id)] = digest
            records += 1
        elif schema == "mindgarden.source/v1":
            artifact_value = value.get("artifact")
            if not isinstance(artifact_value, dict):
                raise ContractError(f"{path}: source artifact must be an object")
            artifact_path = artifact_value.get("path")
            digest = artifact_value.get("sha256")
            if not isinstance(artifact_path, str) or not isinstance(digest, str):
                raise ContractError(f"{path}: invalid source artifact reference")
            artifact = safe_relative_path(garden, artifact_path, "source artifact")
            if not artifact.is_file() or sha256_bytes(artifact.read_bytes()) != digest:
                raise ContractError(f"{path}: source artifact hash does not match")
            artifact_id = value.get("id")
            if isinstance(artifact_id, str):
                artifacts[(garden_id, artifact_id)] = digest
            records += 1

    for path in sorted((garden / "provenance").glob("*.json")):
        value = load_json_object(path)
        if value.get("schema") != "mindgarden.provenance/v1":
            raise ContractError(f"{path}: unsupported provenance schema")
        artifact = value.get("artifact")
        digest = value.get("artifact_sha256")
        if not isinstance(artifact, dict) or not isinstance(digest, str):
            raise ContractError(f"{path}: invalid provenance artifact reference")
        key = (str(artifact.get("garden")), str(artifact.get("id")))
        expected = artifacts.get(key)
        if expected is not None and expected != digest:
            raise ContractError(f"{path}: provenance artifact hash does not match")
    return records


def require_plan_digest(value: str | None, expected: str) -> None:
    """Require an explicit exact reviewed plan digest for mutation."""
    if value is None:
        raise ContractError("--plan-digest is required with --apply")
    if SHA256_PATTERN.fullmatch(value) is None:
        raise ContractError("--plan-digest must be a lowercase SHA-256")
    if value != expected:
        raise ContractError(
            f"reviewed plan digest does not match current inputs: expected {expected}"
        )


def apply_init(root: Path, plan: FilePlan) -> bool:
    """Atomically initialize a garden or verify an idempotent rerun."""
    target = root / ".garden"
    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_dir():
            raise ContractError(f"refusing conflicting garden path: {target}")
        check_plan_files(target, plan)
        check_v1_tree(target)
        return False
    stage = write_staged_tree(root, plan)
    try:
        os.replace(stage, target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return True


def apply_migration(root: Path, plan: FilePlan) -> bool:
    """Stage v1, preserve v0, and atomically select the new canonical tree."""
    target = root / ".garden"
    backup = root / ".garden.v0"
    if (target / "garden.json").is_file():
        check_v1_tree(target)
        if backup.is_dir():
            return False
        raise ContractError("v1 garden exists without the required .garden.v0 rollback tree")
    if backup.exists() or backup.is_symlink():
        raise ContractError(f"refusing conflicting migration backup: {backup}")
    stage = write_staged_tree(root, plan)
    moved_source = False
    try:
        os.replace(target, backup)
        moved_source = True
        os.replace(stage, target)
    except Exception:
        if moved_source and not target.exists() and backup.exists():
            os.replace(backup, target)
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return True


def identity_from_arguments(arguments: Namespace, root: Path) -> GardenIdentity:
    """Build deterministic init configuration from explicit options and stable defaults."""
    if arguments.visibility is None:
        raise ContractError("--visibility is required unless --check is used")
    garden_id = arguments.garden_id or normalized_identifier(root.name, "repository name")
    require_identifier(garden_id, "garden id")
    owners = identifier_set(arguments.owner, "owner", default=garden_id)
    domains = identifier_set(arguments.domain, "domain", default="general")
    topics = identifier_set(arguments.topic, "topic")
    canonical_uri = arguments.canonical_uri or f"urn:mindgarden:garden:{garden_id}"
    require_uri(canonical_uri, "canonical URI")
    if arguments.repository_uri is not None:
        require_uri(arguments.repository_uri, "repository URI", https_only=True)
    derived_title = garden_id.replace("-", " ").title()
    if derived_title.lower().endswith(" garden"):
        default_title = derived_title
    else:
        default_title = f"{derived_title} Garden"
    return GardenIdentity(
        garden_id=garden_id,
        title=require_title(arguments.title or default_title),
        kind=arguments.kind,
        visibility=arguments.visibility,
        owners=owners,
        canonical_uri=canonical_uri,
        repository=arguments.repository_uri,
        domains=domains,
        topics=topics,
    )


def identity_from_v1_manifest(manifest: Mapping[str, object]) -> GardenIdentity:
    """Recover initializer inputs from a current v1 manifest for --check."""
    classification = manifest.get("classification")
    if not isinstance(classification, dict):
        raise ContractError(".garden/garden.json: classification must be an object")
    owners = manifest.get("owners")
    domains = classification.get("domains")
    topics = classification.get("topics")
    if not isinstance(owners, list) or not all(isinstance(value, str) for value in owners):
        raise ContractError(".garden/garden.json: owners must be strings")
    if not isinstance(domains, list) or not all(isinstance(value, str) for value in domains):
        raise ContractError(".garden/garden.json: domains must be strings")
    if not isinstance(topics, list) or not all(isinstance(value, str) for value in topics):
        raise ContractError(".garden/garden.json: topics must be strings")
    repository = manifest.get("repository")
    return GardenIdentity(
        garden_id=str(manifest.get("id")),
        title=str(manifest.get("title")),
        kind=str(manifest.get("kind")),
        visibility=str(manifest.get("visibility")),
        owners=tuple(owners),
        canonical_uri=str(manifest.get("canonical_uri")),
        repository=repository if isinstance(repository, str) else None,
        domains=tuple(domains),
        topics=tuple(topics),
    )


def print_plan(plan: FilePlan) -> None:
    """Print one stable human- and machine-readable plan."""
    print(json.dumps(plan.document(), indent=2, sort_keys=True))


def run_init(arguments: Namespace) -> int:
    """Plan, check, or apply deterministic garden initialization."""
    root = repository_root(arguments.repository_root)
    if arguments.check:
        manifest_path = root / ".garden/garden.json"
        if not manifest_path.is_file():
            raise ContractError(f"{manifest_path}: missing v1 garden manifest")
        manifest = load_json_object(manifest_path)
        plan = build_init_plan(identity_from_v1_manifest(manifest))
        check_plan_files(root / ".garden", plan)
        records = check_v1_tree(root / ".garden")
        print(f"mindgarden initialization check passed: {records} durable record(s)")
        return 0
    plan = build_init_plan(identity_from_arguments(arguments, root))
    if not arguments.apply:
        print_plan(plan)
        return 0
    require_plan_digest(arguments.plan_digest, plan.digest)
    changed = apply_init(root, plan)
    action = "applied" if changed else "already current"
    print(f"mindgarden initialization {action}: {len(plan.files)} file(s)")
    return 0


def run_migrate(arguments: Namespace) -> int:
    """Plan, check, or apply rollback-safe v0 to v1 migration."""
    root = repository_root(arguments.repository_root)
    if arguments.check:
        records = check_v1_tree(root / ".garden")
        if not (root / ".garden.v0/garden.yaml").is_file():
            raise ContractError("migration rollback tree is missing: .garden.v0")
        print(f"mindgarden migration check passed: {records} durable record(s)")
        return 0
    if (root / ".garden/garden.json").is_file():
        if arguments.apply and (root / ".garden.v0/garden.yaml").is_file():
            records = check_v1_tree(root / ".garden")
            print(f"mindgarden migration already current: {records} durable record(s)")
            return 0
        raise ContractError("garden already uses the v1 contract; run migrate --check")
    plan = build_migration_plan(root, arguments.domain, arguments.topic)
    if arguments.plan:
        print_plan(plan)
        return 0
    require_plan_digest(arguments.plan_digest, plan.digest)
    changed = apply_migration(root, plan)
    action = "applied" if changed else "already current"
    print(f"mindgarden migration {action}: {len(plan.files)} file(s)")
    return 0
