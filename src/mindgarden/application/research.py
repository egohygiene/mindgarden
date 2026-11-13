"""Bounded read plans supplied by a caller; no model, writes or new authority."""

from copy import deepcopy
from datetime import datetime
import time

from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    strict_json,
)
from ..domain.source_access import source_grants
from ..domain.validation import ContractError
from .evidence import resolve_evidence
from .local_federation import (
    OPERATIONS,
    ordinary_output_scope,
    query_local,
    require_private,
    verified_metadata,
)
from .query import QueryContext, authority_bytes
from .source_evidence import resolve_source_evidence

TOOLS = {**OPERATIONS, "evidence": "evidence", "source-evidence": "source-evidence"}


def validate_request(request):
    if ContractRegistry().errors(request, "research-request"):
        raise ContractError("RESEARCH_INVALID: supply a supported bounded read plan")
    gardens = {item["garden"] for item in request["gardens"]}
    if len(gardens) != len(request["gardens"]):
        raise ContractError(
            "RESEARCH_INVALID: selected garden identities must be unique"
        )
    if len(request["steps"]) > request["budgets"]["max_steps"]:
        raise ContractError("RESEARCH_BUDGET: step budget exceeded before reading")
    for step in request["steps"]:
        if step["operation"] not in request["allowed_tools"]:
            raise ContractError(
                "RESEARCH_TOOL_DENIED: caller plan exceeds selected tools"
            )
        if step["operation"] in OPERATIONS:
            if step["gardens"] != request["gardens"]:
                raise ContractError(
                    "RESEARCH_INVALID: every tool must retain exact selected revisions"
                )
            if step["operation"] == "context" and step["format"] != "json":
                raise ContractError(
                    "RESEARCH_INVALID: research observations require JSON context"
                )
        elif step["citation"] not in request["sources"]:
            raise ContractError(
                "RESEARCH_SOURCE_DENIED: exact citation was not selected"
            )
    if any(
        item["source"]["garden"] not in gardens or item["source"]["revision"] is None
        for item in request["sources"]
    ):
        raise ContractError(
            "RESEARCH_SOURCE_DENIED: source selection needs an exact authorized garden/revision"
        )


def observation_count(operation, payload):
    field = {
        "search": "results",
        "graph": "nodes",
        "context": "included",
        "outbound": "links",
        "backlinks": "links",
    }.get(operation)
    return len(payload[field]) if field else 1


