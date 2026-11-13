"""Stable command-line interface for the Mindgarden package."""

from __future__ import annotations

from argparse import SUPPRESS, ArgumentParser, ArgumentTypeError, Namespace
from enum import IntEnum
from functools import partial
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
    parser.add_argument("--captured", required=True, help="V0 capture date or v1 RFC3339 captured timestamp")
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
    parser.add_argument("--local-config", type=Path, help="Explicit machine-local storage bindings for v1")
    parser.add_argument("--vault-id", help="Logical private source vault for v1")
    parser.add_argument("--adapter", help="Explicit registered source adapter")
    parser.add_argument("--source-scope", type=Path, help="Exact declared captured scope for a v1 source adapter")
    parser.add_argument("--manifest-version", help="Declared captured-package contract version")
    parser.add_argument("--attachment-mode", choices=("all", "catalog-only", "selected"),
                        help="Normalize all attachment bytes, catalog metadata only, or selected asset identities")
    parser.add_argument("--asset-id", action="append", default=[], help="Explicit attachment identity to normalize; repeatable")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Preview v1 normalization without writing")
    mode.add_argument("--apply", action="store_true", help="Apply a digest-bound v1 plan")
    parser.add_argument("--plan-digest", help="Reviewed v1 plan_sha256")
    from ..application.ingestion import run_ingest

    parser.set_defaults(handler=run_ingest)


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

    for command in (index_parser, search_parser, context_parser, llms_parser, verify_parser):
        command.add_argument("--local-config", type=Path, help="Explicit local garden and storage bindings")
        command.add_argument("--scope", type=Path, help="Explicit v1 scoped-query session")
        command.add_argument("--diagnostic-format", choices=("text","json"), default="text")
        command.set_defaults(scoped_output_command=True)

    from ..application.retrieval import run_projection

    for name in ("graph", "backlinks", "outbound"):
        command = commands.add_parser(name, help="Retrieve an authorized typed relationship projection")
        add_repository_root(command)
        command.add_argument("--local-config", type=Path, required=True)
        command.add_argument("--scope", type=Path, required=True)
        command.add_argument("--diagnostic-format", choices=("text","json"), default="text")
        command.set_defaults(scoped_output_command=True)
        if name == "graph":
            command.add_argument("--start", help="Stable garden/artifact traversal start")
            command.add_argument("--max-depth", type=positive_integer, default=1)
            command.add_argument("--limit", type=positive_integer, default=100)
        else:
            command.add_argument("--artifact", required=True, help="Stable garden/artifact identifier")
        command.set_defaults(handler=partial(run_projection, operation=name))


def run_validation(arguments: Namespace) -> int:
    """Validate one consumer repository."""
    if (arguments.repository_root / ".mindgarden-write.lock").exists():
        if arguments.format == "json":
            print(json.dumps({"schema": "mindgarden.validation/v1", "status": "incomplete", "diagnostics": [{
                "code": "WRITE_LOCKED", "severity": "warning", "location": "garden.json",
                "message": "A write or recovery owns this garden", "remediation": "Complete or recover the owning operation."}]}))
            return ExitCode.CONTRACT
        raise ContractError("WRITE_LOCKED: complete or recover the owning operation before validation")
    resolver = None
    authorized = None
    if arguments.local_config:
        from ..application.bindings import LocalBindings
        from ..application.storage import content_resolver

        bindings = LocalBindings.load(arguments.local_config)
        resolver = content_resolver(bindings)
        from ..domain.garden import inspect_garden

        authorized = {identity: inspect_garden(item["root"], content_resolver=resolver, allow_unavailable_references=True)
                      for identity, item in bindings.gardens.items()}
    if arguments.format == "json":
        from ..domain.garden import inspect_garden

        if (arguments.repository_root / ".garden/garden.json").exists():
            if (arguments.repository_root / ".garden/garden.yaml").exists():
                payload = {"schema": "mindgarden.validation/v1", "status": "invalid",
                           "diagnostics": [{"code": "MANIFEST_AMBIGUOUS", "severity": "error",
                                            "location": "garden.json", "message": "Multiple garden manifests",
                                            "remediation": "Select one contract version."}]}
            else:
                payload = inspect_garden(arguments.repository_root, content_resolver=resolver,
                                          authorized_gardens=authorized).report()
        else:
            try:
                count = validate_repository(arguments.repository_root)
                payload = {"schema": "mindgarden.validation/v1", "status": "valid",
                           "coverage": {"contracts": "v0"}, "records": count, "diagnostics": []}
            except ContractError:
                payload = {"schema": "mindgarden.validation/v1", "status": "invalid",
                           "coverage": {"contracts": "v0"}, "diagnostics": [{
                               "code": "V0_CONTRACT", "severity": "error", "location": ".garden",
                               "message": "Legacy contract validation failed",
                               "remediation": "Run text validation in the authorized local workspace."}]}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        return ExitCode.SUCCESS if payload["status"] == "valid" else ExitCode.CONTRACT
    note_count = validate_repository(arguments.repository_root, content_resolver=resolver, authorized_gardens=authorized)
    print(f"mindgarden validation passed: {note_count} note(s)")
    return ExitCode.SUCCESS


