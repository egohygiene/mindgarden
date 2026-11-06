"""Authored hierarchical compaction: exact evidence, qualifications and manifests."""

from collections import defaultdict
import re

from .contracts import ContractRegistry, canonical_json, digest_bytes
from .scope import POLICY_REFERENCE, inherit_scope, validate_scope
from .validation import ContractError

LAYERS = ("normalized-segment", "source-summary", "durable-knowledge", "cross-source-synthesis", "context", "publication-candidate")


def node_sources(node):
    values = {canonical_json(citation): citation for statement in node["statements"] for citation in statement["evidence"]}
    return [values[key] for key in sorted(values)]


def render_node(node):
    return "\n\n".join(statement["text"] for statement in node["statements"]) + "\n"


def qualifications(node):
    statements = node["statements"]
    attributions = {statement["attribution"] for statement in statements}
    states = {statement["epistemic_state"] for statement in statements}
    return {"attribution": next(iter(attributions)) if len(attributions) == 1 else "mixed",
            "epistemic_state": next(iter(states)) if len(states) == 1 else "proposed",
            "uncertainty": sorted({text for statement in statements for text in statement["uncertainty"]}),
            "caveats": sorted({"Contradiction: " + text for statement in statements for text in statement["contradictions"]}
                | {"Validity: " + statement["validity"]["state"] + ". " + statement["validity"]["reason"] for statement in statements})}


def validate_plan(plan):
    if len(canonical_json(plan)) > 2_000_000 or ContractRegistry().errors(plan, "compaction-plan"):
        raise ContractError("COMPACTION_INVALID: supported bounded authored compaction plan required")
    validate_scope(plan["scope"])
    if plan["retention"]["policy"] != POLICY_REFERENCE:
        raise ContractError("POLICY_UNSUPPORTED: compaction requires the supported explicit local policy")
    if plan["scope"]["persistence"] == "encrypted-vault":
        raise ContractError("COMPACTION_SCOPE: restricted runtime assurance is unavailable")
    if plan["budget_profile"] == "publishing" and (plan["scope"]["visibility"] != "public" or plan["scope"]["publication"] != "publishable"):
        raise ContractError("COMPACTION_PUBLICATION: public candidate budgets cannot declassify private inputs")
    nodes = {node["id"]: node for node in plan["nodes"]}
    if len(nodes) != len(plan["nodes"]) or not set(plan["outputs"]) <= nodes.keys():
        raise ContractError("COMPACTION_RELATIONSHIP: unique nodes and existing selected outputs required")
    order = []
    pending = set(nodes)
    statement_ids = set()
    for node in nodes.values():
        if node["action"] == "supersede" and not node["supersedes"]:
            raise ContractError("COMPACTION_RELATIONSHIP: supersession requires explicit retained knowledge references")
        if node["action"] == "merge" and len(node["inputs"]) < 2:
            raise ContractError("COMPACTION_RELATIONSHIP: merging requires two explicit hierarchy inputs")
        if not set(node["inputs"]) <= nodes.keys() or any(LAYERS.index(nodes[parent]["layer"]) > LAYERS.index(node["layer"]) for parent in node["inputs"]):
            raise ContractError("COMPACTION_RELATIONSHIP: hierarchy inputs must be existing same-or-earlier layers")
        for statement in node["statements"]:
            if statement["id"] in statement_ids:
                raise ContractError("COMPACTION_DUPLICATE: statement identities must be unique")
            statement_ids.add(statement["id"])
            validity = statement["validity"]
            first, last = validity["valid_from"], validity["valid_until"]
            if (first and last and first > last) or (last and last < plan["created_at"][:10] and validity["state"] == "current"):
                raise ContractError("COMPACTION_VALIDITY: expired or contradictory validity must remain explicit")
            if validity["state"] == "unknown" and not statement["uncertainty"]:
                raise ContractError("COMPACTION_VALIDITY: unknown facts require explicit uncertainty")
            if validity["state"] == "conflicting" and not statement["contradictions"]:
                raise ContractError("COMPACTION_VALIDITY: conflicting facts require explicit contradictions")
    while pending:
        ready = sorted(identity for identity in pending if set(nodes[identity]["inputs"]) <= set(order))
        if not ready:
            raise ContractError("COMPACTION_CYCLE: hierarchy dependencies must be acyclic")
        order.extend(ready); pending.difference_update(ready)
    return nodes, order


