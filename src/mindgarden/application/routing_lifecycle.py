"""Reviewed private moves and merge retirement without overwriting original records."""

from copy import deepcopy
from pathlib import Path

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object
from ..domain.routing_transitions import retired_references
from ..domain.scope import inherit_scope, record_scope
from ..domain.validation import ContractError
from .bindings import LocalBindings, garden_fingerprint
from .changes import ChangePlan
from .curation import require_review_authority
from .records import artifact_reference, provenance_record
from .routing import RoutingPlan, snapshots_for
from .routing_graph import retain_attached_graph


def build_transition_plan(bindings: LocalBindings, request_path: Path) -> RoutingPlan:
    if request_path.is_symlink():
        raise ContractError("ROUTE_PATH: transition request must be a regular explicit file")
    request = read_object(request_path)
    is_v2 = request.get("schema") == "mindgarden.routing-transition/v2"
    contract = "urn:egohygiene:mindgarden:routing-transition:v2" if is_v2 else "routing-transition"
    if ContractRegistry().errors(request, contract):
        raise ContractError("ROUTE_TRANSITION_INVALID: request does not conform")
    require_review_authority(request["review"], request["authority"])
    if request["review"]["state"] != "approved":
        raise ContractError("REVIEW_AUTHORITY: transition requires approved human review")
    if (request["operation"] in {"move", "split", "supersede"} and len(request["from"]) != 1
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
        body = snapshots[original["garden"]].contents[original["id"]].decode("utf8")
        exact_target = artifact_reference(destination["garden"], destination["id"], digest_bytes(body.encode()))
        if destination["revision"] not in {None, exact_target["revision"]}:
            raise ContractError("PLAN_STALE: destination revision differs from the retained body")
        provenance = provenance_record(destination["garden"], "provenance-transfer-" + request["id"],
            destination["id"], exact_target["revision"][7:],
            inputs=[{"artifact":request["from"][0], "sha256":request["from"][0]["revision"][7:], "role":"source"}],
            transformations=({"name":"retain-knowledge-graph", "version":"1.0.0",
                              "parameters":{"request_sha256":request_digest, "rationale":request["rationale"]}},),
            created_at=request["created_at"], rights="Transferred private knowledge; source rights remain authoritative.",
            origin=None, scope=scope)
        knowledge = deepcopy(original)
        knowledge.update(id=destination["id"], garden=destination["garden"], scope=scope, review=request["review"],
                         updated=request["created_at"][:10], publication="excluded",
                         content={"path":"knowledge/" + destination["id"] + ".md", "sha256":exact_target["revision"][7:]},
                         provenance=[artifact_reference(destination["garden"], provenance["id"], digest_bytes(canonical_json(provenance)))])
        knowledge["x-routing"] = {"unit":original.get("x-routing", {}).get("unit", original["garden"] + "/" + original["id"]),
                                  "role":"canonical", "canonical_home":exact_target}
        files = {knowledge["content"]["path"]:body.encode(), "knowledge/" + knowledge["id"] + ".json":canonical_json(knowledge),
                 "provenance/" + provenance["id"] + ".json":canonical_json(provenance)}
        retain_attached_graph(files, original, snapshots, exact_target, scope, request_digest)
        from ..domain.contracts import strict_json
        for path, content in files.items():
            if path.endswith(".json"):
                record = strict_json(content)
                if ContractRegistry().errors(record, record["schema"]):
                    raise ContractError("ROUTE_GRAPH_INVALID: retained records violate the supported graph contract")
        changes[destination["garden"]] = ChangePlan("route", destination["garden"], target_binding["root"],
            {"garden_revision":garden_fingerprint(target_binding["root"]), "scope":scope}, files)

    else:
        target = resolve(destination); exact_target = destination
        if record_scope(target, target_binding["scope"]) != scope:
            raise ContractError("ROUTE_TRANSITION_SCOPE: merged target policy must match contributing policies")
        lineage = [item["artifact"] for reference in target["provenance"]
                   for item in snapshots[reference["garden"]].records[reference["id"]]["inputs"]]
        if not all(reference in lineage for reference in request["from"]):
            raise ContractError("ROUTE_MERGE_LINEAGE: curate the merged output with every exact original before retiring inputs")
        if request["operation"] == "supersede" and request["from"][0] not in target.get("supersedes", []):
            raise ContractError("ROUTE_SUPERSESSION: explicitly curate the exact supersession relationship before retirement")
        if request["operation"] == "split":
            if target["kind"] not in {"map", "reference"}:
                raise ContractError("ROUTE_SPLIT: select a reviewed reference/map anchor as the single canonical successor")
            seen = {(destination["garden"], destination["id"]), *[(r["garden"], r["id"]) for r in request["from"]]}
            links = [snapshots[ref["garden"]].records[ref["id"]] for ref in target["synapses"]]
            for reference in request["split_targets"]:
                child = resolve(reference)
                identity = reference["garden"], reference["id"]
                if identity in seen or record_scope(child, bindings.garden(reference["garden"])["scope"]) != scope:
                    raise ContractError("ROUTE_SPLIT: distinct reviewed children require the same ordinary private policy")
                seen.add(identity)
                child_lineage = [item["artifact"] for ref in child["provenance"]
                                 for item in snapshots[ref["garden"]].records[ref["id"]]["inputs"]]
                if request["from"][0] not in child_lineage or not any(
                        edge["source"] == destination and edge["type"] in {"references", "part-of"}
                        and edge["target"] == reference and edge["review"]["state"] == "approved" for edge in links):
                    raise ContractError("ROUTE_SPLIT_LINEAGE: anchor must link every exact child and each child must derive from the original")
    checks = [(request_path.absolute(), request_digest), (bindings.path, digest_bytes(bindings.path.read_bytes()))]
    for reference in request["from"]:
        garden = reference["garden"]
        event = {"request_sha256":request_digest, "operation":request["operation"], "from":reference,
                 "to":exact_target, "review":request["review"], "authority":request["authority"], "rationale":request["rationale"]}
        if is_v2:
            event["schema"] = "mindgarden.routing-transition-event/v2"
            if request["operation"] == "split":
                event["split_targets"] = request["split_targets"]
        receipt = provenance_record(garden, "transition-" + request["id"] + "-" + digest_bytes(canonical_json(reference))[:16],
            reference["id"], reference["revision"][7:], inputs=[{"artifact":ref, "sha256":ref["revision"][7:], "role":"source"}
                    for ref in [exact_target, *request.get("split_targets", [])]],
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
        [{**({"split_targets":request["split_targets"]} if request["operation"] == "split" else {}),
          "state":"reviewed-" + request["operation"], "originals":request["from"], "canonical_home":exact_target,
          "rationale":request["rationale"], "preservation":"original records and exact references retained"}], changes)
