"""Read-only compaction proof over existing scoped evidence and curation contracts."""

from ..domain.compaction import evaluate_compaction, node_sources, qualifications, render_node, validate_plan
from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object
from ..domain.validation import ContractError
from .curation import require_review_authority
from .evidence import resolve_evidence
from .query import QueryContext


def validate_curation_bridge(context, plan, proposal):
    if plan["curation_plan_sha256"] is None:
        if proposal is not None or any(node["curation_candidate"] is not None for node in plan["nodes"]):
            raise ContractError("COMPACTION_CURATION: explicit curation pin and bindings are required")
        return []
    if (proposal is None or ContractRegistry().errors(proposal, "curation-plan")
            or digest_bytes(canonical_json(proposal)) != plan["curation_plan_sha256"] or proposal["garden"] != plan["garden"]):
        raise ContractError("COMPACTION_CURATION: exact supported authored curation plan required")
    bound = [node for node in plan["nodes"] if node["curation_candidate"] is not None]
    candidates = {candidate["id"]: candidate for candidate in proposal["candidates"]}
    if len(candidates) != len(proposal["candidates"]) or len({node["curation_candidate"] for node in bound}) != len(bound) or set(candidates) != {node["curation_candidate"] for node in bound}:
        raise ContractError("COMPACTION_CURATION: each supplied candidate needs one explicit hierarchy binding")
    snapshots = context.snapshots()
    results = []
    for node in bound:
        candidate = candidates[node["curation_candidate"]]
        action = {"discard-proposed": "exclude", "supersede": "keep"}.get(node["action"], node["action"])
        if (candidate["action"] != action or candidate["rationale"] != node["rationale"]
                or sorted(candidate["sources"], key=canonical_json) != node_sources(node)):
            raise ContractError("COMPACTION_CURATION: candidate action, rationale and exact evidence must match")
        references = list(candidate["merge_inputs"]) + node["supersedes"]
        output = candidate.get("output")
        if output is not None:
            if action == "reference" and output["kind"] != "reference":
                raise ContractError("COMPACTION_CURATION: reference dispositions require reference knowledge")
            expected = qualifications(node)
            if (output["body"] != render_node(node) or output["claims"] or output["synapses"]
                    or output["attribution"] != expected["attribution"] or output["epistemic_state"] != expected["epistemic_state"]
                    or not set(expected["uncertainty"]) <= set(output["uncertainty"])
                    or not set(expected["caveats"]) <= set(output["caveats"])
                    or output.get("supersedes", []) != node["supersedes"]):
                raise ContractError("COMPACTION_CURATION: output must retain authored text, attribution, qualifications and supersession")
            require_review_authority(output["review"], proposal["review_authority"])
            if output["status"] == "active" and output["review"]["state"] != "approved":
                raise ContractError("REVIEW_AUTHORITY: active knowledge needs independent approved review")
            references += output["contradictions"]
        for reference in references:
            owner = snapshots.get(reference["garden"])
            record = owner.records.get(reference["id"]) if owner is not None else None
            if record is None or reference["revision"] != "sha256:" + owner.hashes[reference["id"]] or not context.allowed(reference["garden"], record):
                raise ContractError("COMPACTION_CURATION: referenced knowledge is unavailable to this session")
        results.append({"node": node["id"], "candidate": candidate["id"], "action": candidate["action"],
                        "review_state": output["review"]["state"] if output is not None else "not-applicable"})
    return results


def preview_compaction(context, plan, *, curation=None):
    nodes, _order = validate_plan(plan)
    context.require("context")
    if plan["garden"] not in context.bindings.gardens or not context.allows_scope(plan["scope"]):
        raise ContractError("COMPACTION_SCOPE: compaction requires an explicitly permitted garden and scope")
    citations = {canonical_json(citation): citation for node in nodes.values() for citation in node_sources(node)}
    evidence = {key: resolve_evidence(context, **citation) for key, citation in sorted(citations.items())}
    if context.output_scope([item["scope"] for item in evidence.values()]) != plan["scope"]:
        raise ContractError("COMPACTION_SCOPE: declared output must equal effective authorized input restrictions")
    report = evaluate_compaction(plan, evidence)
    report["curation"] = validate_curation_bridge(context, plan, curation)
    report["evidence"] = [{key: value for key, value in item.items() if key in {
        "source", "locator", "content_sha256", "trust", "source_identity", "source_review", "origin", "lineage"}}
        for item in evidence.values()]
    report["plan_sha256"] = digest_bytes(canonical_json({"plan": plan, "authority_sha256": context.scope_digest()}))
    maximum = min(context.session["budgets"]["max_context_bytes"], plan["retention"]["model_context"]["max_bytes"],
                  plan["retention"]["detail_budgets"][plan["budget_profile"]]["max_bytes"])
    if len(canonical_json(report)) > maximum:
        raise ContractError("COMPACTION_BUDGET: complete proof and provenance exceed the authorized byte budget")
    return context.finalize(report)


def run_compaction(arguments):
    context = QueryContext.load(arguments.local_config, arguments.scope)
    plan = read_object(arguments.input)
    curation = read_object(arguments.curation_plan) if arguments.curation_plan is not None else None
    print(canonical_json(preview_compaction(context, plan, curation=curation)).decode(), end="")
    return 0
