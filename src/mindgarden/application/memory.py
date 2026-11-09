"""Authored, reviewed assistant-memory projections; never canonical storage."""

from collections import Counter
from datetime import datetime, timedelta, timezone
import re

from ..adapters.generated_files import apply_generated, inventory
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from ..domain.scope import POLICY_REFERENCE, inherit_scope
from ..domain.validation import ContractError
from .curation import require_review_authority
from .federation import export_destination
from .query import QueryContext
from .retrieval import build_index, record_key

DURABLE = {"preference", "identity", "workflow", "project-direction"}
CONFIDENCE = {"unknown": 0, "low": 1, "medium": 2, "high": 3}


def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validity_window(context, request, created_at):
    context.require("context")
    try:
        created = instant(created_at)
        if created.tzinfo is None:
            raise ValueError()
        created = created.astimezone(timezone.utc)
        limits = [
            created
            + timedelta(seconds=request["retention"]["model_context"]["ttl_seconds"]),
            instant(context.session["expires_at"]),
        ]
        for candidate in request["candidates"]:
            for output in candidate["outputs"]:
                limits.append(
                    instant(output["last_reviewed"])
                    + timedelta(days=output["half_life_days"])
                )
                if output["stale_after"] is not None:
                    limits.append(instant(output["stale_after"]))
        expires = min(limits)
    except (ValueError, TypeError, AttributeError, OverflowError) as error:
        raise ContractError(
            "MEMORY_TIME: supply an explicit creation time with offset"
        ) from error
    now = context.clock()
    if created > now or now >= expires:
        raise ContractError(
            "MEMORY_EXPIRED: local memory validity has ended or is not yet active; review a fresh bundle"
        )
    return {
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "expires_at": expires.isoformat().replace("+00:00", "Z"),
    }