def evaluate_compaction(plan, evidence):
    """Evidence is supplied by the scoped application service, never acquired here."""
    nodes, order = validate_plan(plan)
    manifests = {}
    for identity in order:
        node = nodes[identity]
        parents = [nodes[parent] for parent in node["inputs"]]
        parent_attributions = {statement["attribution"] for parent in parents for statement in parent["statements"]}
        attributions = {statement["attribution"] for statement in node["statements"]}
        if not parent_attributions <= attributions and "mixed" not in attributions:
            raise ContractError("COMPACTION_ATTRIBUTION: derived layers must retain contributing attribution")
        if (any(statement["epistemic_state"] not in {"observed", "decided"} for parent in parents for statement in parent["statements"])
                and any(statement["epistemic_state"] in {"observed", "decided"} for statement in node["statements"])):
            raise ContractError("COMPACTION_EPISTEMIC: derived inference cannot silently become observed or decided")
        if not {canonical_json(citation) for parent in parents for citation in node_sources(parent)} <= {canonical_json(citation) for citation in node_sources(node)}:
            raise ContractError("COMPACTION_EVIDENCE: derived layers must retain contributing exact citations")
        inherited = {text for parent in parents for text in qualifications(parent)["uncertainty"]}
        if not inherited <= set(qualifications(node)["uncertainty"]):
            raise ContractError("COMPACTION_UNCERTAINTY: derived layers must retain contributing uncertainty")
        contradictions = {text for parent in parents for statement in parent["statements"] for text in statement["contradictions"]}
        if not contradictions <= {text for statement in node["statements"] for text in statement["contradictions"]}:
            raise ContractError("COMPACTION_CONTRADICTION: derived layers must retain contributing contradictions")
        if (any(statement["validity"]["state"] != "current" for parent in parents for statement in parent["statements"])
                and all(statement["validity"]["state"] == "current" for statement in node["statements"])):
            raise ContractError("COMPACTION_VALIDITY: derivation cannot silently make uncertain/outdated facts current")
        parent_states = {statement["validity"]["state"] for parent in parents for statement in parent["statements"]} - {"current"}
        missing_states = parent_states - {statement["validity"]["state"] for statement in node["statements"]}
        if not {"Inherited validity: " + state for state in missing_states} <= set(qualifications(node)["uncertainty"]):
            raise ContractError("COMPACTION_VALIDITY: inherited unknown, outdated and conflicting states must remain explicit")
        payloads = []
        for citation in node_sources(node):
            payload = evidence.get(canonical_json(citation))
            if payload is None or digest_bytes(payload["text"].encode()) != citation["content_sha256"]:
                raise ContractError("COMPACTION_EVIDENCE: every statement needs exact verified authorized evidence")
            payloads.append(payload)
        scope = inherit_scope([plan["scope"], *[item["scope"] for item in payloads], *[manifests[parent]["scope"] for parent in node["inputs"]]])
        if scope != plan["scope"]:
            raise ContractError("COMPACTION_SCOPE: declared output must preserve every contributing restriction")
        if node["layer"] == "normalized-segment" and (node["inputs"] or any(len(statement["evidence"]) != 1 or statement["text"] != evidence[canonical_json(statement["evidence"][0])]["text"] for statement in node["statements"])):
            raise ContractError("COMPACTION_SEGMENT: normalized segments must quote their exact evidence")
        if node["layer"] == "cross-source-synthesis" and len({citation["source"]["id"] for citation in node_sources(node)}) < 2:
            raise ContractError("COMPACTION_SYNTHESIS: cross-source synthesis requires two represented sources")
        retention_class = "archival" if node["layer"] == "normalized-segment" else (
            "model_context" if node["layer"] == "context" else "publication" if node["layer"] == "publication-candidate" else "knowledge")
        revision = "sha256:" + digest_bytes(canonical_json({"node": node, "scope": scope,
            "inputs": {parent: manifests[parent]["revision"] for parent in node["inputs"]},
            "policy": plan["retention"]["policy"], "retention": plan["retention"][retention_class]}))
        manifests[identity] = {"id": identity, "layer": node["layer"], "action": node["action"], "inputs": sorted(node["inputs"]),
                               "revision": revision, "scope": scope}
    selected = [nodes[identity] for identity in plan["outputs"]]
    if any(node["action"] in {"defer", "discard-proposed"} for node in selected):
        raise ContractError("COMPACTION_SELECTION: deferred/discard-proposed nodes cannot become selected outputs")
    budget = plan["retention"]["detail_budgets"][plan["budget_profile"]]
    statements = sum(len(node["statements"]) for node in selected)
    text_bytes = sum(len(render_node(node).encode()) for node in selected)
    if statements > budget["max_statements"] or len(canonical_json(selected)) > budget["max_bytes"]:
        raise ContractError("COMPACTION_BUDGET: selected detail exceeds the explicit profile budget")
    groups = defaultdict(list)
    for identity, node in sorted(nodes.items()):
        groups[(node["layer"], " ".join(render_node(node).casefold().split()))].append(identity)
    near = []
    for layer in LAYERS:
        candidates = sorted((identity, set(re.findall(r"\w+", render_node(node).casefold()))) for identity, node in nodes.items() if node["layer"] == layer)
        for index, (left, words) in enumerate(candidates):
            for right, others in candidates[index + 1:]:
                score = len(words & others) / max(1, len(words | others))
                if 0.8 <= score < 1: near.append({"nodes": [left, right], "token_jaccard": round(score, 3), "review": "required"})
    source_bytes = sum(len(payload["text"].encode()) for payload in evidence.values())
    return {"schema": "mindgarden.compaction-report/v1", "classification": "machine-local-control", "publication": "never-exportable",
            "scope": plan["scope"], "manifest": {"schema": "mindgarden.compaction-manifest/v1", "classification": "machine-local-control",
                "publication": "never-exportable", "scope": plan["scope"], "policy_revision": POLICY_REFERENCE["revision"],
                "nodes": [manifests[identity] for identity in sorted(manifests)]}, "selected": selected,
            "budget": {**budget, "profile": plan["budget_profile"], "statements": statements, "text_bytes": text_bytes},
            "metrics": {"statements_with_verified_evidence": len({statement["id"] for node in nodes.values() for statement in node["statements"]}),
                        "exact_citations_verified": len(evidence), "source_selection_bytes": source_bytes,
                        "selected_text_bytes": text_bytes, "selected_text_ratio": round(text_bytes / max(1, source_bytes), 3)},
            "duplicates": [identities for identities in groups.values() if len(identities) > 1], "near_duplicates": near,
            "retention": {"archival": "preserve-originals", "destructive_changes": "unavailable",
                          "enforcement": "preview-contract-only-no-retention-jobs",
                          "context_ttl_seconds": plan["retention"]["model_context"]["ttl_seconds"],
                          "publication": "separate-review"}}


