#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT
# pylint: disable=too-many-arguments,too-many-locals
# ruff: noqa: PLR0913, T201, TRY003

"""Render a Mindgarden projection with an immutable Quartz checkout."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
import json
from pathlib import Path
import shutil
import subprocess  # nosec B404
import sys
from typing import Any

# Commands use validated argument vectors and never invoke a shell.

try:
    from .publish_garden import (
        DEFAULT_OUTPUT_PATH,
        DEFAULT_PROFILE_PATH,
        load_publish_profile,
        project_garden,
    )
    from .validate_garden import ContractError
except ImportError:
    from publish_garden import (  # type: ignore[no-redef]
        DEFAULT_OUTPUT_PATH,
        DEFAULT_PROFILE_PATH,
        load_publish_profile,
        project_garden,
    )
    from validate_garden import ContractError  # type: ignore[no-redef]


DEFAULT_ENGINE_PATH = Path(".cache/mindgarden/quartz")
DEFAULT_SITE_PATH = Path(".cache/mindgarden/site")
ENGINE_MARKER = Path(".mindgarden-quartz-cache.json")
DISTINCT_CACHE_DIRECTORY_COUNT = 3
MAXIMUM_PORT = 65_535


def run_command(arguments: list[str], *, cwd: Path | None = None) -> None:
    """Run one external command without a shell."""
    print("$ " + " ".join(arguments))
    subprocess.run(arguments, cwd=cwd, check=True)  # noqa: S603  # nosec B603


def require_executable(name: str) -> None:
    """Require one executable used by the adapter."""
    if shutil.which(name) is None:
        raise ContractError(f"required executable is unavailable: {name}")


def node_major_version() -> int:
    """Read the active Node.js major version."""
    node_path = shutil.which("node")
    if node_path is None:
        raise ContractError("required executable is unavailable: node")
    result = subprocess.run(  # noqa: S603  # nosec B603
        [node_path, "--version"],
        check=True,
        capture_output=True,
        encoding="utf8",
    )
    match = result.stdout.strip().removeprefix("v").split(".", maxsplit=1)[0]
    if not match.isdecimal():
        raise ContractError(f"could not parse Node.js version: {result.stdout.strip()}")
    return int(match)


def cache_path(repository_root: Path, value: Path, label: str) -> Path:
    """Resolve an adapter cache path beneath `.cache/mindgarden/`."""
    repository = repository_root.resolve()
    candidate = value if value.is_absolute() else repository / value
    resolved = candidate.resolve()
    cache_root = (repository / ".cache" / "mindgarden").resolve()
    try:
        resolved.relative_to(cache_root)
    except ValueError as error:
        raise ContractError(f"{label} must stay beneath {cache_root}: {resolved}") from error
    if resolved == cache_root:
        raise ContractError(f"{label} must not be the shared cache root")
    return resolved


def expected_engine_marker(profile: dict[str, Any]) -> dict[str, str]:
    """Return the ownership metadata for the Quartz cache."""
    return {
        "schema": "mindgarden.quartz-cache/v0",
        "repository": str(profile["quartz_repository"]),
        "commit": str(profile["quartz_commit"]),
    }


def prepare_engine(engine_root: Path, profile: dict[str, Any]) -> None:
    """Prepare a clean, detached Quartz checkout at the configured commit."""
    expected_marker = expected_engine_marker(profile)
    marker_path = engine_root / ENGINE_MARKER
    if engine_root.exists():
        if engine_root.is_symlink() or not marker_path.is_file():
            raise ContractError(
                f"refusing to reuse unowned Quartz cache without {ENGINE_MARKER}: {engine_root}"
            )
        observed = json.loads(marker_path.read_text(encoding="utf8"))
        if observed != expected_marker:
            raise ContractError(
                "Quartz cache pin differs from the publishing profile; remove the "
                f"owned cache and retry: {engine_root}"
            )
    else:
        engine_root.parent.mkdir(parents=True, exist_ok=True)
        run_command(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                str(profile["quartz_repository"]),
                str(engine_root),
            ]
        )

    run_command(
        [
            "git",
            "fetch",
            "--depth=1",
            "origin",
            str(profile["quartz_commit"]),
        ],
        cwd=engine_root,
    )
    run_command(["git", "checkout", "--detach", "--force", "FETCH_HEAD"], cwd=engine_root)
    run_command(["git", "clean", "-ffdx"], cwd=engine_root)
    marker_path.write_text(
        json.dumps(expected_marker, indent=2, sort_keys=True) + "\n",
        encoding="utf8",
        newline="\n",
    )


def render_site(
    repository_root: Path,
    *,
    profile_path: Path,
    content_directory: Path,
    engine_directory: Path,
    output_directory: Path,
    serve: bool,
    port: int,
) -> None:
    """Project canonical notes and invoke the pinned Quartz renderer."""
    repository = repository_root.resolve()
    resolved_profile, profile = load_publish_profile(repository, profile_path)
    for executable in ("git", "node", "npm"):
        require_executable(executable)
    expected_node_major = profile["node_major"]
    observed_node_major = node_major_version()
    if observed_node_major != expected_node_major:
        raise ContractError(
            f"Quartz profile requires Node.js {expected_node_major}; observed {observed_node_major}"
        )

    content_root = cache_path(repository, content_directory, "content directory")
    engine_root = cache_path(repository, engine_directory, "engine directory")
    output_root = cache_path(repository, output_directory, "output directory")
    if len({content_root, engine_root, output_root}) != DISTINCT_CACHE_DIRECTORY_COUNT:
        raise ContractError("content, engine, and output directories must be distinct")

    project_garden(repository, content_root, profile_path)
    prepare_engine(engine_root, profile)
    configuration_path = resolved_profile.parent / "quartz.config.yaml"
    if not configuration_path.is_file() or configuration_path.is_symlink():
        raise ContractError(f"Quartz configuration must be a regular file: {configuration_path}")
    shutil.copyfile(configuration_path, engine_root / "quartz.config.yaml")

    engine_content = engine_root / "content"
    if engine_content.is_symlink():
        raise ContractError(f"Quartz content directory must not be a symlink: {engine_content}")
    if engine_content.exists():
        shutil.rmtree(engine_content)
    shutil.copytree(content_root, engine_content)

    npm_cache = repository / ".cache" / "npm"
    npm_cache.mkdir(parents=True, exist_ok=True)
    run_command(
        ["npm", "ci", "--cache", str(npm_cache), "--prefer-offline"],
        cwd=engine_root,
    )
    command = [
        "node",
        "quartz/bootstrap-cli.mjs",
        "build",
        "--directory",
        "content",
        "--output",
        str(output_root),
        "--verbose",
    ]
    if serve:
        command.extend(["--serve", "--port", str(port)])
    run_command(command, cwd=engine_root)


def build_parser() -> ArgumentParser:
    """Build the Quartz adapter command-line contract."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE_PATH)
    parser.add_argument("--content-directory", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--engine-directory", type=Path, default=DEFAULT_ENGINE_PATH)
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_SITE_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build", help="Build the static Quartz site")
    serve = commands.add_parser("serve", help="Build and serve the local Quartz preview")
    serve.add_argument("--port", type=int, default=8080)
    return parser


def run(arguments: Namespace) -> int:
    """Execute a parsed Quartz command."""
    port = arguments.port if arguments.command == "serve" else 8080
    if not 1 <= port <= MAXIMUM_PORT:
        raise ContractError("preview port must be between 1 and 65535")
    render_site(
        arguments.repository_root,
        profile_path=arguments.profile,
        content_directory=arguments.content_directory,
        engine_directory=arguments.engine_directory,
        output_directory=arguments.output_directory,
        serve=arguments.command == "serve",
        port=port,
    )
    return 0


def main() -> int:
    """Run the CLI with stable diagnostics."""
    arguments = build_parser().parse_args()
    try:
        return run(arguments)
    except (
        ContractError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Quartz rendering failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
