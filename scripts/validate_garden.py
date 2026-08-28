#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the dependency-free Mindgarden v0 repository contract."""

from __future__ import annotations

from argparse import ArgumentParser
from datetime import date
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

FRONTMATTER_PATTERN = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^0\.[0-9]+\.[0-9]+$")

MANIFEST_REQUIRED_FIELDS = {
    "schema",
    "id",
    "title",
    "version",
    "status",
    "owners",
    "repository",
    "visibility",
    "entrypoint",
    "content_roots",
    "generated_roots",
    "private_overlay",
}

NOTE_REQUIRED_FIELDS = {
    "schema",
    "id",
    "title",
    "kind",
    "status",
    "reviewed",
    "confidence",
    "visibility",
    "owners",
    "created",
    "updated",
    "sources",
    "related",
    "supersedes",
}

NOTE_OPTIONAL_FIELDS = {"aliases", "tags"}
GARDEN_STATUSES = {"incubating", "active", "deprecated", "archived"}
NOTE_KINDS = {"map", "concept", "decision", "project", "procedure", "source", "note"}
NOTE_STATUSES = {"draft", "proposed", "reviewed", "deprecated", "archived"}
CONFIDENCE_LEVELS = {"uncertain", "low", "medium", "high"}
VISIBILITY_LEVELS = {"public", "internal", "private"}


class ContractError(ValueError):
    """Raised when a garden violates its declared contract."""


def parse_scalar(raw_value: str) -> str | bool:
    """Parse the scalar subset supported by the v0 metadata contract."""
    value = raw_value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def parse_simple_yaml(text: str, source: Path) -> dict[str, str | bool | list[str]]:
    """Parse top-level scalar fields and scalar lists without a YAML dependency."""
    metadata: dict[str, str | bool | list[str]] = {}
    active_list: str | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        if line.startswith("  - "):
            if active_list is None:
                raise ContractError(f"{source}:{line_number}: orphan list item")
            value = parse_scalar(line.removeprefix("  - "))
            if not isinstance(value, str) or not value:
                raise ContractError(f"{source}:{line_number}: list items must be strings")
            current = metadata[active_list]
            if not isinstance(current, list):
                raise ContractError(f"{source}:{line_number}: invalid list field {active_list}")
            current.append(value)
            continue

        if line.startswith(" "):
            raise ContractError(f"{source}:{line_number}: nested mappings are not supported in v0")
        if ":" not in line:
            raise ContractError(f"{source}:{line_number}: expected a key-value field")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not key or key in metadata:
            raise ContractError(f"{source}:{line_number}: invalid or duplicate field {key!r}")

        value = raw_value.strip()
        if value == "[]":
            metadata[key] = []
            active_list = None
        elif value:
            metadata[key] = parse_scalar(value)
            active_list = None
        else:
            metadata[key] = []
            active_list = key

    return metadata


def parse_manifest(path: Path) -> dict[str, str | bool | list[str]]:
    """Read a garden manifest."""
    return parse_simple_yaml(path.read_text(encoding="utf8"), path)


def parse_note(path: Path) -> dict[str, str | bool | list[str]]:
    """Read Mindgarden metadata from Markdown YAML frontmatter."""
    text = path.read_text(encoding="utf8")
    match = FRONTMATTER_PATTERN.match(text)
    if match is None:
        raise ContractError(f"{path}: missing YAML frontmatter")
    return parse_simple_yaml(match.group("body"), path)


def require_string(metadata: dict[str, object], field: str, source: Path) -> str:
    value = metadata.get(field)
    if not isinstance(value, str) or not value:
        raise ContractError(f"{source}: {field} must be a non-empty string")
    return value


def require_string_list(
    metadata: dict[str, object],
    field: str,
    source: Path,
    *,
    non_empty: bool = False,
) -> list[str]:
    value = metadata.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ContractError(f"{source}: {field} must be a list of non-empty strings")
    if non_empty and not value:
        raise ContractError(f"{source}: {field} must not be empty")
    if len(value) != len(set(value)):
        raise ContractError(f"{source}: {field} must not contain duplicates")
    return value


def require_identifier(value: str, field: str, source: Path) -> None:
    if IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ContractError(f"{source}: {field} must be a stable lowercase identifier")