def run_version(_arguments: Namespace) -> int:
    """Print the installed package version."""
    print(f"mindgarden {__version__}")
    return ExitCode.SUCCESS


def run_design(arguments) -> int:
    from ..domain.design import css_variables, load_tokens, quartz_theme
    from ..domain.contracts import canonical_json

    tokens = load_tokens(arguments.tokens)
    value = css_variables(tokens) if arguments.format == "css" else canonical_json(quartz_theme(tokens) if arguments.format == "quartz" else tokens).decode()
    print(value, end="")
    return 0


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
    verify.add_argument("--output-directory", type=Path, default=publishing.DEFAULT_OUTPUT_PATH)
    for command in (project, verify):
        command.add_argument("--profile", type=Path, default=SUPPRESS)
        add_site_authority(command)
    parser.set_defaults(handler=run_publication)


def add_site_authority(command) -> None:
    command.add_argument("--local-config", type=Path, help="Explicit v1 local bindings")
    command.add_argument("--scope", type=Path, help="Explicit reviewed-public publication session")
    mode = command.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Preview v1 inputs without writing (default)")
    mode.add_argument("--apply", action="store_true", help="Create or verify v1 output after exact-digest review")
    mode.add_argument("--check", action="store_true", help="Verify existing v1 output without renderer calls")
    command.add_argument("--plan-digest", help="Exact reviewed v1 site-plan digest")
    command.add_argument("--diagnostic-format", choices=("text", "json"), default="text", help="Shareable v1 failure diagnostics")


def uses_v1_site(arguments) -> bool:
    return (arguments.local_config is not None or arguments.scope is not None
            or (arguments.repository_root / ".garden/garden.json").exists())


def run_publication(arguments) -> int:
    if uses_v1_site(arguments):
        from ..application.site import run_site

        if arguments.command == "verify":
            arguments.check = True
        return run_site(arguments, operation="project")
    if arguments.plan or arguments.apply or arguments.check or arguments.plan_digest:
        raise ContractError("SITE_VERSION: reviewed site plans require explicit v1 inputs")
    return publishing.run(arguments)


def run_site_adapter(arguments) -> int:
    if uses_v1_site(arguments):
        from ..application.site import run_site

        return run_site(arguments, operation="build")
    if arguments.plan or arguments.apply or arguments.check or arguments.plan_digest:
        raise ContractError("SITE_VERSION: reviewed site plans require explicit v1 inputs")
    return quartz.run(arguments)


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
    for command in (build, serve):
        for name in ("profile", "content-directory", "engine-directory", "output-directory"):
            command.add_argument("--" + name, type=Path, default=SUPPRESS)
        add_site_authority(command)
    parser.set_defaults(handler=run_site_adapter)
    from ..application.portal import run_portal

    compose = actions.add_parser("compose", help="Compose a pinned public garden without changing sibling portal surfaces")
    compose.add_argument("--input", type=Path, required=True, help="Explicit private portal-request/v1 control file")
    mode = compose.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Inspect the exact composition plan (default)")
    mode.add_argument("--apply", action="store_true", help="Create or verify after exact-digest review")
    mode.add_argument("--check", action="store_true", help="Require a complete checked garden and final portal receipt")
    compose.add_argument("--plan-digest", help="Exact reviewed portal-plan digest")
    compose.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    compose.set_defaults(handler=run_portal, public_artifact_command=True)


