"""Explicit scoped handoff to replaceable disposable query stores."""

from ..adapters.registry_files import control_path, private_parent
from ..adapters.sqlite_query import SQLiteQueryStore, VERSION
from ..domain.contracts import canonical_json, digest_bytes, read_object
from ..domain.validation import ContractError
from .query import QueryContext
from .retrieval import build_index


def run_query_store(arguments, *, store_factory=SQLiteQueryStore):
    context = QueryContext.load(arguments.local_config, arguments.scope)
    operation = arguments.operation
    projection = {"search": "search", "graph": "graph", "backlinks": "backlinks"}.get(
        operation, "index"
    )
    # Authorization, revocation, expiry, input integrity and output budgets are
    # checked before any store bytes are opened, including stale cache metadata.
    index = build_index(context, projection=projection)
    store = (
        None
        if operation == "capabilities"
        else store_factory(arguments.cache_directory)
    )
    scope = context.scope_digest()
    if operation == "capabilities":
        result = store_factory.capabilities()
    elif operation in {"plan", "build"}:
        result = (
            store.plan(index, scope)
            if operation == "plan"
            else store.build(
                index, scope, arguments.plan_digest, check_live=context.check_live
            )
        )
    elif operation == "audit":
        store.load(index, scope)
        result = {"status": "verified", "version": VERSION}
    elif operation == "search":
        result = {
            "schema": "mindgarden.query-store-results/v1",
            "scope": index["scope"],
            "inputs": index["inputs"],
            "results": store.search(index, scope, arguments.query)[
                : min(arguments.limit, context.session["budgets"]["max_results"])
            ],
        }
    elif operation == "graph":
        result = store.traverse(
            index,
            scope,
            arguments.target,
            min(arguments.depth, context.session["budgets"]["max_depth"]),
            min(arguments.limit, context.session["budgets"]["max_results"]),
        )
    elif operation == "backlinks":
        result = {
            "links": store.backlinks(index, scope, arguments.target)[
                : context.session["budgets"]["max_results"]
            ]
        }
    elif operation == "backup":
        if arguments.backup_file is None:
            raise ContractError(
                "QUERY_STORE_INPUT: supply an explicit private backup file"
            )
        result = store.backup(index, scope)
        content = canonical_json(result)
        context.ensure_output(content)
        path = control_path(arguments.backup_file)
        private_parent(path)
        with path.open("xb") as output:
            output.write(content)
        path.chmod(0o600)
        result = {"status": "backed-up", "sha256": digest_bytes(content)}
    elif operation == "restore":
        backup = (
            read_object(control_path(arguments.backup_file))
            if arguments.backup_file
            else {}
        )
        if backup != store_backup(index, scope):
            raise ContractError(
                "QUERY_STORE_INCOMPATIBLE: backup is not the exact current authorized projection"
            )
        result = store.build(
            index, scope, arguments.plan_digest, check_live=context.check_live
        )
    elif operation == "reset-plan":
        marker = store.inventory()
        value = {
            "schema": "mindgarden.query-store-reset/v1",
            "before": digest_bytes(canonical_json(marker)),
            "scope_sha256": scope,
        }
        result = {**value, "plan_sha256": digest_bytes(canonical_json(value))}
    else:
        marker = store.inventory()
        value = {
            "schema": "mindgarden.query-store-reset/v1",
            "before": digest_bytes(canonical_json(marker)),
            "scope_sha256": scope,
        }
        if digest_bytes(canonical_json(value)) != arguments.plan_digest:
            raise ContractError("QUERY_STORE_STALE: review the current reset plan")
        result = store.reset(value["before"], check_live=context.check_live)
    context.ensure_output(canonical_json(result))
    print(canonical_json(result).decode(), end="")
    return 0


def store_backup(index, scope):
    return {
        "schema": "mindgarden.query-store-backup/v1",
        "adapter": "sqlite-fts5",
        "version": VERSION,
        "scope_sha256": scope,
        "index_sha256": digest_bytes(canonical_json(index)),
        "index": index,
        "publication": "never-exportable",
    }