def contained_path(base: Path, value: str, field: str, source: Path) -> Path:
    candidate = (base / value).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError as error:
        raise ContractError(f"{source}: {field} escapes .garden: {value}") from error
    return candidate


def validate_manifest(path: Path) -> dict[str, str | bool | list[str]]:
    metadata = parse_manifest(path)
    observed_fields = set(metadata)
    if observed_fields != MANIFEST_REQUIRED_FIELDS:
        missing = sorted(MANIFEST_REQUIRED_FIELDS - observed_fields)
        unknown = sorted(observed_fields - MANIFEST_REQUIRED_FIELDS)
        raise ContractError(f"{path}: manifest fields differ; missing={missing}, unknown={unknown}")

    if require_string(metadata, "schema", path) != "mindgarden.garden/v0":
        raise ContractError(f"{path}: unsupported garden schema")

    garden_id = require_string(metadata, "id", path)
    require_identifier(garden_id, "id", path)
    require_string(metadata, "title", path)

    version = require_string(metadata, "version", path)
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ContractError(f"{path}: v0 version must use 0.MINOR.PATCH")

    status = require_string(metadata, "status", path)
    if status not in GARDEN_STATUSES:
        raise ContractError(f"{path}: unsupported garden status {status}")

    owners = require_string_list(metadata, "owners", path, non_empty=True)
    for owner in owners:
        require_identifier(owner, "owners", path)

    repository = require_string(metadata, "repository", path)
    parsed_repository = urlparse(repository)
    if parsed_repository.scheme not in {"http", "https"} or not parsed_repository.netloc:
        raise ContractError(f"{path}: repository must be an HTTP(S) URI")

    visibility = require_string(metadata, "visibility", path)
    if visibility not in VISIBILITY_LEVELS:
        raise ContractError(f"{path}: unsupported visibility {visibility}")

    require_string(metadata, "entrypoint", path)
    require_string_list(metadata, "content_roots", path, non_empty=True)
    require_string_list(metadata, "generated_roots", path)
    require_string(metadata, "private_overlay", path)
    return metadata


def validate_note_metadata(
    metadata: dict[str, str | bool | list[str]],
    path: Path,
    garden_visibility: str,
) -> None:
    observed_fields = set(metadata)
    missing = NOTE_REQUIRED_FIELDS - observed_fields
    unknown = {
        field
        for field in observed_fields - NOTE_REQUIRED_FIELDS - NOTE_OPTIONAL_FIELDS
        if not field.startswith("x-")
    }
    if missing or unknown:
        raise ContractError(
            f"{path}: note fields differ; "
            f"missing={sorted(missing)}, unknown={sorted(unknown)}"
        )

    if require_string(metadata, "schema", path) != "mindgarden.note/v0":
        raise ContractError(f"{path}: unsupported note schema")

    note_id = require_string(metadata, "id", path)
    require_identifier(note_id, "id", path)
    require_string(metadata, "title", path)

    kind = require_string(metadata, "kind", path)
    if kind not in NOTE_KINDS:
        raise ContractError(f"{path}: unsupported note kind {kind}")

    status = require_string(metadata, "status", path)
    if status not in NOTE_STATUSES:
        raise ContractError(f"{path}: unsupported note status {status}")

    reviewed = metadata.get("reviewed")
    if not isinstance(reviewed, bool):
        raise ContractError(f"{path}: reviewed must be a boolean")
    if status in {"draft", "proposed"} and reviewed:
        raise ContractError(f"{path}: draft or proposed knowledge cannot be reviewed")
    if status == "reviewed" and not reviewed:
        raise ContractError(f"{path}: reviewed knowledge must set reviewed: true")

    confidence = require_string(metadata, "confidence", path)
    if confidence not in CONFIDENCE_LEVELS:
        raise ContractError(f"{path}: unsupported confidence {confidence}")

    visibility = require_string(metadata, "visibility", path)
    if visibility not in VISIBILITY_LEVELS:
        raise ContractError(f"{path}: unsupported visibility {visibility}")
    if garden_visibility == "public" and visibility != "public":
        raise ContractError(f"{path}: a public garden cannot commit {visibility} knowledge")

    owners = require_string_list(metadata, "owners", path, non_empty=True)
    for owner in owners:
        require_identifier(owner, "owners", path)

    created = date.fromisoformat(require_string(metadata, "created", path))
    updated = date.fromisoformat(require_string(metadata, "updated", path))
    if updated < created:
        raise ContractError(f"{path}: updated date precedes created date")

    for field in ("sources", "related", "supersedes", "aliases", "tags"):
        if field in metadata:
            values = require_string_list(metadata, field, path)
            if field in {"related", "supersedes", "tags"}:
                for value in values:
                    require_identifier(value, field, path)