def add_federation_command(commands: ParserCollection) -> None:
    """Register offline, reviewed public discovery projections."""
    from ..application.federation import run_federation

    federation = commands.add_parser("federation", help="Discover explicit public projections or authorized local gardens")
    operations = federation.add_subparsers(dest="operation", required=True)
    build = operations.add_parser("build", help="Plan, create or check an immutable public projection bundle")
    build.add_argument("--local-config", type=Path, required=True)
    build.add_argument("--scope", type=Path, required=True)
    build.add_argument("--profile", type=Path, required=True, help="Approved v1 federation projection profile")
    build.add_argument("--output-directory", type=Path, required=True, help="Existing export parent; profile output_root selects its bundle directory")
    mode = build.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Preview without writing (default)")
    mode.add_argument("--apply", action="store_true", help="Create after checking the exact reviewed plan digest")
    mode.add_argument("--check", action="store_true", help="Verify an existing bundle against current reviewed inputs")
    build.add_argument("--plan-digest", help="Exact federation plan_sha256 required by --apply")
    build.set_defaults(handler=run_federation)
    catalog = operations.add_parser("catalog", help="Verify and combine explicitly supplied public bundles without fetching")
    catalog.add_argument("--input", type=Path, required=True, help="Machine-local versioned catalog request with expected revisions")
    catalog.set_defaults(handler=run_federation)
    public_query = operations.add_parser("query", help="Read selected supplied public bundles into bounded cited context")
    public_query.add_argument("--local-config", type=Path, required=True)
    public_query.add_argument("--scope", type=Path, required=True)
    public_query.add_argument("--input", type=Path, required=True, help="Catalog, selected bundles and explicit byte/item limits")
    public_query.add_argument("--format", choices=("json", "markdown"), default="json")
    public_query.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    public_query.set_defaults(handler=run_federation, scoped_output_command=True)

    from ..application.local_federation import run_local_federation

    local = operations.add_parser("local-discover", help="Inspect authorized private/internal garden metadata before opening bodies")
    local.add_argument("--local-config", type=Path, required=True)
    local.add_argument("--scope", type=Path, required=True)
    local.add_argument("--garden-id", action="append", help="Narrow to an already-authorized garden; repeat for dependencies")
    local.add_argument("--max-gardens", type=int, default=16)
    local.add_argument("--output-directory", type=Path)
    mode = local.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    local.add_argument("--plan-digest")
    local.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    local.set_defaults(handler=run_local_federation, scoped_output_command=True)
    query = operations.add_parser("local-query", help="Use a bounded existing read handler over exact selected garden revisions")
    query.add_argument("--local-config", type=Path, required=True)
    query.add_argument("--scope", type=Path, required=True)
    query.add_argument("--input", type=Path, required=True)
    query.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    query.set_defaults(handler=run_local_federation, scoped_output_command=True)


def add_compaction_command(commands: ParserCollection) -> None:
    from ..application.compaction import run_compaction

    parser = commands.add_parser("compaction", help="Inspect authored compaction without changing originals or review state")
    operations = parser.add_subparsers(dest="operation", required=True)
    preview = operations.add_parser("preview", help="Verify exact scoped evidence, hierarchy, retention and an optional curation handoff")
    preview.add_argument("--input", type=Path, required=True)
    preview.add_argument("--local-config", type=Path, required=True)
    preview.add_argument("--scope", type=Path, required=True)
    preview.add_argument("--curation-plan", type=Path, help="Exact existing curation-plan/v1 proposal pinned by the hierarchy")
    preview.add_argument("--source-only", action="store_true", help="Use exact private session grants for first-pass proposed summaries")
    preview.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    preview.set_defaults(handler=run_compaction, public_artifact_command=True)
    from ..application.compaction_bundles import run_compaction_bundle

    build = operations.add_parser("build", help="Plan, create or verify an immutable private proof bundle with bounded lifetime")
    build.add_argument("--input", type=Path, required=True)
    build.add_argument("--local-config", type=Path, required=True)
    build.add_argument("--scope", type=Path, required=True)
    build.add_argument("--curation-plan", type=Path)
    build.add_argument("--source-only", action="store_true")
    build.add_argument("--created-at", required=True, help="Explicit proof creation time with offset, retained for reproducible checks")
    build.add_argument("--output-directory", type=Path, required=True)
    mode = build.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    build.add_argument("--plan-digest", help="Reviewed build digest required for application")
    build.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    build.set_defaults(handler=run_compaction_bundle, public_artifact_command=True)