def invalidated_nodes(previous, current):
    registry = ContractRegistry()
    if any(registry.errors(value, "compaction-manifest") for value in (previous, current)):
        raise ContractError("COMPACTION_MANIFEST: supported bounded private manifests required")
    if previous["scope"] != current["scope"]:
        raise ContractError("COMPACTION_SCOPE: compare only explicitly authorized matching-scope manifests")
    for manifest in (previous, current):
        validate_scope(manifest["scope"])
        if manifest["policy_revision"] != POLICY_REFERENCE["revision"]:
            raise ContractError("POLICY_UNSUPPORTED: invalidation requires the supported policy revision")
        if any(node["scope"] != manifest["scope"] for node in manifest["nodes"]):
            raise ContractError("COMPACTION_SCOPE: manifest nodes cannot hide a different scope")
        identities = {node["id"] for node in manifest["nodes"]}
        if len(identities) != len(manifest["nodes"]) or any(not set(node["inputs"]) <= identities for node in manifest["nodes"]):
            raise ContractError("COMPACTION_MANIFEST: unique nodes and complete dependency membership required")
    old = {node["id"]: node for node in previous["nodes"]}
    new = {node["id"]: node for node in current["nodes"]}
    changed = {identity for identity in old.keys() | new.keys() if old.get(identity) != new.get(identity)}
    return sorted(changed)
