"""Reviewed private moves and merge retirement without overwriting original records."""

from copy import deepcopy
from pathlib import Path

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object
from ..domain.routing_transitions import retired_references
from ..domain.scope import inherit_scope, record_scope
from ..domain.validation import ContractError
from .bindings import LocalBindings, garden_fingerprint
from .changes import ChangePlan
from .curation import build_curation_plan, require_review_authority
from .records import artifact_reference, provenance_record
from .routing import RoutingPlan, snapshots_for


def build_transition_plan(bindings: LocalBindings, request_path: Path) -> RoutingPlan:
    if request_path.is_symlink():
        raise ContractError("ROUTE_PATH: transition request must be a regular explicit file")
    request = read_object(request_path)
    if ContractRegistry().errors(request, "routing-transition"):
        raise ContractError("ROUTE_TRANSITION_INVALID: request does not conform")
    require_review_authority(request["review"], request["authority"])
    if request["review"]["state"] != "approved":
        raise ContractError("REVIEW_AUTHORITY: transition requires approved human review")
    if (request["operation"] == "move" and len(request["from"]) != 1
            or request["operation"] == "merge" and len(request["from"]) < 2):
        raise ContractError("ROUTE_TRANSITION_INVALID: move requires one input; merge requires distinct inputs")
    snapshots = snapshots_for(bindings)
    retired = retired_references(record for snapshot in snapshots.values() for record in snapshot.records.values())
    request_digest = digest_bytes(request_path.read_bytes())

    def resolve(reference):
        owner = snapshots.get(reference["garden"])
        record = owner.records.get(reference["id"]) if owner else None
        if (record is None or record["schema"] != "mindgarden.knowledge/v1"
                or reference["revision"] != "sha256:" + owner.hashes[reference["id"]]):
            raise ContractError("PLAN_STALE: transition requires exact available knowledge revisions")
        if record["status"] != "active" or record["review"]["state"] != "approved":
            raise ContractError("REVIEW_AUTHORITY: only reviewed active knowledge can transition")
        prior = retired.get((reference["garden"], reference["id"]))
        if prior and prior["request_sha256"] != request_digest:
            raise ContractError("ROUTE_TRANSFER_REQUIRED: input already transitioned; use its current canonical home")
        return record

    inputs = [resolve(reference) for reference in request["from"]]
    destination = request["to"]
    target_binding = bindings.garden(destination["garden"])
    scope = inherit_scope([target_binding["scope"], *[record_scope(record, bindings.garden(record["garden"])["scope"])
                                                   for record in inputs]])
    if (scope["visibility"] != "personal" or scope["persistence"] == "encrypted-vault"
            or any(bindings.garden(record["garden"])["scope"] != target_binding["scope"] for record in inputs)
            or any(record_scope(record, bindings.garden(record["garden"])["scope"]) != scope for record in inputs)):
        raise ContractError("ROUTE_TRANSITION_SCOPE: this checkpoint requires matching ordinary personal policies")
    if any((reference["garden"], reference["id"]) == (destination["garden"], destination["id"]) for reference in request["from"]):
        raise ContractError("ROUTE_TRANSITION_CYCLE: destination must differ from all original identities")
    changes = {}
    if request["operation"] == "move":
        original = inputs[0]
        if original["claims"] or original["synapses"] or original.get("x-curation", {}).get("contradictions"):
            raise ContractError("ROUTE_TRANSITION_COMPLEX: curate attached claims and relationships explicitly before transfer")
        body = snapshots[original["garden"]].contents[original["id"]].decode("utf8")
        exact_target = artifact_reference(destination["garden"], destination["id"], digest_bytes(body.encode()))
        if destination["revision"] not in {None, exact_target["revision"]}:
            raise ContractError("PLAN_STALE: destination revision differs from the retained body")
        qualifications = original.get("x-curation", {})
        output = {field: deepcopy(original[field]) for field in ("title", "kind", "confidence", "authors", "domains", "topics")}
        output.update(id=destination["id"], body=body, status="active", review=request["review"], claims=[], synapses=[],
                      aliases=original["aliases"], tags=original["tags"],
                      epistemic_state=qualifications.get("epistemic_state", "unverified"),
                      attribution=qualifications.get("attribution", "mixed"),
                      caveats=qualifications.get("caveats", []), uncertainty=qualifications.get("uncertainty", []), contradictions=[])
        if qualifications.get("redactions"):
            output["redactions"] = qualifications["redactions"]
        proposal = {"schema":"mindgarden.curation-plan/v1", "id":"transfer-" + request["id"],
                    "garden":destination["garden"], "created_at":request["created_at"], "producer":request["authority"],
                    "review_authority":request["authority"], "candidates":[{"id":"transfer-candidate", "action":"keep",
                    "rationale":request["rationale"], "sources":original["sources"], "merge_inputs":request["from"], "output":output}]}
        changes[destination["garden"]] = build_curation_plan(bindings, request_path, supplied_proposal=proposal,
            authorized_snapshots=snapshots, canonical_routing={"unit":original.get("x-routing", {}).get("unit", original["garden"] + "/" + original["id"]),
            "role":"canonical", "canonical_home":exact_target})
    else:
        target = resolve(destination); exact_target = destination
        if record_scope(target, target_binding["scope"]) != scope:
            raise ContractError("ROUTE_TRANSITION_SCOPE: merged target policy must match contributing policies")
        lineage = [item["artifact"] for reference in target["provenance"]
                   for item in snapshots[reference["garden"]].records[reference["id"]]["inputs"]]
        if not all(reference in lineage for reference in request["from"]):
            raise ContractError("ROUTE_MERGE_LINEAGE: curate the merged output with every exact original before retiring inputs")
    checks = [(request_path.absolute(), request_digest), (bindings.path, digest_bytes(bindings.path.read_bytes()))]
    for reference in request["from"]:
        garden = reference["garden"]
        event = {"request_sha256":request_digest, "operation":request["operation"], "from":reference,
                 "to":exact_target, "review":request["review"], "authority":request["authority"], "rationale":request["rationale"]}
        receipt = provenance_record(garden, "transition-" + request["id"] + "-" + digest_bytes(canonical_json(reference))[:16],
            reference["id"], reference["revision"][7:], inputs=[{"artifact":exact_target, "sha256":exact_target["revision"][7:], "role":"source"}],
            transformations=({"name":"review-canonical-transition", "version":"1.0.0", "parameters":{"request_sha256":request_digest}},),
            created_at=request["created_at"], rights="Private canonical-home transition; original rights remain authoritative.", origin=None, scope=scope)
        receipt["x-routing-transition"] = event
        if garden not in changes:
            changes[garden] = ChangePlan("route", garden, bindings.garden(garden)["root"],
                                        {"garden_revision":garden_fingerprint(bindings.garden(garden)["root"])}, {})
        changes[garden].files["provenance/" + receipt["id"] + ".json"] = canonical_json(receipt)
    for plan in changes.values():
        plan.source_checks = checks
        plan.verify(plan.digest)
    return RoutingPlan(bindings, {"request_sha256":request_digest, "garden_revisions":{
        garden:garden_fingerprint(binding["root"]) for garden,binding in sorted(bindings.gardens.items())}},
        [{"state":"reviewed-" + request["operation"], "originals":request["from"], "canonical_home":exact_target,
          "rationale":request["rationale"], "preservation":"original records and exact references retained"}], changes)
