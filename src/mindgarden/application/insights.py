"""Reviewed renderer-independent insight handoffs; no rendering or publication."""

from copy import deepcopy

from ..adapters.generated_files import apply_generated, inventory
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from ..domain.publication import permits_publication
from ..domain.validation import ContractError
from .curation import require_review_authority
from .query import QueryContext
from .reviewed_selection import (
    selection_view,
    select_records,
    source_trail,
    qualification_reasons,
    selected_digest,
)


def candidate_revision(candidate):
    """Artifact feedback binds content and rights, not its changing display state."""
    return digest_bytes(
        canonical_json(
            {k: v for k, v in candidate.items() if k not in {"lifecycle", "review"}}
        )
    )


def require_public(context):
    session = context.session
    if (
        session["allowed_visibilities"] != ["public"]
        or session["allowed_review_states"] != ["approved"]
        or session.get("request_scope", {}).get("visibility") != "public"
        or session["publication_authority"] != "publishable"
    ):
        raise ContractError(
            "INSIGHT_SCOPE: explicit public-only reviewed handoff authority is required"
        )


def plan_insights(context, request):
    contracts = ContractRegistry()
    if contracts.errors(request, "insight-plan"):
        raise ContractError(
            "INSIGHT_PLAN: use the versioned authored candidate/series/feedback contract"
        )
    require_public(context)
    index, snapshots = selection_view(context)
    available = {}
    exported = []
    duplicates = []
    fingerprints = {}
    authority = request["review_authority"]
    excluded = []
    for candidate in sorted(request["candidates"], key=lambda c: c["id"]):
        identity = candidate["id"]
        if identity in available:
            if candidate != available[identity]:
                raise ContractError(
                    "INSIGHT_IDENTITY: conflicting versions require distinct candidate identities"
                )
            duplicates.append({"candidate": identity, "canonical_candidate": identity})
            continue
        available[identity] = candidate
        if any(
            item == identity or item not in {c["id"] for c in request["candidates"]}
            for item in candidate["supersedes"]
        ):
            raise ContractError(
                "INSIGHT_SUPERSEDES: supersession must name a different supplied candidate"
            )
        references = []
        for claim in candidate["claims"]:
            for reference in claim["references"]:
                if reference not in references:
                    references.append(reference)
        records = select_records(index, snapshots, references)
        if candidate["garden"] not in {r["garden"] for r in records}:
            raise ContractError(
                "INSIGHT_HOME: canonical garden must be represented by selected evidence"
            )
        for record in records:
            scope = record["scope"]
            policy = snapshots[record["garden"]].manifest["publication"]
            if (
                scope["visibility"] != "public"
                or scope["publication"] != "publishable"
                or not permits_publication(
                    policy,
                    kind=record["kind"],
                    domains=record["domains"],
                    topics=record["topics"],
                )
            ):
                raise ContractError(
                    "INSIGHT_PRIVACY: only reviewed public derivations with public-safe evidence are supported"
                )
            if record["record_type"] == "claim":
                subject = snapshots[record["garden"]].records[record["id"]]["subject"]
                if not any(
                    r["garden"] == subject["garden"] and r["id"] == subject["id"]
                    for r in records
                ):
                    raise ContractError(
                        "INSIGHT_SELECTION: a selected claim requires its reviewed subject"
                    )
        require_review_authority(candidate["review"], authority)
        rights = [
            candidate["rights"],
            *[claim["rights"] for claim in candidate["claims"]],
        ]
        for entry in rights:
            require_review_authority(entry["review"], authority)
        if candidate["lifecycle"] in {"proposed", "rejected", "superseded"}:
            if (
                candidate["lifecycle"] == "rejected"
                and candidate["review"]["state"] != "rejected"
            ):
                raise ContractError(
                    "INSIGHT_REVIEW: rejection requires explicit human review"
                )
            excluded.append({"candidate": identity, "reason": candidate["lifecycle"]})
            continue
        if candidate["review"]["state"] != "approved" or any(
            r["status"] != "approved" or r["review"]["state"] != "approved"
            for r in rights
        ):
            raise ContractError(
                "INSIGHT_RIGHTS: handoff requires human-reviewed candidate and claim-level rights"
            )
        transformed = deepcopy(candidate)
        for claim in transformed["claims"]:
            claim_records = select_records(index, snapshots, claim["references"])
            reasons = qualification_reasons(claim_records)
            if claim["representation"] == "inference":
                reasons.append("derived-inference")
            if reasons and claim["certainty"] != "qualified":
                raise ContractError(
                    "INSIGHT_QUALIFICATION: uncertain or contradictory support requires a qualified teaching claim"
                )
            if claim["representation"] == "quoted" and not any(
                claim["text"] in r["content"] for r in claim_records
            ):
                raise ContractError(
                    "INSIGHT_QUOTE: quoted text must match the selected reviewed content"
                )
        transformed["uncertainty"] = sorted(
            set(candidate["uncertainty"])
            | {
                u
                for r in records
                for u in r["qualifications"]["caveats"]
                + r["qualifications"]["uncertainty"]
            }
        )
        # Candidate identity is user-owned; content fingerprint detects duplicate proposals.
        fingerprint = digest_bytes(
            canonical_json(
                {
                    k: v
                    for k, v in candidate.items()
                    if k not in {"id", "review", "lifecycle", "supersedes"}
                }
            )
        )
        if fingerprint in fingerprints:
            duplicates.append(
                {
                    "candidate": identity,
                    "canonical_candidate": fingerprints[fingerprint],
                }
            )
            continue
        fingerprints[fingerprint] = identity
        exported.append(
            {
                "candidate": transformed,
                "revision": candidate_revision(candidate),
                "sources": source_trail(records),
                "qualification_reasons": qualification_reasons(records),
                "source_digest": selected_digest(records),
                "artifact_events": [],
            }
        )
    by_id = {item["candidate"]["id"]: item for item in exported}
    superseded = {
        old
        for c in request["candidates"]
        if c["lifecycle"] in {"approved", "published"}
        for old in c["supersedes"]
    }
    for old in superseded:
        if available[old]["lifecycle"] != "superseded":
            raise ContractError(
                "INSIGHT_SUPERSEDES: the replaced candidate must be explicitly marked superseded"
            )
    seen_events = set()
    for event in request["artifact_events"]:
        if event["id"] in seen_events:
            raise ContractError("INSIGHT_EVENT: duplicate artifact event identity")
        seen_events.add(event["id"])
        target = by_id.get(event["candidate"])
        if target is None or event["candidate_revision"] != target["revision"]:
            raise ContractError(
                "INSIGHT_EVENT: artifact feedback requires the exact exported candidate version"
            )
        require_review_authority(event["review"], authority)
        if event["review"]["state"] != "approved" or (
            event["state"] in {"rendered", "published"} and not event["artifacts"]
        ):
            raise ContractError(
                "INSIGHT_EVENT: artifact feedback requires approved human review and declared artifacts"
            )
        target["artifact_events"].append(event)
    for item in exported:
        if item["candidate"]["lifecycle"] == "published" and not any(
            e["state"] == "published" for e in item["artifact_events"]
        ):
            raise ContractError(
                "INSIGHT_EVENT: published state requires reviewed artifact feedback"
            )
        item["artifact_events"].sort(key=lambda e: e["id"])
    series = []
    seen_series = set()
    for entry in sorted(request["series"], key=lambda s: s["id"]):
        if entry["id"] in seen_series or len(set(entry["candidates"])) != len(
            entry["candidates"]
        ):
            raise ContractError(
                "INSIGHT_SERIES: series identities and ordered members must be unique"
            )
        seen_series.add(entry["id"])
        require_review_authority(entry["review"], authority)
        if entry["review"]["state"] != "approved" or any(
            c not in by_id for c in entry["candidates"]
        ):
            raise ContractError(
                "INSIGHT_SERIES: all series members must be eligible reviewed candidates"
            )
        series.append(entry)
    projection = {
        "schema": "mindgarden.insight-projection/v1",
        "canonical": False,
        "scope": context.output_scope(
            [r["scope"] for item in exported for r in item["sources"]]
        ),
        "trust": "source-data-only",
        "candidates": exported,
        "series": series,
        "duplicates": duplicates,
        "artifact_verification": "declared-not-fetched",
    }
    if contracts.errors(projection, "insight-projection"):
        raise ContractError(
            "INSIGHT_PROJECTION: output violates the versioned producer contract"
        )
    files = {"insight-candidates.json": canonical_json(projection)}
    size = sum(map(len, files.values()))
    if size > min(
        request["max_bytes"], context.session["budgets"]["max_context_bytes"]
    ):
        raise ContractError(
            "INSIGHT_BUDGET: complete claims and provenance exceed the explicit bound"
        )
    value = {
        "schema": "mindgarden.insight-preview/v1",
        "projection": projection,
        "excluded": excluded,
        "files": inventory(files),
        "total_bytes": size,
        "authority_sha256": context.scope_digest(),
        "request_sha256": digest_bytes(canonical_json(request)),
    }
    preview = {**value, "plan_sha256": digest_bytes(canonical_json(value))}
    context.ensure_output(canonical_json(preview))
    return preview, files


def run_insights(arguments):
    context = QueryContext.load(arguments.local_config, arguments.scope)
    request = read_object(arguments.input)
    preview, files = plan_insights(context, request)
    if arguments.apply:
        if request["review"]["state"] != "approved":
            raise ContractError(
                "INSIGHT_REVIEW: applying a handoff requires explicit human plan review"
            )
        require_review_authority(request["review"], request["review_authority"])
        if arguments.output_directory is None:
            raise ContractError(
                "INSIGHT_OUTPUT: supply a new private staging directory"
            )

        def verify():
            if plan_insights(context, read_object(arguments.input))[0] != preview:
                raise ContractError(
                    "INSIGHT_STALE: source, rights, feedback or authority changed"
                )

        changed = apply_generated(
            arguments.output_directory,
            files,
            arguments.plan_digest,
            preview["plan_sha256"],
            check_live=context.check_live,
            validate_output=context.ensure_bundle,
            verify_inputs=verify,
        )
        result = {
            "status": "created" if changed else "verified-no-op",
            "plan_sha256": preview["plan_sha256"],
        }
    else:
        result = preview
    context.ensure_output(canonical_json(result))
    print(canonical_json(result).decode(), end="")
    return 0
