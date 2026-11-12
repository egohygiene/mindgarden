"""Private local discovery and selected reads over existing garden/session contracts."""

from ..adapters.generated_files import apply_generated, inventory
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from ..domain.scope import inherit_scope, local_scope
from ..domain.validation import ContractError
from .federation import export_destination
from .query import QueryContext
from .query_view import metadata_view
from .retrieval import (
    backlinks_payload,
    graph_payload,
    outbound_payload,
    render_context,
    search_payload,
)

OPERATIONS = {
    "search": "search",
    "graph": "graph",
    "backlinks": "backlinks",
    "outbound": "graph",
    "context": "context",
}


def require_private(context):
    context.check_live()
    if (
        context.session["publication_authority"] != "never-exportable"
        or context.session.get("request_scope", {}).get("visibility")
        not in {"personal", "organization"}
        or context.session["execution"] != "offline"
    ):
        raise ContractError(
            "LOCAL_FEDERATION_SCOPE: explicit private/internal offline never-exportable session required"
        )


def ordinary_output_scope(context, scopes):
    scope = context.output_scope(scopes)
    if scope["visibility"] == "restricted" or scope["persistence"] == "encrypted-vault":
        raise ContractError(
            "RUNTIME_UNVERIFIED: mixed private/internal outputs require unavailable confidential runtime/storage"
        )
    return inherit_scope(
        [
            scope,
            local_scope(
                scope["visibility"],
                persistence=scope["persistence"],
                execution=scope["execution"],
                publication="never-exportable",
            ),
        ]
    )


def verified_metadata(context):
    views = metadata_view(context)
    represented = {
        item["garden"]: item["revision"] for item in context.session["readable"]
    }
    if any(
        view["revision"] != represented.get(garden) for garden, view in views.items()
    ):
        raise ContractError(
            "SESSION_REVISION: discovery metadata differs from the exact authorized view"
        )
    context.last_view_revisions = {
        garden: view["revision"] for garden, view in views.items()
    }
    context.check_live()
    return views


def discover_local(context: QueryContext, *, max_gardens=16):
    require_private(context)
    context.require("index")
    if type(max_gardens) is not int or not 1 <= max_gardens <= 16:
        raise ContractError(
            "QUERY_BUDGET: local discovery requires one to sixteen gardens"
        )
    views = verified_metadata(context)
    maximum = min(max_gardens, context.session["budgets"]["max_results"])
    selected = sorted(views)[:maximum]
    retired = set().union(*(view["retired"] for view in views.values()))
    gardens, scopes = [], []
    for garden in selected:
        view = views[garden]
        # Read only the already-authorized manifest/metadata; no source or body access.
        binding = context.bindings.garden(garden)
        manifest = read_object(binding["root"] / ".garden/garden.json")
        records = [
            record
            for record in view["records"].values()
            if record["schema"] in {"mindgarden.knowledge/v1", "mindgarden.claim/v1"}
            and record["status"] == "active"
            and record["review"]["state"] == "approved"
            and (garden, record["id"]) not in retired
            and (
                record["schema"] != "mindgarden.claim/v1"
                or (record["subject"]["garden"], record["subject"]["id"]) not in retired
            )
        ]
        scope = inherit_scope(
            [binding["scope"], *[view["scopes"][record["id"]] for record in records]]
        )
        scopes.append(scope)
        gardens.append(
            {
                "garden": garden,
                "revision": view["revision"],
                "canonical_uri": manifest["canonical_uri"],
                "title": manifest["title"],
                "kind": manifest["kind"],
                "scope": scope,
                "review_state": "approved-only",
                "records_available": len(records),
                "body_verification": "not-performed",
                "permitted_operations": sorted(
                    op
                    for op, projection in OPERATIONS.items()
                    if projection in context.session["projections"]
                ),
                "contracts": sorted(set(manifest["contracts"]["reads"])),
            }
        )
    scope = ordinary_output_scope(context, scopes)
    catalog = {
        "schema": "mindgarden.local-federation-catalog/v1",
        "classification": "machine-local-control",
        "publication": "never-exportable",
        "scope": scope,
        "freshness": "represented-revision",
        "expires_at": context.session["expires_at"],
        "authority_sha256": context.scope_digest(),
        "trust": "untrusted-evidence",
        "gardens": gardens,
        "truncated": len(selected) < len(views),
        "capabilities": {
            "local_discovery": True,
            "metadata_before_bodies": True,
            "remote_fetch": False,
            "remote_query": False,
            "remote_write": False,
            "signatures": False,
            "package_installation": False,
            "ai_summary": False,
            "organization_assurance": "draft-local-policy-only",
        },
    }
    catalog["catalog_sha256"] = digest_bytes(canonical_json(catalog))
    if ContractRegistry().errors(catalog, "local-federation-catalog"):
        raise ContractError(
            "LOCAL_DISCOVERY_INVALID: local catalog violates the supported metadata contract"
        )
    return context.finalize(catalog)