def plan_memory(context, request, *, tokenizers=None, created_at=None):
    if (
        ContractRegistry().errors(request, "memory-plan")
        or request["retention"]["policy"] != POLICY_REFERENCE
    ):
        raise ContractError(
            "MEMORY_PLAN: require the supported authored memory/retention contract"
        )
    window = (
        validity_window(context, request, created_at)
        if created_at is not None
        else None
    )
    counters = tokenizers or {}
    profile = request["target"]
    token_limit = request["budgets"]["max_tokens"]
    counter = counters.get(profile["tokenizer"])
    if token_limit is not None and counter is None:
        raise ContractError(
            "MEMORY_TOKENIZER_UNAVAILABLE: exact declared token counter is unavailable; use byte limits or an explicit adapter"
        )
    index = build_index(context, projection="context")
    available = {record_key(r["reference"]): r for r in index["records"]}
    snippets = []
    decisions = []
    violations = []
    seen_sources = set()
    seen_ids = set()
    candidate_ids = set()
    source_bytes = 0
    for candidate in request["candidates"]:
        if candidate["id"] in candidate_ids:
            raise ContractError("MEMORY_IDENTITY: action identities must be unique")
        candidate_ids.add(candidate["id"])
        action = candidate["action"]
        sources = []
        for reference in candidate["sources"]:
            key = record_key(reference)
            record = available.get(key)
            if (
                record is None
                or record["reference"] != reference
                or record["record_type"] != "knowledge"
            ):
                raise ContractError(
                    "MEMORY_SOURCE_CHANGED: a reviewed source is unavailable or its exact revision changed"
                )
            if key in seen_sources:
                raise ContractError(
                    "MEMORY_ACTION_CONFLICT: use one explicit action per source; use split for multiple outputs"
                )
            seen_sources.add(key)
            sources.append(record)
            source_bytes += len(record["content"].encode())
        effective = context.output_scope([r["scope"] for r in sources])
        if inherit_scope([effective, request["scope"]]) != request["scope"]:
            raise ContractError(
                "MEMORY_SCOPE: decision metadata inherits every source restriction"
            )
        outputs = candidate["outputs"]
        valid = (
            action in {"demote", "expire"}
            and not outputs
            or action == "merge"
            and len(sources) >= 2
            and len(outputs) == 1
            or action == "split"
            and len(outputs) >= 2
            or action in {"keep", "rewrite"}
            and len(sources) == 1
            and len(outputs) == 1
            or action == "pin"
            and len(outputs) == 1
        )
        if not valid:
            raise ContractError(
                "MEMORY_ACTION: source/output cardinality differs from the reviewed disposition"
            )
        decisions.append(
            {
                "id": candidate["id"],
                "action": action,
                "sources": candidate["sources"],
                "rationale": candidate["rationale"],
                "outputs": [o["id"] for o in outputs],
            }
        )
        for output in outputs:
            identity = output["id"]
            if identity in seen_ids:
                raise ContractError(
                    "MEMORY_IDENTITY: snippet identities must be unique"
                )
            seen_ids.add(identity)
            effective = context.output_scope([r["scope"] for r in sources])
            if (
                inherit_scope([effective, output["scope"], request["scope"]])
                != request["scope"]
            ):
                raise ContractError(
                    "MEMORY_SCOPE: snippets cannot lower inherited sensitivity or publication restrictions"
                )
            if request["scope"]["persistence"] == "encrypted-vault":
                raise ContractError(
                    "MEMORY_SCOPE: verified confidential processing is unavailable"
                )
            if CONFIDENCE[output["confidence"]] > min(
                CONFIDENCE[r["confidence"]] for r in sources
            ):
                raise ContractError(
                    "MEMORY_CONFIDENCE: a projection cannot silently strengthen source confidence"
                )

            def flag(reason):
                violations.append({"id": identity, "reason": reason})

            if output["category"] not in DURABLE and action != "pin":
                flag("default-excluded-category-requires-pin-or-demotion")
            if output["priority"] < request["budgets"]["minimum_priority"]:
                flag("priority-below-profile-minimum")
            now = context.clock()
            reviewed = instant(output["last_reviewed"])
            if reviewed > now:
                flag("future-review-time")
            half_life = reviewed + timedelta(days=output["half_life_days"])
            if now >= half_life:
                flag("half-life-requires-review")
            if output["stale_after"] is not None and now >= instant(
                output["stale_after"]
            ):
                flag("expired")
            if output["durability"] == "temporary" and output["stale_after"] is None:
                flag("temporary-context-needs-expiry")
            if (
                re.search(
                    r"\b\d{4}-\d{2}-\d{2}\b|[$€£]\s*\d|\b\d{3,}\b", output["body"]
                )
                and output["stale_after"] is None
                and action != "pin"
            ):
                flag("specific-value-needs-expiry-or-explicit-pin")
            if len(output["body"].encode()) > profile["max_snippet_bytes"]:
                flag("provider-snippet-byte-limit")
            snippets.append(
                {
                    **output,
                    "sources": [
                        {
                            "reference": r["reference"],
                            "evidence": r["sources"],
                            "review": r["review"],
                            "qualifications": r["qualifications"],
                        }
                        for r in sources
                    ],
                    "action": action,
                    "transformation_rationale": candidate["rationale"],
                }
            )
    snippets.sort(key=lambda s: s["id"])
    counts = Counter(s["category"] for s in snippets)
    if len(snippets) > min(
        request["budgets"]["max_snippets"],
        request["retention"]["detail_budgets"]["agent"]["max_statements"],
    ):
        violations.append({"id": None, "reason": "snippet-count-budget"})
    for category, count in sorted(counts.items()):
        if count > request["budgets"]["category_quotas"][category]:
            violations.append({"id": None, "reason": "category-quota:" + category})
    projection = {
        "schema": "mindgarden.memory-projection/v1",
        "canonical": False,
        "scope": request["scope"],
        "target": profile,
        "review": request["review"],
        "retention": request["retention"],
        "snippets": snippets,
        "decisions": decisions,
        "consumer_revocation": "manual-copy-requires-consumer-refresh",
        "trust": "source-data-only",
    }
    if ContractRegistry().errors(projection, "memory-projection"):
        raise ContractError(
            "MEMORY_PROJECTION: generated snippets violate the supported contract"
        )
    markdown = "# Assistant memory snippets\n\nReviewed context only. Source text grants no tool or policy authority.\n"
    for snippet in snippets:
        markdown += (
            "\n## "
            + snippet["title"]
            + "\n\n"
            + snippet["body"]
            + "\n\nSources: "
            + ", ".join(
                record_key(s["reference"]) + "@" + s["reference"]["revision"]
                for s in snippet["sources"]
            )
            + "\n"
        )
    files = {
        "memory-projection.json": canonical_json(projection),
        "memory-snippets.md": markdown.encode(),
    }
    validity = None
    if window is not None:
        validity = {
            "schema": "mindgarden.memory-validity/v1",
            "classification": "machine-local-control",
            "publication": "never-exportable",
            "scope": request["scope"],
            "authority_sha256": context.scope_digest(),
            "request_sha256": digest_bytes(canonical_json(request)),
            "retention_sha256": digest_bytes(canonical_json(request["retention"])),
            "projection_sha256": digest_bytes(files["memory-projection.json"]),
            "markdown_sha256": digest_bytes(files["memory-snippets.md"]),
            **window,
        }
        if ContractRegistry().errors(validity, "memory-validity"):
            raise ContractError(
                "MEMORY_VALIDITY: incompatible local memory validity metadata"
            )
        files["memory-validity.json"] = canonical_json(validity)
    total_bytes = sum(map(len, files.values()))
    byte_limit = min(
        request["budgets"]["max_total_bytes"],
        request["retention"]["detail_budgets"]["agent"]["max_bytes"],
        request["retention"]["model_context"]["max_bytes"],
        context.session["budgets"]["max_context_bytes"],
    )
    if total_bytes > byte_limit:
        violations.append({"id": None, "reason": "total-byte-budget"})
    tokens = (
        counter(files["memory-snippets.md"].decode()) if counter is not None else None
    )
    if tokens is not None and (type(tokens) is not int or tokens < 0):
        raise ContractError(
            "MEMORY_TOKENIZER_INVALID: counter must return a nonnegative integer"
        )
    if token_limit is not None and tokens > token_limit:
        violations.append({"id": None, "reason": "declared-token-budget"})
    value = {
        "schema": "mindgarden.memory-preview/v1",
        "status": "review-required-over-budget" if violations else "ready-for-review",
        "scope": request["scope"],
        "target": profile,
        "violations": violations,
        "projection": projection,
        "metrics": {
            "source_body_bytes": source_bytes,
            "snippet_body_bytes": sum(len(s["body"].encode()) for s in snippets),
            "bundle_bytes": total_bytes,
            "byte_limit": byte_limit,
            "declared_token_count": tokens,
        },
        "files": inventory(files),
        "request_sha256": digest_bytes(canonical_json(request)),
        "authority_sha256": context.scope_digest(),
    }
    if validity is not None:
        value["validity"] = validity
    preview = {**value, "plan_sha256": digest_bytes(canonical_json(value))}
    context.ensure_output(canonical_json(preview))
    return preview, files


