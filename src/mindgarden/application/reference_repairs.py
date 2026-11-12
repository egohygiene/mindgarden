"""Digest-bound, append-only repairs after matching-policy private transitions."""

from copy import deepcopy

from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from ..domain.reference_repairs import repair_history
from ..domain.routing_transitions import canonical_reference, retired_references
from ..domain.scope import record_scope
from ..domain.validation import ContractError
from .bindings import garden_fingerprint
from .changes import ChangePlan
from .curation import require_review_authority
from .records import artifact_reference, provenance_record
from .routing import RoutingPlan, snapshots_for


def build_reference_repair_plan(bindings, request_path):
    if request_path.is_symlink():
        raise ContractError("ROUTE_PATH: repair request must be a regular private file")
    request = read_object(request_path)
    registry = ContractRegistry()
    if registry.errors(request, "reference-repair"):
        raise ContractError(
            "ROUTE_REPAIR_INVALID: supply a versioned exact repair request"
        )
    require_review_authority(request["review"], request["authority"])
    if request["review"]["state"] != "approved":
        raise ContractError(
            "REVIEW_AUTHORITY: reference repair requires explicit approval"
        )
    snapshots = snapshots_for(bindings)
    records = {
        (garden, identity): record
        for garden, snapshot in snapshots.items()
        for identity, record in snapshot.records.items()
    }
    retired = retired_references(records.values())
    previous = repair_history(records.values())
    digest = digest_bytes(request_path.read_bytes())
    checks = [
        (request_path.absolute(), digest),
        (bindings.path, digest_bytes(bindings.path.read_bytes())),
    ]
    changes, decisions, seen = {}, [], set()

    def resolve(reference, kind):
        owner = snapshots.get(reference["garden"])
        record = owner.records.get(reference["id"]) if owner else None
        if (
            record is None
            or record["schema"] != "mindgarden." + kind + "/v1"
            or reference["revision"] != "sha256:" + owner.hashes[record["id"]]
        ):
            raise ContractError(
                "PLAN_STALE: repair requires an exact available represented revision"
            )
        if record.get("status") != "active" or record["review"]["state"] != "approved":
            raise ContractError(
                "REVIEW_AUTHORITY: repair dependencies require active reviewed records"
            )
        return record

    for item in request["repairs"]:
        old = resolve(item["edge"], "synapse")
        identity = old["garden"], old["id"]
        if identity in seen:
            raise ContractError("ROUTE_REPAIR_DUPLICATE: select a relationship once")
        seen.add(identity)
        if identity in previous and previous[identity]["request_sha256"] != digest:
            raise ContractError(
                "ROUTE_REPAIR_CONFLICT: review the existing replacement before another repair"
            )
        source = resolve(item["source"], "knowledge")
        historical = resolve(item["historical_target"], "knowledge")
        target = resolve(item["canonical_target"], "knowledge")
        if (
            old["source"] != item["source"]
            or old["target"] != item["historical_target"]
            or (source["garden"], source["id"]) in retired
            or (target["garden"], target["id"]) in retired
            or item["historical_target"] == item["canonical_target"]
            or canonical_reference(item["historical_target"], records.values())
            != item["canonical_target"]
        ):
            raise ContractError(
                "ROUTE_REPAIR_TARGET: name the exact historical edge and its current reviewed successor"
            )
        scope = bindings.garden(old["garden"])["scope"]
        dependencies = [old, source, historical, target]
        for evidence in old["evidence"]:
            ref = evidence["source"]
            owner = snapshots.get(ref["garden"])
            record = owner.records.get(ref["id"]) if owner else None
            if record is None or ref["revision"] != "sha256:" + owner.hashes[ref["id"]]:
                raise ContractError("PLAN_STALE: relationship evidence changed")
            dependencies.append(record)
        if (
            scope["visibility"] != "personal"
            or scope["persistence"] == "encrypted-vault"
            or any(
                bindings.garden(r["garden"])["scope"] != scope
                or record_scope(r, scope) != scope
                for r in dependencies
            )
        ):
            raise ContractError(
                "ROUTE_REPAIR_SCOPE: matching ordinary personal policies are required"
            )
        required = {"mindgarden.synapse/v1", "mindgarden.provenance/v1"}
        if any(
            not required <= set(snapshots[old["garden"]].manifest["contracts"][field])
            for field in ("reads", "writes")
        ):
            raise ContractError(
                "CAPABILITY_UNDECLARED: repair owner must declare relationship and provenance contracts"
            )
        event_id = (
            "reference-repair-"
            + digest_bytes(canonical_json({"request": digest, "edge": item["edge"]}))[
                :32
            ]
        )
        replacement = deepcopy(old)
        replacement.update(
            id=item["replacement_id"],
            target=item["canonical_target"],
            review=request["review"],
        )
        replacement["x-reference-repair-event"] = artifact_reference(
            old["garden"], event_id
        )
        replacement["x-repair-rationale"] = item["rationale"]
        if replacement["id"] == old["id"]:
            raise ContractError(
                "ROUTE_REPAIR_DUPLICATE: replacement requires a new immutable identity"
            )
        replacement_ref = artifact_reference(
            old["garden"], replacement["id"], digest_bytes(canonical_json(replacement))
        )
        inputs = [
            item["edge"],
            item["source"],
            item["historical_target"],
            item["canonical_target"],
        ]
        current = item["historical_target"]
        while current != item["canonical_target"]:
            transition = retired[(current["garden"], current["id"])]
            lineage = next(
                r
                for _, r in sorted(records.items())
                if r.get("x-routing-transition") == transition
            )
            inputs.append(
                artifact_reference(
                    lineage["garden"],
                    lineage["id"],
                    digest_bytes(canonical_json(lineage)),
                )
            )
            current = transition["to"]
        event = provenance_record(
            old["garden"],
            event_id,
            replacement["id"],
            replacement_ref["revision"][7:],
            inputs=[
                {"artifact": ref, "sha256": ref["revision"][7:], "role": "source"}
                for ref in inputs
            ],
            transformations=(
                {
                    "name": "review-incoming-reference-repair",
                    "version": "1.0.0",
                    "parameters": {
                        "request_sha256": digest,
                        "rationale": item["rationale"],
                    },
                },
            ),
            created_at=request["created_at"],
            rights="Source rights and historical attribution retained.",
            origin=None,
            scope=scope,
        )
        event["x-reference-repair"] = {
            "schema": "mindgarden.reference-repair-event/v1",
            "request_sha256": digest,
            "original": item["edge"],
            "replacement": replacement_ref,
            "source": item["source"],
            "historical_target": item["historical_target"],
            "canonical_target": item["canonical_target"],
            "review": request["review"],
            "authority": request["authority"],
            "rationale": item["rationale"],
        }
        files = {
            "synapses/" + replacement["id"] + ".json": canonical_json(replacement),
            "provenance/" + event_id + ".json": canonical_json(event),
        }
        for record in (replacement, event):
            if registry.errors(record, record["schema"]):
                raise ContractError(
                    "ROUTE_REPAIR_INVALID: generated private repair violates its contract"
                )
            existing = snapshots[old["garden"]].records.get(record["id"])
            if existing is not None and existing != record:
                raise ContractError(
                    "ROUTE_REPAIR_CONFLICT: replacement identity already represents different content"
                )
        if old["garden"] not in changes:
            changes[old["garden"]] = ChangePlan(
                "route",
                old["garden"],
                bindings.garden(old["garden"])["root"],
                {
                    "garden_revision": garden_fingerprint(
                        bindings.garden(old["garden"])["root"]
                    )
                },
                {},
                source_checks=checks,
            )
        for path, content in files.items():
            previous_file = changes[old["garden"]].files.get(path)
            if previous_file is not None and previous_file != content:
                raise ContractError(
                    "ROUTE_REPAIR_DUPLICATE: replacement identity is duplicated"
                )
            changes[old["garden"]].files[path] = content
        decisions.append(
            {
                "state": "reviewed-reference-repair",
                "original": item["edge"],
                "replacement": replacement_ref,
                "canonical_target": item["canonical_target"],
                "type": old["type"],
                "directed": old["directed"],
                "rationale": item["rationale"],
                "preservation": "original edge, evidence, attribution and source owner retained",
            }
        )
    return RoutingPlan(
        bindings,
        {
            "request_sha256": digest,
            "garden_revisions": {
                garden: garden_fingerprint(binding["root"])
                for garden, binding in sorted(bindings.gardens.items())
            },
        },
        decisions,
        changes,
    )