def query_local(context: QueryContext, request: dict):
    require_private(context)
    if ContractRegistry().errors(request, "local-federation-query"):
        raise ContractError(
            "LOCAL_QUERY_INVALID: select one supported read handler and exact garden revisions"
        )
    ids = {item["garden"] for item in request["gardens"]}
    if len(ids) != len(request["gardens"]):
        raise ContractError("LOCAL_QUERY_INVALID: garden identities must be distinct")
    selected = context.select_gardens(ids)
    operation = request["operation"]
    selected.require(OPERATIONS[operation])
    views = verified_metadata(selected)
    if {garden: view["revision"] for garden, view in views.items()} != {
        item["garden"]: item["revision"] for item in request["gardens"]
    }:
        raise ContractError(
            "SESSION_REVISION: request selection differs from current authorized metadata"
        )
    ordinary_output_scope(
        selected,
        [binding["scope"] for binding in selected.bindings.gardens.values()]
        + [scope for view in views.values() for scope in view["scopes"].values()],
    )
    if operation == "search":
        payload = canonical_json(
            search_payload(selected, request["query"], limit=request["limit"])
        )
    elif operation == "graph":
        payload = canonical_json(
            graph_payload(
                selected,
                start=request["start"],
                depth=request["depth"],
                limit=request["limit"],
            )
        )
    elif operation == "backlinks":
        payload = canonical_json(backlinks_payload(selected, request["artifact"]))
    elif operation == "outbound":
        payload = canonical_json(outbound_payload(selected, request["artifact"]))
    else:
        payload = render_context(selected, request["profile"], request["format"])
    selected.ensure_output(payload)
    return payload


def run_local_federation(arguments):
    request = (
        read_object(arguments.input) if arguments.operation == "local-query" else None
    )
    if request is not None:
        if ContractRegistry().errors(request, "local-federation-query"):
            raise ContractError(
                "LOCAL_QUERY_INVALID: unsupported selected read request"
            )
        garden_ids = {item["garden"] for item in request["gardens"]}
    else:
        garden_ids = set(arguments.garden_id) if arguments.garden_id else None
    context = QueryContext.load(
        arguments.local_config, arguments.scope, garden_ids=garden_ids
    )
    if request is not None:
        content = query_local(context, request)
    else:
        catalog = discover_local(context, max_gardens=arguments.max_gardens)
        if arguments.output_directory:
            directory = export_destination(
                context,
                arguments.output_directory.absolute().parent,
                arguments.output_directory.name,
            )
            files = {"catalog.json": canonical_json(catalog)}
            preview = {"catalog": catalog, "files": inventory(files)}
            digest = digest_bytes(canonical_json(preview))
            if arguments.apply or arguments.check:
                if arguments.check and not directory.is_dir():
                    raise ContractError(
                        "LOCAL_DISCOVERY_INVALID: owned local catalog is unavailable"
                    )

                def verify():
                    if (
                        discover_local(context, max_gardens=arguments.max_gardens)
                        != catalog
                    ):
                        raise ContractError(
                            "SESSION_REVISION: local discovery changed before output selection"
                        )

                apply_generated(
                    directory,
                    files,
                    digest if arguments.check else arguments.plan_digest,
                    digest,
                    check_live=context.check_live,
                    validate_output=context.ensure_bundle,
                    verify_inputs=verify,
                )
            content = canonical_json({**preview, "plan_sha256": digest})
        elif arguments.apply or arguments.check:
            raise ContractError(
                "LOCAL_DISCOVERY_INVALID: supply an explicit private output directory"
            )
        else:
            content = canonical_json(catalog)
    context.ensure_output(content)
    print(content.decode(), end="")
    return 0