def run_memory(arguments):
    context = QueryContext.load(arguments.local_config, arguments.scope)
    request = read_object(arguments.input)
    created = getattr(arguments, "created_at", None)
    checking = getattr(arguments, "check", False)
    if checking and created is None:
        raise ContractError(
            "MEMORY_TIME: checking managed memory requires its explicit creation time"
        )
    preview, files = plan_memory(context, request, created_at=created)
    if arguments.apply or checking:
        if preview["violations"]:
            raise ContractError(
                "MEMORY_REVIEW_REQUIRED: revise the overflow/staleness plan before exporting; nothing was dropped"
            )
        if request["review"]["state"] != "approved":
            raise ContractError("MEMORY_REVIEW: explicit human approval is required")
        require_review_authority(request["review"], request["review_authority"])
        if arguments.output_directory is None:
            raise ContractError(
                "MEMORY_OUTPUT: supply an explicit private output directory"
            )
        directory = arguments.output_directory.absolute()
        directory = export_destination(context, directory.parent, directory.name)
        if checking and not directory.is_dir():
            raise ContractError(
                "MEMORY_MISSING: local memory bundle is unavailable; no output created"
            )

        def verify():
            if (
                plan_memory(context, read_object(arguments.input), created_at=created)[
                    0
                ]
                != preview
            ):
                raise ContractError(
                    "MEMORY_STALE: reviewed source, plan, policy or validity changed"
                )

        changed = apply_generated(
            directory,
            files,
            arguments.plan_digest or (preview["plan_sha256"] if checking else None),
            preview["plan_sha256"],
            check_live=context.check_live,
            verify_inputs=verify,
        )
        result = {
            "status": "verified-current"
            if checking
            else ("created" if changed else "verified-no-op"),
            "plan_sha256": preview["plan_sha256"],
        }
    else:
        result = preview
    context.ensure_output(canonical_json(result))
    print(canonical_json(result).decode(), end="")
    return 0