def add_registry_command(commands: ParserCollection) -> None:
    """Register machine-local control flows without changing canonical gardens."""
    from ..application.registry import run_registry

    registry = commands.add_parser("registry", help="Manage explicit machine-local garden registrations")
    operations = registry.add_subparsers(dest="operation", required=True)
    from ..application.registry_cache import run_cache

    for name in ("cache-inspect","cache-plan","cache-apply"):
        command = operations.add_parser(name,help="Inspect or reversibly quarantine an explicitly owned scope cache")
        command.add_argument("--registry",type=Path)
        if name != "cache-apply":
            command.add_argument("--garden-id",required=True)
            command.add_argument("--scope-digest",required=True)
        if name == "cache-plan":
            command.add_argument("--operation-id",required=True)
            command.add_argument("--action",choices=("quarantine","restore"),required=True)
            command.add_argument("--recovery-id")
            command.add_argument("--output",type=Path)
        if name == "cache-apply":
            command.add_argument("--plan",type=Path,required=True)
            command.add_argument("--plan-digest",required=True)
        command.set_defaults(handler=run_cache)
    for name in ("init", "register", "unregister", "set-view", "remove-view", "restore", "apply", "list", "inspect", "doctor", "capabilities"):
        command = operations.add_parser(name)
        command.add_argument("--registry", type=Path, help="Absolute private registry path; defaults to platform user configuration")
        if name in {"init", "register", "unregister", "set-view", "remove-view", "restore"}:
            command.add_argument("--plan", action="store_true", help="Preview only (default); apply uses a saved plan separately")
            command.add_argument("--output", type=Path, help="Save a new private plan file; omission previews JSON only")
        if name in {"register", "unregister", "inspect", "doctor"}:
            command.add_argument("--garden-id", required=name in {"unregister", "inspect"})
        if name == "register":
            command.add_argument("--root", type=Path, required=True, help="Explicit absolute garden root; no discovery")
            command.add_argument("--visibility", required=True, choices=("public", "organization", "personal", "restricted"))
            command.add_argument("--persistence", choices=("git-tracked", "machine-local", "encrypted-vault"))
            command.add_argument("--execution", choices=("offline", "controlled-import", "networked"), default="offline")
            command.add_argument("--publication", choices=("publishable", "review-required", "never-exportable"), default="review-required")
            command.add_argument("--owner", action="append", default=[], help="Assert canonical owner; registration never rewrites it")
        if name in {"set-view", "remove-view"}:
            command.add_argument("--view-id", required=True)
        if name == "set-view":
            command.add_argument("--garden", action="append", default=[], help="Registered garden identity; repeat for an authorized union selection")
        if name == "restore":
            command.add_argument("--revision", required=True, help="Owned immutable registry snapshot SHA-256")
        if name == "apply":
            command.add_argument("--plan", type=Path, required=True, help="Saved reviewed registry-plan JSON")
            command.add_argument("--plan-digest", required=True)
        if name in {"list", "inspect", "doctor"}:
            command.add_argument("--include-local-paths", action="store_true", help="Show paths in private control output")
        command.set_defaults(handler=run_registry)


def add_asset_command(commands: ParserCollection) -> None:
    """Keep private inventory and human triage separate from publication/deletion."""
    from ..application.assets import run_asset

    command = commands.add_parser("asset", help="Inspect scoped assets or review non-destructive triage")
    operations = command.add_subparsers(dest="operation", required=True)
    for operation in ("inventory", "review"):
        selected = operations.add_parser(operation)
        selected.add_argument("--local-config", type=Path, required=True)
        selected.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
        if operation == "inventory":
            selected.add_argument("--scope", type=Path, required=True)
        else:
            selected.add_argument("--garden-id", required=True)
            selected.add_argument("--input", type=Path, required=True)
            mode = selected.add_mutually_exclusive_group(required=True)
            mode.add_argument("--plan", action="store_true"); mode.add_argument("--apply", action="store_true")
            selected.add_argument("--plan-digest")
        selected.set_defaults(handler=run_asset, scoped_output_command=True)


def add_document_command(commands: ParserCollection) -> None:
    """Select a local PDF integration explicitly; confidential is the default."""
    from ..application.documents import run_document

    command = commands.add_parser("document", help="Plan/apply a classified PDF through optional local tools")
    command.add_argument("--local-config", type=Path, required=True)
    command.add_argument("--garden-id", required=True)
    command.add_argument("--vault-id", required=True)
    command.add_argument("--input", type=Path, required=True)
    for name in ("source-id", "title", "origin", "owner", "rights", "captured"):
        command.add_argument("--" + name, required=True)
    command.add_argument("--classification-review", type=Path, help="Approved initial classification bound to source bytes")
    command.add_argument("--tool-directory", type=Path, help="Explicit directory containing pdfinfo and pdftotext")
    mode = command.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    command.add_argument("--plan-digest")
    command.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    command.set_defaults(handler=run_document, scoped_output_command=True)


