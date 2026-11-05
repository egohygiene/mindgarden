"""Authorized metadata closure and revisions, before opening any content bodies."""

from collections import defaultdict, deque
from copy import deepcopy

from ..domain.contracts import canonical_json, digest_bytes
from ..domain.garden import inspect_garden
from ..domain.publication import permits_publication
from ..domain.scope import inherit_scope
from ..domain.validation import ContractError


def key(reference: dict) -> tuple[str, str]:
    return reference["garden"], reference["id"]


def dependencies(record: dict) -> set[tuple[str, str]]:
    kind = record["schema"]
    references = []
    if kind in {"mindgarden.knowledge/v1", "mindgarden.source/v1"}:
        references += record["provenance"]
    if kind == "mindgarden.knowledge/v1":
        references += [item["source"] for item in record["sources"]]
    elif kind == "mindgarden.source/v1":
        references += record["inputs"]
    elif kind == "mindgarden.claim/v1":
        references += [record["subject"]]
        references += [item["target"].get("source", item["target"]) for item in record["evidence"]]
    elif kind == "mindgarden.synapse/v1":
        references += [record["source"], record["target"]]
        references += [item["source"] for item in record["evidence"]]
    elif kind == "mindgarden.provenance/v1":
        references += [record["artifact"]]
        references += [item["artifact"] for item in record["inputs"]
                       if not (item["role"] == "configuration" and item["artifact"]["id"] == record["garden"])]
    return {key(reference) for reference in references}


def metadata_view(context):
    snapshots = {}
    recognized = {"mindgarden." + item + "/v1" for item in ("knowledge", "claim", "synapse", "source", "provenance")}
    for garden, binding in sorted(context.bindings.gardens.items()):
        def permitted(record):
            schema = record.get("schema")
            if not isinstance(schema, str) or schema not in recognized:
                return False
            reviewed = schema in {"mindgarden.knowledge/v1", "mindgarden.claim/v1", "mindgarden.synapse/v1"}
            return (context.allowed(garden, record, review=reviewed)
                    and (not reviewed or record.get("status") in {"active", "proposed"}))

        snapshot = inspect_garden(binding["root"], metadata_only=True, record_filter=permitted,
                                  allow_unavailable_references=True)
        if snapshot.diagnostics:
            raise ContractError("QUERY_INTEGRITY: an authorized record is invalid; run owner validation in its local workspace")
        snapshots[garden] = snapshot
    records = {(garden, record_id): record for garden, snapshot in snapshots.items()
               for record_id, record in snapshot.records.items()}
    public_output = (context.session.get("request_scope", {}).get("visibility") == "public"
                     and context.session["publication_authority"] == "publishable")
    if public_output:
        for identity, record in list(records.items()):
            if record["schema"] == "mindgarden.knowledge/v1" and (record["publication"] != "eligible"
                    or not permits_publication(snapshots[identity[0]].manifest["publication"], kind=record["kind"],
                                               domains=record["domains"], topics=record["topics"])):
                del records[identity]
    required = {identity: dependencies(record) for identity, record in records.items()}
    dependents = defaultdict(set)
    denied = deque()
    for identity, targets in required.items():
        if not targets <= records.keys():
            denied.append(identity)
        for target in targets:
            dependents[target].add(identity)
    while denied:
        identity = denied.popleft()
        if identity in records:
            del records[identity]
            denied.extend(dependents[identity])
    # Propagate every evidence/provenance restriction before opening bodies.
    # Self references in provenance are harmless monotone cycles, not a reason
    # to discard attribution or silently weaken a derived classification.
    effective = {identity: context.declared_scope_for(identity[0], record) for identity, record in records.items()}
    pending_scopes = deque(sorted(records))
    while pending_scopes:
        identity = pending_scopes.popleft()
        joined = inherit_scope([effective[identity], *[effective[target] for target in required[identity]]])
        if joined != effective[identity]:
            effective[identity] = joined
            pending_scopes.extend(item for item in dependents[identity] if item in records)
    denied.extend(identity for identity, scope in effective.items() if not context.allows_scope(scope))
    while denied:
        identity = denied.popleft()
        if identity in records:
            del records[identity]
            denied.extend(dependents[identity])
    # Apply budgets after both authorization and sensitivity inheritance.
    candidates = sorted(identity for identity, record in records.items()
                        if record["schema"] in {"mindgarden.knowledge/v1", "mindgarden.claim/v1"})
    permitted_candidates = set(candidates[:context.session["budgets"]["max_candidates"]])
    denied.extend(set(candidates) - permitted_candidates)
    while denied:
        identity = denied.popleft()
        if identity in records:
            del records[identity]
            denied.extend(dependents[identity])
    roots = {identity for identity in permitted_candidates if identity in records}
    edges = sorted(identity for identity, record in records.items() if record["schema"] == "mindgarden.synapse/v1"
                   and key(record["source"]) in roots and key(record["target"]) in roots)
    roots.update(edges[:context.session["budgets"]["max_candidates"]])
    selected = set()
    pending = list(roots)
    while pending:
        identity = pending.pop()
        if identity in selected:
            continue
        selected.add(identity)
        if len(selected) > 10000:
            raise ContractError("QUERY_BUDGET: authorized evidence closure exceeds 10,000 records")
        pending.extend(required[identity] - selected)
    views = {}
    for garden, snapshot in snapshots.items():
        retained = {record_id: record for record_id, record in snapshot.records.items() if (garden, record_id) in selected}
        representations = []
        for record_id, original in sorted(retained.items()):
            record = deepcopy(original)
            if record["schema"] == "mindgarden.knowledge/v1":
                for field in ("claims", "synapses", "supersedes"):
                    record[field] = [ref for ref in record[field] if key(ref) in selected]
                if "x-curation" in record:
                    record["x-curation"]["contradictions"] = [ref for ref in record["x-curation"].get("contradictions", [])
                                                             if key(ref) in selected]
            representations.append({"record": record, "effective_scope": effective[(garden, record_id)]})
        manifest = snapshot.manifest
        revision = "sha256:" + digest_bytes(canonical_json({
            "schema": "mindgarden.authorized-view/v1", "garden": garden, "version": manifest["version"],
            "contracts": manifest["contracts"], "scope": context.bindings.garden(garden)["scope"],
            "publication": manifest["publication"], "records": representations}))
        views[garden] = {"records": retained, "revision": revision,
                         "scopes": {record_id: effective[(garden, record_id)] for record_id in retained}}
    return views
