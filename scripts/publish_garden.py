#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT
# pylint: disable=too-many-arguments,too-many-locals
# ruff: noqa: PLR0913, T201, TRY003

"""Project reviewed public Mindgarden notes into a deterministic site tree."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import sys
from tempfile import TemporaryDirectory
from typing import Any
from urllib.parse import quote, unquote, urlsplit, urlunsplit

try:
    from .garden_agent import markdown_body
    from .validate_garden import (
        ContractError,
        discover_note_paths,
        parse_manifest,
        parse_note,
        parse_simple_yaml,
        require_string,
        require_string_list,
        validate_repository,
    )
except ImportError:
    from garden_agent import markdown_body  # type: ignore[no-redef]
    from validate_garden import (  # type: ignore[no-redef]
        ContractError,
        discover_note_paths,
        parse_manifest,
        parse_note,
        parse_simple_yaml,
        require_string,
        require_string_list,
        validate_repository,
    )


DEFAULT_PROFILE_PATH = Path(".garden/publishing/quartz.yaml")
DEFAULT_OUTPUT_PATH = Path(".cache/mindgarden/publish")
MARKER_PATH = Path(".mindgarden-projection.json")
PROFILE_REQUIRED_FIELDS = {
    "schema",
    "id",
    "adapter",
    "garden_root",
    "entrypoint",
    "repository",
    "repository_ref",
    "base_url",
    "quartz_repository",
    "quartz_commit",
    "node_major",
    "statuses",
    "visibilities",
}
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MINIMUM_NODE_MAJOR = 22
MARKDOWN_LINK_PATTERN = re.compile(r"(?P<prefix>!?\[[^\]\n]+\]\()(?P<target>[^)\n]+)(?P<suffix>\))")
WIKILINK_PATTERN = re.compile(r"(?P<embed>!)?\[\[(?P<value>[^\]\n]+)\]\]")
BASE_EMBED_PATTERN = re.compile(
    r"^!\[\[[^\]\n]+\.base(?:#[^\]\n]+)?\]\]\s*$",
    re.IGNORECASE | re.MULTILINE,
)
QUARTZ_FRONTMATTER = "publish: true\ndraft: false"
BASE_REPLACEMENT = (
    "> [!info] Vault-only view\n"
    "> This embedded Obsidian Base remains available in the repository vault.\n\n"
)


def canonical_json(value: object) -> str:
    """Serialize stable JSON with a final newline."""
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_bytes(value: bytes) -> str:
    """Return a lowercase SHA-256 digest."""
    return hashlib.sha256(value).hexdigest()


def contained_path(base: Path, candidate: Path, label: str) -> Path:
    """Resolve a path and require it to remain beneath the supplied base."""
    resolved_base = base.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_base)
    except ValueError as error:
        raise ContractError(f"{label} escapes {resolved_base}: {candidate}") from error
    return resolved_candidate


def resolve_repository_path(repository_root: Path, value: str, label: str) -> Path:
    """Resolve one repository-relative configuration path."""
    candidate = Path(value)
    if candidate.is_absolute():
        raise ContractError(f"{label} must be repository-relative: {value}")
    return contained_path(repository_root, repository_root / candidate, label)


def require_exact_string_list(
    metadata: dict[str, Any], field: str, expected: list[str], source: Path
) -> list[str]:
    """Read a profile list and require the fail-closed publication value."""
    observed = require_string_list(metadata, field, source, non_empty=True)
    if observed != expected:
        raise ContractError(f"{source}: {field} must be exactly {expected}")
    return observed


def load_publish_profile(  # noqa: PLR0912
    repository_root: Path,
    profile_path: Path = DEFAULT_PROFILE_PATH,
) -> tuple[Path, dict[str, Any]]:
    """Load and validate one deterministic public-publishing profile."""
    repository = repository_root.resolve()
    resolved_profile = resolve_repository_path(
        repository, profile_path.as_posix(), "publish profile"
    )
    if not resolved_profile.is_file() or resolved_profile.is_symlink():
        raise ContractError(f"publish profile must be a regular file: {resolved_profile}")

    profile: dict[str, Any] = parse_simple_yaml(
        resolved_profile.read_text(encoding="utf8"), resolved_profile
    )
    if set(profile) != PROFILE_REQUIRED_FIELDS:
        missing = sorted(PROFILE_REQUIRED_FIELDS - set(profile))
        extra = sorted(set(profile) - PROFILE_REQUIRED_FIELDS)
        raise ContractError(
            f"{resolved_profile}: profile fields differ; missing={missing}, extra={extra}"
        )

    if require_string(profile, "schema", resolved_profile) != "mindgarden.publish-profile/v0":
        raise ContractError(f"{resolved_profile}: unsupported publish profile schema")
    profile_id = require_string(profile, "id", resolved_profile)
    if IDENTIFIER_PATTERN.fullmatch(profile_id) is None:
        raise ContractError(f"{resolved_profile}: id must be a stable lowercase identifier")
    if require_string(profile, "adapter", resolved_profile) != "quartz-v5":
        raise ContractError(f"{resolved_profile}: unsupported publishing adapter")
    if require_string(profile, "garden_root", resolved_profile) != ".garden":
        raise ContractError(f"{resolved_profile}: garden_root must be .garden")

    repository_url = require_string(profile, "repository", resolved_profile)
    parsed_repository = urlsplit(repository_url)
    if (
        parsed_repository.scheme != "https"
        or parsed_repository.netloc != "github.com"
        or not parsed_repository.path.strip("/")
    ):
        raise ContractError(f"{resolved_profile}: repository must be a GitHub HTTPS URL")
    require_string(profile, "repository_ref", resolved_profile)

    base_url = require_string(profile, "base_url", resolved_profile)
    if "://" in base_url or base_url.startswith("/") or base_url.endswith("/"):
        raise ContractError(f"{resolved_profile}: base_url must omit protocol and edge slashes")
    quartz_repository = require_string(profile, "quartz_repository", resolved_profile)
    if quartz_repository != "https://github.com/jackyzha0/quartz.git":
        raise ContractError(f"{resolved_profile}: unexpected Quartz repository")
    quartz_commit = require_string(profile, "quartz_commit", resolved_profile)
    if COMMIT_PATTERN.fullmatch(quartz_commit) is None:
        raise ContractError(f"{resolved_profile}: quartz_commit must be a full commit SHA")

    node_major = profile.get("node_major")
    if (
        not isinstance(node_major, int)
        or isinstance(node_major, bool)
        or node_major < MINIMUM_NODE_MAJOR
    ):
        raise ContractError(f"{resolved_profile}: node_major must be an integer of at least 22")
    require_exact_string_list(profile, "statuses", ["reviewed"], resolved_profile)
    require_exact_string_list(profile, "visibilities", ["public"], resolved_profile)

    manifest_path = repository / ".garden" / "garden.yaml"
    manifest: dict[str, Any] = parse_manifest(manifest_path)
    if require_string(profile, "repository", resolved_profile) != require_string(
        manifest, "repository", manifest_path
    ):
        raise ContractError(f"{resolved_profile}: repository differs from garden manifest")
    if require_string(profile, "entrypoint", resolved_profile) != require_string(
        manifest, "entrypoint", manifest_path
    ):
        raise ContractError(f"{resolved_profile}: entrypoint differs from garden manifest")

    return resolved_profile, profile


def projected_path(source_path: Path, entrypoint: Path) -> Path:
    """Map a canonical garden note to its public content path."""
    if source_path == entrypoint:
        return Path("index.md")
    if source_path.name.casefold() == "readme.md":
        return source_path.parent / "index.md"
    return source_path


def note_aliases(note_path: Path, mapped_path: Path, entrypoint: Path) -> set[str]:
    """Return the supported deterministic wikilink aliases for one note."""
    aliases = {
        note_path.with_suffix("").as_posix(),
        mapped_path.with_suffix("").as_posix(),
        note_path.stem,
    }
    if note_path.name.casefold() == "readme.md":
        aliases.add(note_path.parent.as_posix())
    if note_path == entrypoint:
        aliases.add("index")
    return {alias.removeprefix("./") for alias in aliases if alias not in {"", "."}}


def build_alias_map(
    paths: set[Path], mapped_paths: dict[Path, Path], entrypoint: Path
) -> dict[str, Path | None]:
    """Build an alias map while retaining ambiguity as an explicit failure."""
    aliases: dict[str, Path | None] = {}
    for path in sorted(paths):
        for alias in note_aliases(path, mapped_paths[path], entrypoint):
            if alias in aliases and aliases[alias] != path:
                aliases[alias] = None
            else:
                aliases[alias] = path
    return aliases


def repository_link(profile: dict[str, Any], repository_path: Path) -> str:
    """Build a stable GitHub source link for material outside the projection."""
    repository = str(profile["repository"]).rstrip("/")
    repository_ref = quote(str(profile["repository_ref"]), safe="")
    encoded_path = quote(repository_path.as_posix(), safe="/")
    return f"{repository}/blob/{repository_ref}/{encoded_path}"


def relative_projected_link(source: Path, target: Path) -> str:
    """Return a relative Markdown link between projected paths."""
    start = source.parent.as_posix()
    return posixpath.relpath(target.as_posix(), start if start != "." else ".")


def resolve_note_reference(
    raw_target: str,
    source_path: Path,
    all_notes: set[Path],
    aliases: dict[str, Path | None],
) -> Path | None:
    """Resolve one garden-relative or shortest-path note reference."""
    normalized = raw_target.removeprefix("./")
    candidate = (source_path.parent / normalized).with_suffix(".md")
    normalized_candidate = Path(os.path.normpath(candidate.as_posix()))
    if normalized_candidate in all_notes:
        return normalized_candidate

    key = normalized.removesuffix(".md")
    if key not in aliases:
        return None
    resolved = aliases[key]
    if resolved is None:
        raise ContractError(f"ambiguous wikilink target {raw_target!r} in {source_path}")
    return resolved


def rewrite_wikilinks(
    text: str,
    *,
    repository_root: Path,
    garden_root: Path,
    source_path: Path,
    mapped_source: Path,
    all_notes: set[Path],
    included_notes: set[Path],
    mapped_paths: dict[Path, Path],
    aliases: dict[str, Path | None],
    profile: dict[str, Any],
) -> str:
    """Rewrite mapped wikilinks and remove native Base embeds."""
    without_bases = BASE_EMBED_PATTERN.sub(BASE_REPLACEMENT, text)

    def replace(match: re.Match[str]) -> str:
        value = match.group("value")
        if r"\|" in value:
            target_and_heading, label = value.split(r"\|", maxsplit=1)
            separator = r"\|"
        else:
            target_and_heading, separator, label = value.partition("|")
        target, heading_separator, heading = target_and_heading.partition("#")
        target = target.strip()
        display = label.strip() if separator else ""

        if not target:
            return match.group(0)
        if target.casefold().endswith(".base"):
            base_path = contained_path(
                garden_root,
                garden_root / source_path.parent / target,
                "Obsidian Base link",
            )
            repository_path = base_path.relative_to(repository_root)
            link_label = display or Path(target).stem
            return f"[{link_label}]({repository_link(profile, repository_path)})"

        resolved = resolve_note_reference(target, source_path, all_notes, aliases)
        if resolved is None:
            raise ContractError(f"unresolved wikilink {target!r} in {source_path}")
        if resolved not in included_notes:
            raise ContractError(
                f"reviewed public note {source_path} links to excluded note {resolved}"
            )

        rewritten = relative_projected_link(
            mapped_source.with_suffix(""), mapped_paths[resolved].with_suffix("")
        )
        if heading_separator:
            rewritten = f"{rewritten}#{heading}"
        if display:
            rewritten = f"{rewritten}{separator}{display}"
        embed = "!" if match.group("embed") else ""
        return f"{embed}[[{rewritten}]]"

    return WIKILINK_PATTERN.sub(replace, without_bases)


def rewrite_markdown_links(
    text: str,
    *,
    repository_root: Path,
    garden_root: Path,
    source_path: Path,
    mapped_source: Path,
    all_note_files: dict[Path, Path],
    included_notes: set[Path],
    mapped_paths: dict[Path, Path],
    profile: dict[str, Any],
) -> str:
    """Rewrite repository links while preserving external and in-page links."""
    source_file = garden_root / source_path

    def replace(match: re.Match[str]) -> str:
        raw_value = match.group("target").strip()
        if ' "' in raw_value or " '" in raw_value:
            raise ContractError(f"Markdown link titles are unsupported in {source_path}")
        wrapped = raw_value.startswith("<") and raw_value.endswith(">")
        target = raw_value[1:-1] if wrapped else raw_value
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or target.startswith(("#", "/")):
            return match.group(0)

        decoded_path = unquote(parsed.path)
        resolved = (source_file.parent / decoded_path).resolve()
        contained_path(repository_root, resolved, "Markdown link")
        is_embed = match.group("prefix").startswith("!")

        relative_garden: Path | None
        try:
            relative_garden = resolved.relative_to(garden_root)
        except ValueError:
            relative_garden = None

        if relative_garden in all_note_files:
            note_path = all_note_files[relative_garden]
            if note_path not in included_notes:
                raise ContractError(
                    f"reviewed public note {source_path} links to excluded note {note_path}"
                )
            rewritten = relative_projected_link(mapped_source, mapped_paths[note_path])
        else:
            if is_embed:
                raise ContractError(
                    f"repository assets are not enabled for publication: {source_path} -> {target}"
                )
            rewritten = repository_link(profile, resolved.relative_to(repository_root))

        rewritten = urlunsplit(("", "", rewritten, parsed.query, parsed.fragment))
        if wrapped:
            rewritten = f"<{rewritten}>"
        return f"{match.group('prefix')}{rewritten}{match.group('suffix')}"

    return MARKDOWN_LINK_PATTERN.sub(replace, text)


def add_quartz_frontmatter(text: str, source: Path) -> str:
    """Add projection-only publication flags to canonical note frontmatter."""
    if not text.startswith("---\n"):
        raise ContractError(f"{source}: missing YAML frontmatter")
    boundary = text.find("\n---\n", 4)
    if boundary < 0:
        raise ContractError(f"{source}: malformed YAML frontmatter")
    return f"{text[:boundary]}\n{QUARTZ_FRONTMATTER}{text[boundary:]}"


def projection_marker(profile: dict[str, Any], paths: list[Path]) -> str:
    """Render the deterministic ownership marker for a disposable projection."""
    return canonical_json(
        {
            "schema": "mindgarden.projection/v0",
            "profile": profile["id"],
            "notes": [path.as_posix() for path in paths],
        }
    )


def projection_digests(root: Path) -> dict[str, str]:
    """Hash every regular projection file in stable path order."""
    return {
        path.relative_to(root).as_posix(): sha256_bytes(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def replace_owned_directory(source: Path, destination: Path) -> None:
    """Replace only a prior Mindgarden-owned projection directory."""
    if destination.is_symlink():
        raise ContractError(f"projection output must not be a symlink: {destination}")
    if destination.exists():
        marker = destination / MARKER_PATH
        if not marker.is_file():
            raise ContractError(
                f"refusing to replace unowned projection directory without {MARKER_PATH}: "
                f"{destination}"
            )
        metadata = json.loads(marker.read_text(encoding="utf8"))
        if metadata.get("schema") != "mindgarden.projection/v0":
            raise ContractError(f"invalid projection ownership marker: {marker}")
        shutil.rmtree(destination)
    source.replace(destination)


def project_garden(  # noqa: PLR0915
    repository_root: Path,
    output_directory: Path,
    profile_path: Path = DEFAULT_PROFILE_PATH,
) -> list[Path]:
    """Write the reviewed public garden projection atomically."""
    repository = repository_root.resolve()
    validate_repository(repository)
    _, profile = load_publish_profile(repository, profile_path)
    garden_root = repository / str(profile["garden_root"])
    manifest_path = garden_root / "garden.yaml"
    manifest = parse_manifest(manifest_path)
    content_roots = require_string_list(manifest, "content_roots", manifest_path, non_empty=True)
    entrypoint = Path(require_string(profile, "entrypoint", profile_path))

    all_source_files = discover_note_paths(garden_root, content_roots, manifest_path)
    all_notes: set[Path] = set()
    metadata_by_path: dict[Path, dict[str, Any]] = {}
    all_note_files: dict[Path, Path] = {}
    for source_file in all_source_files:
        if source_file.is_symlink() or not source_file.is_file():
            raise ContractError(f"garden notes must be regular files: {source_file}")
        relative = source_file.relative_to(garden_root)
        all_notes.add(relative)
        all_note_files[relative] = relative
        metadata_by_path[relative] = parse_note(source_file)

    statuses = set(require_string_list(profile, "statuses", profile_path, non_empty=True))
    visibilities = set(require_string_list(profile, "visibilities", profile_path, non_empty=True))
    included_notes = {
        path
        for path, metadata in metadata_by_path.items()
        if metadata.get("status") in statuses
        and metadata.get("visibility") in visibilities
        and metadata.get("reviewed") is True
    }
    if entrypoint not in included_notes:
        raise ContractError("published entrypoint must be a reviewed public note")

    mapped_paths = {path: projected_path(path, entrypoint) for path in all_notes}
    included_outputs = [mapped_paths[path] for path in sorted(included_notes)]
    if len(included_outputs) != len(set(included_outputs)):
        raise ContractError("published notes map to duplicate output paths")
    aliases = build_alias_map(all_notes, mapped_paths, entrypoint)

    destination = output_directory
    if not destination.is_absolute():
        destination = repository / destination
    destination = destination.resolve()
    if destination in {repository, garden_root}:
        raise ContractError(f"unsafe projection output directory: {destination}")
    try:
        destination.relative_to(garden_root)
    except ValueError:
        pass
    else:
        raise ContractError(
            f"projection output must stay outside the canonical garden: {destination}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(
        dir=destination.parent, prefix=f".{destination.name}.mindgarden-"
    ) as temporary_name:
        temporary_root = Path(temporary_name)
        for note_path in sorted(included_notes):
            source_file = garden_root / note_path
            mapped_path = mapped_paths[note_path]
            text = source_file.read_text(encoding="utf8")
            if markdown_body(text) == "":
                raise ContractError(f"published note has an empty body: {source_file}")
            text = rewrite_wikilinks(
                text,
                repository_root=repository,
                garden_root=garden_root,
                source_path=note_path,
                mapped_source=mapped_path,
                all_notes=all_notes,
                included_notes=included_notes,
                mapped_paths=mapped_paths,
                aliases=aliases,
                profile=profile,
            )
            text = rewrite_markdown_links(
                text,
                repository_root=repository,
                garden_root=garden_root,
                source_path=note_path,
                mapped_source=mapped_path,
                all_note_files=all_note_files,
                included_notes=included_notes,
                mapped_paths=mapped_paths,
                profile=profile,
            )
            rendered = add_quartz_frontmatter(text, source_file).rstrip("\n") + "\n"
            target = temporary_root / mapped_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered, encoding="utf8", newline="\n")

        (temporary_root / MARKER_PATH).write_text(
            projection_marker(profile, included_outputs), encoding="utf8", newline="\n"
        )
        replace_owned_directory(temporary_root, destination)

    return included_outputs


def verify_projection(repository_root: Path, profile_path: Path) -> int:
    """Build the projection twice and require byte-identical output."""
    repository = repository_root.resolve()
    with (
        TemporaryDirectory(prefix="mindgarden-publish-a-") as first_name,
        TemporaryDirectory(prefix="mindgarden-publish-b-") as second_name,
    ):
        first_root = Path(first_name) / "projection"
        second_root = Path(second_name) / "projection"
        first_paths = project_garden(repository, first_root, profile_path)
        second_paths = project_garden(repository, second_root, profile_path)
        first_digests = projection_digests(first_root)
        second_digests = projection_digests(second_root)
        if first_paths != second_paths or first_digests != second_digests:
            raise ContractError("public projection is not byte-deterministic")
    return len(first_paths)


def build_parser() -> ArgumentParser:
    """Build the publishing command-line contract."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE_PATH)
    commands = parser.add_subparsers(dest="command", required=True)

    project = commands.add_parser("project", help="Write the disposable public tree")
    project.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_PATH)
    commands.add_parser("verify", help="Validate and reproduce the public tree twice")
    return parser


def run(arguments: Namespace) -> int:
    """Execute a parsed publication command."""
    if arguments.command == "project":
        paths = project_garden(
            arguments.repository_root, arguments.output_directory, arguments.profile
        )
        print(f"Projected {len(paths)} reviewed public note(s) to {arguments.output_directory}.")
        return 0
    if arguments.command == "verify":
        count = verify_projection(arguments.repository_root, arguments.profile)
        print(f"Verified deterministic public projection for {count} note(s).")
        return 0
    raise ContractError(f"unsupported command: {arguments.command}")


def main() -> int:
    """Run the CLI with stable diagnostics."""
    arguments = build_parser().parse_args()
    try:
        return run(arguments)
    except (ContractError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"Mindgarden publication failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
