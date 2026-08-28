"""Stable command-line interface for the Mindgarden package."""

from __future__ import annotations

from argparse import SUPPRESS, ArgumentParser, ArgumentTypeError, Namespace
from enum import IntEnum
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Protocol, Sequence

from .. import __version__
from ..adapters import publishing, quartz
from ..application import agent, lifecycle
from ..domain.validation import ContractError, validate_repository


class ExitCode(IntEnum):
    """Stable process exit codes for machine consumers."""

    SUCCESS = 0
    USAGE = 2
    CONTRACT = 3
    IO = 4
    EXTERNAL = 5


class ParserCollection(Protocol):
    """Structural type for an argparse subparser collection."""

    def add_parser(self, name: str, **kwargs: Any) -> ArgumentParser:
        """Add and return one command parser."""
        ...


def positive_integer(value: str) -> int:
    """Parse one strictly positive command-line integer."""
    parsed = int(value)
    if parsed < 1:
        raise ArgumentTypeError("value must be a positive integer")
    return parsed


def add_repository_root(
    parser: ArgumentParser,
    *,
    suppress_default: bool = False,
) -> None:
    """Add the shared consumer-repository argument."""
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=SUPPRESS if suppress_default else Path.cwd(),
        help="Repository containing .garden (default: current directory)",
    )


def add_ingest_command(commands: ParserCollection) -> None:
    """Register deterministic source ingestion."""
    parser = commands.add_parser("ingest", help="Normalize one supplied source artifact")
    add_repository_root(parser)
    parser.add_argument("--input", type=Path, required=True, help="UTF-8 source file")
    parser.add_argument("--source-id", required=True, help="Stable source note identifier")
    parser.add_argument("--title", required=True, help="Source note title")
    parser.add_argument("--origin", required=True, help="HTTP(S) or URN source origin")
    parser.add_argument("--captured", required=True, help="Capture date in YYYY-MM-DD")
    parser.add_argument("--owner", required=True, help="Stable owner identifier")
    parser.add_argument("--rights", required=True, help="Rights or license statement")
    parser.add_argument(
        "--media-type",
        default="text/markdown",
        help="Lowercase source media type",
    )
    parser.add_argument(
        "--related",
        action="append",
        default=[],
        help="Related note identifier; repeat as needed",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Source tag; repeat as needed",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply the plan; omission is a read-only dry run",
    )
    parser.add_argument(
        "--confirm-public",
        action="store_true",
        help="Confirm the supplied source is safe for a public garden",
    )
    parser.set_defaults(handler=agent.run_ingest)


def add_lifecycle_commands(commands: ParserCollection) -> None:
    """Register deterministic initialization and v0 to v1 migration."""
    init_parser = commands.add_parser("init", help="Plan or initialize a v1 garden")
    add_repository_root(init_parser)
    init_parser.add_argument(
        "--visibility",
        choices=("public", "internal", "private"),
        help="Committed garden visibility; required unless --check is used",
    )
    init_parser.add_argument(
        "--garden-id",
        help="Stable garden identifier (default: normalized repository directory name)",
    )
    init_parser.add_argument("--title", help="Garden title (default: derived from garden id)")
    init_parser.add_argument(
        "--kind",
        choices=("repository", "personal", "organization"),
        default="repository",
        help="Garden identity kind",
    )
    init_parser.add_argument(
        "--owner",
        action="append",
        default=[],
        help="Stable owner identifier; repeat as needed",
    )
    init_parser.add_argument("--canonical-uri", help="Stable canonical garden URI")
    init_parser.add_argument("--repository-uri", help="Optional HTTPS repository URI")
    init_parser.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Authoritative domain identifier; repeat as needed",
    )
    init_parser.add_argument(
        "--topic",
        action="append",
        default=[],
        help="Authoritative topic identifier; repeat as needed",
    )
    init_mode = init_parser.add_mutually_exclusive_group()
    init_mode.add_argument("--apply", action="store_true", help="Apply a reviewed plan")
    init_mode.add_argument("--check", action="store_true", help="Check the initialized tree")
    init_parser.add_argument(
        "--plan-digest",
        help="Exact plan_sha256 emitted by the reviewed dry run",
    )
    init_parser.set_defaults(handler=lifecycle.run_init)

    migrate_parser = commands.add_parser(
        "migrate",
        help="Plan, apply, or check a v0 to v1 migration",
    )
    add_repository_root(migrate_parser)
    migrate_parser.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Authoritative v1 domain identifier; repeat as needed",
    )
    migrate_parser.add_argument(
        "--topic",
        action="append",
        default=[],
        help="Authoritative v1 topic identifier; repeat as needed",
    )
    migrate_mode = migrate_parser.add_mutually_exclusive_group(required=True)
    migrate_mode.add_argument("--plan", action="store_true", help="Print the complete plan")
    migrate_mode.add_argument("--apply", action="store_true", help="Apply a reviewed plan")
    migrate_mode.add_argument("--check", action="store_true", help="Check migrated v1 state")
    migrate_parser.add_argument(
        "--plan-digest",
        help="Exact plan_sha256 emitted by --plan",
    )
    migrate_parser.set_defaults(handler=lifecycle.run_migrate)