def research(
    context: QueryContext,
    request: dict,
    *,
    monotonic=time.monotonic,
    verify_request=lambda: None,
):
    """All-or-nothing observations; every step uses the ordinary scoped services.

    Callers may inspect a result and submit another explicitly bounded plan. They
    do not execute inside this process. The elapsed-time bound is cooperative
    between synchronous local reads; it is not a hard OS deadline.
    """
    request = deepcopy(request)
    validate_request(request)
    require_private(context)
    selected = context.select_gardens({item["garden"] for item in request["gardens"]})
    ceiling = request["budgets"]
    if len(request["steps"]) > selected.session["budgets"]["max_candidates"]:
        raise ContractError(
            "RESEARCH_BUDGET: step selection exceeds the session candidate ceiling"
        )
    started = monotonic()
    expires = datetime.fromisoformat(request["expires_at"].replace("Z", "+00:00"))
    if expires > datetime.fromisoformat(
        selected.session["expires_at"].replace("Z", "+00:00")
    ):
        raise ContractError(
            "RESEARCH_INVALID: request lifetime cannot extend the session"
        )

    def live():
        selected.check_live()
        verify_request()
        if selected.clock() >= expires:
            raise ContractError("SESSION_EXPIRED: research request expired")
        if (monotonic() - started) * 1000 >= ceiling["max_elapsed_ms"]:
            raise ContractError("RESEARCH_BUDGET: elapsed-time budget exceeded")

    live()
    # Validate every requested projection and exact first-pass grant before any body.
    grants = source_grants(selected.session)
    for step in request["steps"]:
        selected.require(TOOLS[step["operation"]])
        if step["operation"] == "source-evidence":
            reference = step["citation"]["source"]
            if (
                grants.get((reference["garden"], reference["id"]))
                != reference["revision"]
            ):
                raise ContractError(
                    "RESEARCH_SOURCE_DENIED: exact source grant is unavailable"
                )
    views = verified_metadata(selected)
    if {garden: value["revision"] for garden, value in views.items()} != {
        item["garden"]: item["revision"] for item in request["gardens"]
    }:
        raise ContractError(
            "SESSION_REVISION: research selection differs from represented revisions"
        )
    scopes = [binding["scope"] for binding in selected.bindings.gardens.values()]
    ordinary_output_scope(
        selected,
        scopes
        + [scope for view in views.values() for scope in view["scopes"].values()],
    )
    observations = []
    total = 0
    maximum = min(ceiling["max_results"], selected.session["budgets"]["max_results"])
    for ordinal, step in enumerate(request["steps"]):
        live()
        operation = step["operation"]
        if operation in OPERATIONS:
            payload = strict_json(query_local(selected, step))
        else:
            handler = (
                resolve_evidence if operation == "evidence" else resolve_source_evidence
            )
            payload = handler(selected, **step["citation"])
        live()
        scopes.append(payload["scope"])
        total += observation_count(operation, payload)
        if total > maximum:
            raise ContractError("RESEARCH_BUDGET: cumulative result budget exceeded")
        observations.append(
            {"step": ordinal + 1, "operation": operation, "payload": payload}
        )
        if len(canonical_json(observations)) > ceiling["max_bytes"]:
            raise ContractError(
                "RESEARCH_BUDGET: cumulative observations exceed the byte budget"
            )
    result = {
        "schema": "mindgarden.research-result/v1",
        "id": request["id"],
        "request_sha256": digest_bytes(canonical_json(request)),
        "authority_sha256": selected.scope_digest(),
        "inputs": request["gardens"],
        "scope": ordinary_output_scope(selected, scopes),
        "policy": selected.session["policy"],
        "expires_at": request["expires_at"],
        "trust": "untrusted-evidence",
        "planner": request["planner"],
        "status": "observations-available" if total else "insufficient-evidence",
        "observations": observations,
        "interpretations": [],
        "usage": {"steps": len(observations), "results": total, "model_calls": 0},
        "coverage": "selected-authorized-revisions-only",
        "limitations": [
            "Observations are not an answer, completeness certification or knowledge approval.",
            "No evidence of denied records, unsearched sources or latest provider state is inferred.",
            "Lexical matches and authorized graph links do not establish semantic relevance or factual certainty.",
            "Missing, conflicting or stale evidence requires fresh selection and review; no automatic resolution.",
            "No persisted trace/cache or model call; external consumer execution/network policy is separate.",
        ],
    }
    if ContractRegistry().errors(result, "research-result"):
        raise ContractError(
            "RESEARCH_INVALID: result violates the supported observation contract"
        )
    content = canonical_json(result)
    if len(content) > ceiling["max_bytes"]:
        raise ContractError(
            "RESEARCH_BUDGET: complete result metadata exceeds the byte budget"
        )
    live()
    selected.ensure_output(content)
    live()
    return result


def run_research(arguments):
    raw = authority_bytes(arguments.input)
    if len(raw) > 2_000_000:
        raise ContractError("RESEARCH_BUDGET: request exceeds the metadata ceiling")
    request = strict_json(raw)
    validate_request(request)
    context = QueryContext.load(
        arguments.local_config,
        arguments.scope,
        garden_ids={item["garden"] for item in request["gardens"]},
    )

    def verify():
        if authority_bytes(arguments.input) != raw:
            raise ContractError(
                "RESEARCH_STALE: supplied request changed during research"
            )

    result = research(context, request, verify_request=verify)
    content = canonical_json(result)
    context.ensure_output(content)
    verify()
    print(content.decode(), end="")
    return 0