def discover_note_paths(garden_root: Path, content_roots: list[str], source: Path) -> list[Path]:
    note_paths: set[Path] = set()
    for root_value in content_roots:
        content_path = contained_path(garden_root, root_value, "content_roots", source)
        if not content_path.exists():
            raise ContractError(f"{source}: content root does not exist: {root_value}")
        if content_path.is_file():
            if content_path.suffix != ".md":
                raise ContractError(f"{source}: content file must be Markdown: {root_value}")
            note_paths.add(content_path)
        else:
            note_paths.update(content_path.rglob("*.md"))
    return sorted(note_paths)


def validate_sources(path: Path, sources: list[str]) -> None:
    for source in sources:
        parsed = urlparse(source)
        if parsed.scheme in {"http", "https", "urn"}:
            continue
        source_path = (path.parent / source).resolve()
        if not source_path.exists():
            raise ContractError(f"{path}: source does not resolve: {source}")


def validate_repository(repository_root: Path) -> int:
    repository_root = repository_root.resolve()
    garden_root = repository_root / ".garden"
    manifest_path = garden_root / "garden.yaml"
    if not manifest_path.is_file():
        raise ContractError(f"{manifest_path}: missing garden manifest")

    manifest = validate_manifest(manifest_path)
    entrypoint = contained_path(
        garden_root,
        require_string(manifest, "entrypoint", manifest_path),
        "entrypoint",
        manifest_path,
    )
    if not entrypoint.is_file():
        raise ContractError(f"{manifest_path}: entrypoint does not exist")

    content_roots = require_string_list(manifest, "content_roots", manifest_path, non_empty=True)
    generated_roots = require_string_list(manifest, "generated_roots", manifest_path)
    for generated_root in generated_roots:
        contained_path(garden_root, generated_root, "generated_roots", manifest_path)
    if set(content_roots) & set(generated_roots):
        raise ContractError(f"{manifest_path}: content and generated roots overlap")

    private_overlay_value = require_string(manifest, "private_overlay", manifest_path)
    private_overlay = (garden_root / private_overlay_value).resolve()
    try:
        private_overlay.relative_to(garden_root.resolve())
    except ValueError:
        pass
    else:
        raise ContractError(f"{manifest_path}: private_overlay must live outside .garden")

    note_paths = discover_note_paths(garden_root, content_roots, manifest_path)
    if entrypoint not in note_paths:
        raise ContractError(f"{manifest_path}: entrypoint must belong to content_roots")

    notes: dict[str, tuple[Path, dict[str, str | bool | list[str]]]] = {}
    garden_visibility = require_string(manifest, "visibility", manifest_path)
    for note_path in note_paths:
        metadata = parse_note(note_path)
        validate_note_metadata(metadata, note_path, garden_visibility)
        note_id = require_string(metadata, "id", note_path)
        if note_id in notes:
            raise ContractError(
                f"{note_path}: duplicate note id {note_id}; "
                f"first seen in {notes[note_id][0]}"
            )
        notes[note_id] = (note_path, metadata)
        validate_sources(note_path, require_string_list(metadata, "sources", note_path))

    known_ids = set(notes)
    for note_id, (note_path, metadata) in notes.items():
        for field in ("related", "supersedes"):
            references = require_string_list(metadata, field, note_path)
            dangling = set(references) - known_ids
            if dangling:
                raise ContractError(f"{note_path}: dangling {field}: {sorted(dangling)}")
            if note_id in references:
                raise ContractError(f"{note_path}: {field} cannot reference its own note id")

    return len(notes)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository containing the .garden directory (default: current directory)",
    )
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    try:
        note_count = validate_repository(arguments.repository_root)
    except (ContractError, OSError, ValueError) as error:
        print(f"mindgarden validation failed: {error}", file=sys.stderr)
        return 1

    print(f"mindgarden validation passed: {note_count} note(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