def add_agent_commands(commands: ParserCollection) -> None:
    """Register indexing, search, context, and verification commands."""
    index_parser = commands.add_parser("index", help="Build the deterministic catalog")
    add_repository_root(index_parser)
    index_mode = index_parser.add_mutually_exclusive_group()
    index_mode.add_argument("--write", action="store_true", help="Write the catalog")
    index_mode.add_argument("--check", action="store_true", help="Check the catalog")
    index_parser.set_defaults(handler=agent.run_index)

    search_parser = commands.add_parser("search", help="Search garden knowledge")
    add_repository_root(search_parser)
    search_parser.add_argument("--query", required=True, help="Lexical search query")
    search_parser.add_argument(
        "--limit",
        type=positive_integer,
        default=10,
        help="Maximum result count",
    )
    search_parser.add_argument(
        "--include-unreviewed",
        action="store_true",
        help="Include draft and proposed notes",
    )
    search_parser.set_defaults(handler=agent.run_search)

    context_parser = commands.add_parser("context", help="Render a context pack")
    add_repository_root(context_parser)
    context_parser.add_argument("--pack", required=True, help="Context-pack identifier")
    context_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Context serialization",
    )
    context_parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path under a declared generated root",
    )
    context_parser.set_defaults(handler=agent.run_context)

    llms_parser = commands.add_parser("llms", help="Render the llms.txt entrypoint")
    add_repository_root(llms_parser)
    llms_mode = llms_parser.add_mutually_exclusive_group()
    llms_mode.add_argument("--write", action="store_true", help="Write llms.txt")
    llms_mode.add_argument("--check", action="store_true", help="Check llms.txt")
    llms_parser.set_defaults(handler=agent.run_llms)

    verify_parser = commands.add_parser("verify", help="Verify agent projections")
    add_repository_root(verify_parser)
    verify_parser.set_defaults(handler=agent.run_verify)


def run_validation(arguments: Namespace) -> int:
    """Validate one consumer repository."""
    note_count = validate_repository(arguments.repository_root)
    print(f"mindgarden validation passed: {note_count} note(s)")
    return ExitCode.SUCCESS


def run_version(_arguments: Namespace) -> int:
    """Print the installed package version."""
    print(f"mindgarden {__version__}")
    return ExitCode.SUCCESS


def add_publish_command(commands: ParserCollection) -> None:
    """Register privacy-safe projection commands."""
    parser = commands.add_parser("publish", help="Project reviewed public knowledge")
    add_repository_root(parser)
    parser.add_argument("--profile", type=Path, default=publishing.DEFAULT_PROFILE_PATH)
    actions = parser.add_subparsers(dest="command", required=True)
    project = actions.add_parser("project", help="Write the disposable public tree")
    add_repository_root(project, suppress_default=True)
    project.add_argument(
        "--output-directory",
        type=Path,
        default=publishing.DEFAULT_OUTPUT_PATH,
    )
    verify = actions.add_parser("verify", help="Reproduce the public tree twice")
    add_repository_root(verify, suppress_default=True)
    parser.set_defaults(handler=publishing.run)


def add_site_command(commands: ParserCollection) -> None:
    """Register the replaceable Quartz site adapter."""
    parser = commands.add_parser("site", help="Render with an immutable Quartz checkout")
    add_repository_root(parser)
    parser.add_argument("--profile", type=Path, default=publishing.DEFAULT_PROFILE_PATH)
    parser.add_argument(
        "--content-directory",
        type=Path,
        default=publishing.DEFAULT_OUTPUT_PATH,
    )
    parser.add_argument(
        "--engine-directory",
        type=Path,
        default=quartz.DEFAULT_ENGINE_PATH,
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=quartz.DEFAULT_SITE_PATH,
    )
    actions = parser.add_subparsers(dest="command", required=True)
    build = actions.add_parser("build", help="Build the static Quartz site")
    add_repository_root(build, suppress_default=True)
    serve = actions.add_parser("serve", help="Build and serve a local preview")
    add_repository_root(serve, suppress_default=True)
    serve.add_argument("--port", type=int, default=8080)
    parser.set_defaults(handler=quartz.run)


def build_parser() -> ArgumentParser:
    """Build the stable package command contract."""
    parser = ArgumentParser(prog="mindgarden", description=__doc__)
    parser.add_argument(
        "--version",
        action="version",
        version=f"mindgarden {__version__}",
    )
    commands = parser.add_subparsers(dest="interface", required=True)

    validate = commands.add_parser("validate", help="Validate a garden repository")
    add_repository_root(validate)
    validate.set_defaults(handler=run_validation)
    version = commands.add_parser("version", help="Show the installed version")
    version.set_defaults(handler=run_version)
    add_lifecycle_commands(commands)
    add_ingest_command(commands)
    add_agent_commands(commands)
    add_publish_command(commands)
    add_site_command(commands)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the CLI with stable failures for human and machine callers."""
    parsed = build_parser().parse_args(arguments)
    try:
        result = parsed.handler(parsed)
    except ContractError as error:
        print(f"mindgarden contract error: {error}", file=sys.stderr)
        return ExitCode.CONTRACT
    except json.JSONDecodeError as error:
        print(f"mindgarden contract error: invalid JSON: {error}", file=sys.stderr)
        return ExitCode.CONTRACT
    except (OSError, UnicodeError) as error:
        print(f"mindgarden I/O error: {error}", file=sys.stderr)
        return ExitCode.IO
    except ValueError as error:
        print(f"mindgarden contract error: {error}", file=sys.stderr)
        return ExitCode.CONTRACT
    except subprocess.CalledProcessError as error:
        print(
            f"mindgarden external command failed with status {error.returncode}: "
            f"{error.cmd}",
            file=sys.stderr,
        )
        return ExitCode.EXTERNAL
    return int(result)


if __name__ == "__main__":
    raise SystemExit(main())