def add_extraction_command(commands: ParserCollection) -> None:
    from ..application.extraction import run_extraction

    command = commands.add_parser("extraction", help="Produce unreviewed evidence-bound candidates from recorded optional producer outputs")
    command.add_argument("--local-config", type=Path, required=True)
    command.add_argument("--scope", type=Path, required=True)
    command.add_argument("--input", type=Path, required=True)
    command.add_argument("--recorded-output", type=Path, required=True)
    command.add_argument("--resume", type=Path)
    command.add_argument("--max-new-units", type=int)
    command.add_argument("--output-directory", type=Path)
    command.add_argument("--apply", action="store_true")
    command.add_argument("--plan-digest")
    command.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    command.set_defaults(handler=run_extraction, scoped_output_command=True)


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
    validate.add_argument("--format", choices=("text", "json"), default="text")
    validate.add_argument("--local-config", type=Path, help="Explicit nonportable storage bindings")
    validate.set_defaults(handler=run_validation)
    version = commands.add_parser("version", help="Show the installed version")
    version.set_defaults(handler=run_version)
    add_lifecycle_commands(commands)
    add_ingest_command(commands)
    add_document_command(commands)
    add_asset_command(commands)
    add_agent_commands(commands)
    add_publish_command(commands)
    add_site_command(commands)
    add_federation_command(commands)
    add_compaction_command(commands)
    add_extraction_command(commands)
    add_registry_command(commands)
    from ..application.drive_capture import run_capture

    capture = commands.add_parser("capture", help="Acquire explicitly selected optional provider sources")
    captures = capture.add_subparsers(dest="capture_provider", required=True)
    from ..adapters.drive_credentials import run_authorize

    drive_authorize = captures.add_parser("authorize", help="Configure private read-only Google desktop OAuth locally")
    drive_authorize.add_argument("--client-file", type=Path)
    drive_authorize.add_argument("--token-file", type=Path, required=True)
    drive_authorize.add_argument("--refresh", action="store_true")
    drive_authorize.set_defaults(handler=run_authorize)
    drive_capture = captures.add_parser("drive", help="Plan or acquire a bounded read-only Drive selection")
    drive_capture.add_argument("--input", type=Path, required=True)
    drive_capture.add_argument("--local-config", type=Path, required=True)
    drive_capture.add_argument("--vault-id", required=True)
    drive_capture.add_argument("--output-directory", type=Path, required=True)
    drive_capture.add_argument("--previous-checkpoint", type=Path)
    drive_capture.add_argument("--allow-network", action="store_true")
    drive_capture.add_argument("--apply", action="store_true")
    drive_capture.add_argument("--plan-digest")
    drive_capture.set_defaults(handler=run_capture)

    from ..application.consultation import run_packet

    packet = commands.add_parser("packet", help="Plan a reviewed private preparation packet from exact ledger evidence")
    packet.add_argument("--local-config", type=Path, required=True)
    packet.add_argument("--scope", type=Path, required=True)
    packet.add_argument("--input", type=Path, required=True)
    packet.add_argument("--output-directory", type=Path, required=True)
    packet_mode = packet.add_mutually_exclusive_group()
    packet_mode.add_argument("--apply", action="store_true")
    packet_mode.add_argument("--check", action="store_true")
    packet.add_argument("--plan-digest")
    packet.set_defaults(handler=run_packet)

    from ..application.insights import run_insights

    insights = commands.add_parser("insights", help="Plan reviewed renderer-independent public insight handoffs")
    insights.add_argument("--local-config", type=Path, required=True)
    insights.add_argument("--scope", type=Path, required=True)
    insights.add_argument("--input", type=Path, required=True)
    insights.add_argument("--apply", action="store_true")
    insights.add_argument("--plan-digest")
    insights.add_argument("--output-directory", type=Path)
    insights.set_defaults(handler=run_insights)

    from ..application.learning import run_learning

    learning = commands.add_parser("learning", help="Review authored learning cards, summaries and private schedules")
    learning.add_argument("--local-config", type=Path, required=True)
    learning.add_argument("--scope", type=Path, required=True)
    learning_input = learning.add_mutually_exclusive_group(required=True)
    learning_input.add_argument("--input", type=Path)
    learning_input.add_argument("--import-projection", type=Path)
    learning.add_argument("--events", type=Path, help="Explicit private review-history file")
    learning.add_argument("--review-event", type=Path, help="One authored private grading event to append into the new export")
    learning.add_argument("--as-of", help="Explicit digest/schedule view boundary; does not extend session authority")
    learning.add_argument("--due-only", action="store_true", help="Render a bounded queue of approved cards due in this explicit deck")
    learning.add_argument("--review-limit", type=int, help="Maximum due cards in this view (1–100; default 20)")
    learning.add_argument("--review-offset", type=int, default=0, help="Offset within the exact due-card view")
    learning.add_argument("--apply", action="store_true")
    learning.add_argument("--plan-digest")
    learning.add_argument("--output-directory", type=Path)
    learning.set_defaults(handler=run_learning)
    from ..application.bookmarks import run_bookmarks

    bookmarks = commands.add_parser("bookmarks", help="Inspect or review captured normalized bookmarks privately without browser mutation")
    bookmarks.add_argument("--input", type=Path, required=True)
    bookmarks.add_argument("--input-format", choices=("normalized-json", "captured-source-bundle"), default="normalized-json", help="Select legacy metadata or the pinned verified source-bundle profile")
    bookmarks.add_argument("--catalog", type=Path, required=True)
    bookmarks.add_argument("--classification", choices=("personal", "restricted"), default="restricted")
    bookmark_mode = bookmarks.add_mutually_exclusive_group()
    bookmark_mode.add_argument("--inspect", action="store_true")
    bookmarks.add_argument("--request", type=Path)
    bookmarks.add_argument("--previous-receipt", type=Path)
    bookmarks.add_argument("--plan-file", type=Path, required=True)
    bookmark_mode.add_argument("--apply", action="store_true")
    bookmarks.add_argument("--plan-digest")
    bookmarks.add_argument("--output-directory", type=Path)
    bookmarks.set_defaults(handler=run_bookmarks)
    from ..application.memory import run_memory

    memory = commands.add_parser("memory", help="Review bounded provider-neutral assistant-memory snippets")
    memory.add_argument("--local-config", type=Path, required=True)
    memory.add_argument("--scope", type=Path, required=True)
    memory.add_argument("--input", type=Path, required=True)
    memory_mode = memory.add_mutually_exclusive_group()
    memory_mode.add_argument("--apply", action="store_true")
    memory_mode.add_argument("--check", action="store_true", help="Verify an existing managed bundle against current source, authority and expiry")
    memory.add_argument("--created-at", help="Explicit creation timestamp for an expiring local bundle")
    memory.add_argument("--plan-digest")
    memory.add_argument("--output-directory", type=Path)
    memory.set_defaults(handler=run_memory)
    from ..application.dependency_builds import run_dependency_build

    dependency_build = commands.add_parser("build-projections", help="Plan selected-record dependency builds or reconcile prior outputs")
    dependency_build.add_argument("--local-config", type=Path, required=True)
    dependency_build.add_argument("--scope", type=Path, required=True)
    dependency_build.add_argument("--input", type=Path, required=True)
    dependency_build.add_argument("--select-output", action="append", help="Build only this declared output; repeat for a reviewed subset")
    dependency_mode = dependency_build.add_mutually_exclusive_group()
    dependency_mode.add_argument("--previous-manifest", type=Path)
    dependency_mode.add_argument("--apply", action="store_true")
    dependency_build.add_argument("--plan-digest")
    dependency_build.add_argument("--output-directory", type=Path)
    dependency_build.set_defaults(handler=run_dependency_build)
    from ..application.query_store import run_query_store

    query_store = commands.add_parser("query-store", help="Use an explicit optional private SQLite query cache")
    query_store.add_argument("--local-config", type=Path, required=True)
    query_store.add_argument("--scope", type=Path, required=True)
    query_store.add_argument("--cache-directory", type=Path, required=True)
    query_store.add_argument("--operation", choices=("capabilities", "plan", "build", "audit", "search", "graph", "backlinks", "backup", "restore", "reset-plan", "reset"), required=True)
    query_store.add_argument("--plan-digest")
    query_store.add_argument("--backup-file", type=Path)
    query_store.add_argument("--query", default="")
    query_store.add_argument("--target", default="")
    query_store.add_argument("--limit", type=positive_integer, default=10)
    query_store.add_argument("--depth", type=positive_integer, default=1)
    query_store.set_defaults(handler=run_query_store)
    from ..application.decisions import run_decisions

    decisions = commands.add_parser("decisions", help="Project explicit public ADR read-model metadata")
    decisions.add_argument("--input", type=Path, required=True)
    decisions.add_argument("--input-sha256", required=True)
    decisions.add_argument("--represented-commit", required=True)
    decisions.add_argument("--include-proposed", action="store_true")
    decisions.add_argument("--max-bytes", type=positive_integer, default=65536)
    decisions.set_defaults(handler=run_decisions)
    design = commands.add_parser("design", help="Validate and export stack-neutral design tokens")
    design.add_argument("--tokens", type=Path, help="Explicit token file; omission selects the installed design source")
    design.add_argument("--format", choices=("json", "css", "quartz"), default="json")
    design.set_defaults(handler=run_design)
    from ..application.curation import run_gardenize

    gardenize = commands.add_parser("gardenize", help="Preview or apply an authored curation proposal")
    gardenize.add_argument("--local-config", type=Path, required=True)
    gardenize_mode = gardenize.add_mutually_exclusive_group(required=True)
    gardenize_mode.add_argument("--plan", type=Path, help="Validate and preview the supplied proposal")
    gardenize_mode.add_argument("--apply", type=Path, help="Apply the supplied proposal after review")
    gardenize.add_argument("--plan-digest", help="Exact reviewed preview digest")
    gardenize.set_defaults(handler=run_gardenize)
    from ..application.routing import run_route

    route = commands.add_parser("route", help="Explain or apply authored candidate placement across explicit gardens")
    route.add_argument("--local-config", type=Path, required=True)
    route.add_argument("--catalog", type=Path, help="Portable versioned garden catalog")
    route.add_argument("--input", type=Path, help="Authored routing-plan document")
    route.add_argument("--transition", type=Path, help="Reviewed private move, merge or v2 split/replacement request")
    route.add_argument("--reference-repair", type=Path, help="Independently reviewed incoming-reference repair request")
    mode = route.add_mutually_exclusive_group()
    for operation in ("plan", "apply", "explain", "check", "recover"):
        mode.add_argument("--" + operation, action="store_true")
    route.add_argument("--plan-digest", help="Reviewed plan digest, or interrupted operation digest for recovery")
    route.set_defaults(handler=run_route)
    from ..application.sessions import run_scope

    scope = commands.add_parser("scope", help="Author an explicit local query session with current authorized revisions")
    scope.add_argument("--local-config", type=Path, required=True)
    scope.add_argument("--session-id", required=True)
    selection = scope.add_mutually_exclusive_group(required=True)
    selection.add_argument("--readable-garden", action="append")
    selection.add_argument("--registry-view", help="Named selection from a managed registry; grants remain explicit")
    scope.add_argument("--writable-garden")
    scope.add_argument("--allowed-visibility", action="append", required=True,
                       choices=("public", "organization", "personal", "restricted"))
    scope.add_argument("--allowed-review-state", action="append", choices=("approved", "in-review", "unreviewed", "rejected"))
    scope.add_argument("--execution", choices=("offline", "controlled-import", "networked"), default="offline")
    scope.add_argument("--publication-authority", choices=("never-exportable", "review-required", "publishable"), default="never-exportable")
    scope.add_argument("--request-visibility", choices=("public", "organization", "personal", "restricted"), default="personal")
    scope.add_argument("--projection", action="append", choices=("index", "search", "graph", "backlinks", "context", "llms", "evidence", "assets", "source-evidence"))
    scope.add_argument("--source-grants", type=Path, help="Private wrapper containing exact normalized source references; requires source-evidence projection")
    scope.add_argument("--max-results", type=positive_integer, default=100)
    scope.add_argument("--max-context-bytes", type=positive_integer, default=16384)
    scope.add_argument("--max-output-bytes", type=positive_integer, help="Serialized query-output ceiling; default 16 MiB")
    scope.add_argument("--max-depth", type=positive_integer, default=4)
    scope.add_argument("--max-candidates", type=positive_integer, default=1000)
    scope.add_argument("--expires-at", required=True)
    scope.add_argument("--output", type=Path, help="Create a new private session file; omission previews JSON")
    scope.set_defaults(handler=run_scope)
    from ..application.research import run_research

    research = commands.add_parser("research", help="Run an explicit bounded read plan for a calling assistant")
    research.add_argument("--input", type=Path, required=True, help="Versioned research-request/v1 with closed tools")
    research.add_argument("--local-config", type=Path, required=True)
    research.add_argument("--scope", type=Path, required=True)
    research.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    research.set_defaults(handler=run_research, scoped_output_command=True)
    from ..application.pilot import run_pilot

    pilot = commands.add_parser("pilot", help="Check an explicitly selected private local pilot without reading originals")
    pilot_operations = pilot.add_subparsers(dest="operation", required=True)
    preflight = pilot_operations.add_parser("preflight", help="Inspect private configuration and metadata only")
    preflight.add_argument("--local-config", type=Path, required=True)
    preflight.add_argument("--scope", type=Path, required=True)
    preflight.add_argument("--garden-id", required=True)
    preflight.add_argument("--vault-id", required=True)
    preflight.add_argument("--classification", choices=("personal", "restricted"), required=True)
    preflight.add_argument("--drive-binding", type=Path, help="Optional explicit reviewed capture selection")
    preflight.add_argument("--diagnostic-format", choices=("text", "json"), default="text")
    preflight.set_defaults(handler=run_pilot, scoped_output_command=True)
    from ..application.evidence import run_evidence

    evidence = commands.add_parser("evidence", help="Resolve one exact citation authorized by reviewed knowledge")
    evidence.add_argument("--local-config", type=Path, required=True)
    evidence.add_argument("--scope", type=Path, required=True)
    evidence.add_argument("--diagnostic-format", choices=("text","json"), default="text")
    for field in ("garden-id", "source-id", "revision", "locator", "content-sha256"):
        evidence.add_argument("--" + field, required=True)
    evidence.set_defaults(handler=run_evidence,scoped_output_command=True)
    from ..application.storage import run_vault

    vault = commands.add_parser("vault", help="Manage explicitly bound private source storage")
    vault_commands = vault.add_subparsers(dest="operation", required=True)
    for operation in ("init", "audit", "capabilities", "resolve", "export", "restore", "relocate", "migrate"):
        command = vault_commands.add_parser(operation)
        command.add_argument("--local-config", type=Path, required=True)
        command.add_argument("--vault-id", required=True)
        if operation in {"init", "export", "restore", "relocate", "migrate"}:
            mode = command.add_mutually_exclusive_group()
            mode.add_argument("--plan", action="store_true")
            mode.add_argument("--apply", action="store_true")
            command.add_argument("--plan-digest")
        if operation == "export":
            command.add_argument("--output", type=Path, required=True, help="Private backup file outside garden and vault roots")
        if operation in {"restore", "relocate"}:
            command.add_argument("--destination", type=Path, required=True, help="Explicit clean private filesystem vault root")
        if operation == "restore":
            command.add_argument("--input", type=Path, required=True, help="Captured portable vault backup")
        if operation == "resolve":
            command.add_argument("--content-id", required=True)
        if operation == "migrate":
            command.add_argument("--target-local-config", type=Path, required=True,
                                 help="Private configuration of an initialized target with the same logical vault ID")
        command.set_defaults(handler=run_vault)
    from ..application.policy import run_policy

    policy = commands.add_parser("policy", help="Inspect the local reference policy and deterministic information-flow decisions")
    policy_operations = policy.add_subparsers(dest="operation", required=True)
    policy_operations.add_parser("inspect").set_defaults(handler=run_policy)
    evaluate = policy_operations.add_parser("evaluate")
    evaluate.add_argument("--input", type=Path, required=True)
    evaluate.set_defaults(handler=run_policy)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the CLI with stable failures for human and machine callers."""
    parsed = build_parser().parse_args(arguments)
    try:
        if (getattr(parsed, "public_artifact_command", False)
                or (parsed.handler in (run_publication, run_site_adapter) and uses_v1_site(parsed))):
            try:
                result = parsed.handler(parsed)
            except (ContractError, OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as error:
                from ..domain.public_diagnostics import publication_failure

                report = publication_failure(error)
                if parsed.diagnostic_format == "json":
                    print(json.dumps(report, sort_keys=True), file=sys.stderr)
                else:
                    item = report["diagnostics"][0]
                    print("mindgarden contract error: " + item["code"] + ": " + item["message"] + ". " + item["remediation"], file=sys.stderr)
                return ExitCode.CONTRACT
        elif (getattr(parsed,"scoped_output_command",False)
              and (getattr(parsed,"scope",None) is not None or getattr(parsed,"local_config",None) is not None)):
            try:
                result = parsed.handler(parsed)
            except (ContractError,OSError,UnicodeError,ValueError,subprocess.CalledProcessError) as error:
                from ..domain.query_diagnostics import query_failure

                report = query_failure(error)
                if parsed.diagnostic_format == "json":
                    print(json.dumps(report,sort_keys=True),file=sys.stderr)
                else:
                    diagnostic = report["diagnostics"][0]
                    print("mindgarden contract error: " + diagnostic["code"] + ": " + diagnostic["message"],file=sys.stderr)
                return ExitCode.CONTRACT
        else:
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
