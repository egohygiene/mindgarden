"""Authored, evidence-bound curation without model or silent review authority."""

from __future__ import annotations

from argparse import Namespace
from copy import deepcopy
from pathlib import Path

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object
from ..domain.garden import evidence_bytes, inspect_garden
from ..domain.scope import LEGACY_VISIBILITY, inherit_scope, record_scope
from ..domain.validation import ContractError
from .bindings import LocalBindings, garden_fingerprint
from .changes import ChangePlan
from .records import artifact_reference, provenance_record
from .storage import content_resolver


def require_review_authority(review: dict, authority: dict | None) -> None:
    if review["state"] in {"approved", "rejected"}:
        if (authority is None or authority.get("kind") != "human"
                or authority["id"] not in review["reviewers"] or not review["rationale"]):
            raise ContractError("REVIEW_AUTHORITY: explicit human reviewer evidence is required")


def build_curation_plan(bindings: LocalBindings, candidate_path: Path, *,
                        supplied_proposal: dict | None = None,
                        authorized_snapshots: dict | None = None,
                        public_review: dict | None = None,
                        canonical_routing: dict | None = None) -> ChangePlan:
    if candidate_path.is_symlink():
        raise ContractError("PLAN_PATH: proposal must be a regular private file")
    proposal = deepcopy(supplied_proposal) if supplied_proposal is not None else read_object(candidate_path)
    registry = ContractRegistry()
    if registry.errors(proposal, "curation-plan"):
        raise ContractError("CURATION_INVALID: proposal does not conform to the curation-plan contract")
    binding = bindings.garden(proposal["garden"])
    root = binding["root"]
    if binding["scope"]["visibility"] == "public" and public_review is None:
        raise ContractError("CURATION_BOUNDARY: source curation requires an explicitly private target")
    snapshot = ((authorized_snapshots or {}).get(proposal["garden"])
                or inspect_garden(root, content_resolver=content_resolver(bindings)).require_valid())
    if binding["scope"]["persistence"] == "encrypted-vault":
        raise ContractError("RUNTIME_UNVERIFIED: encrypted curation assurance is unavailable")
    input_digest = digest_bytes(candidate_path.read_bytes())
    files: dict[str, bytes] = {}
    decisions = []
    all_scopes = [binding["scope"]]
    candidate_ids: set[str] = set()
    output_ids: set[str] = set()

    def resolve(reference: dict, expected: str | None = None) -> dict:
        owner = snapshot if reference["garden"] == proposal["garden"] else (authorized_snapshots or {}).get(reference["garden"])
        if owner is None:
            raise ContractError("CURATION_SCOPE: source evidence requires an explicitly authorized garden")
        record = owner.records.get(reference["id"])
        if record is None or (expected and record["schema"] != "mindgarden." + expected + "/v1"):
            raise ContractError("CURATION_EVIDENCE: referenced artifact is unavailable")
        if reference.get("revision") != "sha256:" + owner.hashes[reference["id"]]:
            raise ContractError("PLAN_STALE: an exact represented source revision is required")
        return record

    def verify_evidence(locator: dict) -> dict:
        record = resolve(locator["source"], "source")
        owner = snapshot if record["garden"] == proposal["garden"] else authorized_snapshots[record["garden"]]
        if digest_bytes(evidence_bytes(owner.contents[record["id"]], locator["locator"])) != locator["content_sha256"]:
            raise ContractError("PLAN_STALE: selected source evidence changed")
        return record

    for candidate in proposal["candidates"]:
        if candidate["id"] in candidate_ids:
            raise ContractError("CURATION_DUPLICATE: candidate identity is duplicated")
        candidate_ids.add(candidate["id"])
        inputs = [verify_evidence(locator) for locator in candidate["sources"]]
        merged = [resolve(reference, "knowledge") for reference in candidate["merge_inputs"]]
        sources = list(candidate["sources"])
        for previous in merged:
            sources += previous["sources"]
        sources = list({canonical_json(item): item for item in sources}.values())
        for locator in sources:
            verify_evidence(locator)
        scope = inherit_scope([binding["scope"], *[record_scope(item, bindings.garden(item["garden"])["scope"])
                                                for item in inputs + merged]])
        if scope["persistence"] == "encrypted-vault":
            raise ContractError("OUTPUT_SCOPE: ordinary local storage cannot receive restricted derivations")
        all_scopes.append(scope)
        output_reference = None
        if candidate["action"] not in {"defer", "exclude"}:
            output = candidate["output"]
            if binding["scope"]["visibility"] == "public":
                require_review_authority(public_review, proposal["review_authority"])
                policy = snapshot.manifest["publication"]
                if (scope["visibility"] != "public" or scope["publication"] == "never-exportable"
                        or public_review["state"] != "approved" or output["review"]["state"] != "approved"
                        or "public" not in policy["allowed_visibilities"]):
                    raise ContractError("ROUTE_PUBLIC: public destination lacks explicit publication authority")
                for field, values in (("kinds", [output["kind"]]), ("domains", output["domains"]), ("topics", output["topics"])):
                    if policy["allow"][field] and not set(values) <= set(policy["allow"][field]):
                        raise ContractError("ROUTE_PUBLIC: proposed output is outside the target publication allowlist")
                if any(item["schema"] == "mindgarden.source/v1" and item["kind"] == "captured" for item in inputs):
                    raise ContractError("ROUTE_PUBLIC: raw captures never authorize a public route")
            if output["id"] in output_ids:
                raise ContractError("CURATION_DUPLICATE: output identity is duplicated")
            output_ids.add(output["id"])
            require_review_authority(output["review"], proposal["review_authority"])
            if output["status"] == "active" and output["review"]["state"] != "approved":
                raise ContractError("REVIEW_AUTHORITY: active knowledge needs explicit approved review")
            if candidate["action"] == "reference" and output["kind"] != "reference":
                raise ContractError("CURATION_KIND: reference decisions produce reference knowledge")
            body = output["body"].encode("utf8")
            body_digest = digest_bytes(body)
            provenance = provenance_record(
                proposal["garden"], "provenance-" + output["id"], output["id"], body_digest,
                inputs=[{"artifact": artifact_reference(item["garden"], item["id"],
                            (snapshot if item["garden"] == proposal["garden"] else authorized_snapshots[item["garden"]]).hashes[item["id"]]),
                         "sha256": (snapshot if item["garden"] == proposal["garden"] else authorized_snapshots[item["garden"]]).hashes[item["id"]],
                         "role": "evidence"} for item in inputs + merged],
                transformations=({"name": candidate["action"], "version": "1.0.0",
                                  "parameters": {"candidate_plan_sha256": input_digest,
                                                 "candidate": candidate["id"], "rationale": candidate["rationale"]}},),
                created_at=proposal["created_at"], rights="Derived private knowledge; source rights remain authoritative.",
                origin=None, scope=scope)
            claims = []
            for item in output["claims"]:
                if item["id"] in output_ids:
                    raise ContractError("CURATION_DUPLICATE: claim identity is duplicated")
                output_ids.add(item["id"])
                require_review_authority(item["review"], proposal["review_authority"])
                for evidence in item["evidence"]:
                    if "source" in evidence["target"]:
                        verify_evidence(evidence["target"])
                claim = {"schema": "mindgarden.claim/v1", "garden": proposal["garden"], **deepcopy(item),
                         "subject": artifact_reference(proposal["garden"], output["id"], body_digest),
                         "status": "active" if item["review"]["state"] == "approved" else "proposed",
                         "visibility": LEGACY_VISIBILITY[scope["visibility"]], "scope": scope,
                         "owners": snapshot.manifest["owners"], "authors": output["authors"],
                         "x-curation": {"attribution": output["attribution"],
                                        "caveats": output["caveats"], "uncertainty": output["uncertainty"]}}
                claims.append(artifact_reference(proposal["garden"], claim["id"], digest_bytes(canonical_json(claim))))
                files[f"claims/{claim['id']}.json"] = canonical_json(claim)
            synapses = []
            for item in output["synapses"]:
                if item["id"] in output_ids:
                    raise ContractError("CURATION_DUPLICATE: relationship identity is duplicated")
                output_ids.add(item["id"])
                require_review_authority(item["review"], proposal["review_authority"])
                relationship = {"schema": "mindgarden.synapse/v1", "id": item["id"],
                                "garden": proposal["garden"], "type": item["type"],
                                "source": artifact_reference(proposal["garden"], output["id"], body_digest),
                                "target": item["target"], "directed": item["directed"],
                                "status": "active" if item["review"]["state"] == "approved" else "proposed",
                                "confidence": output["confidence"], "visibility": LEGACY_VISIBILITY[scope["visibility"]],
                                "owners": snapshot.manifest["owners"], "authors": output["authors"],
                                "review": item["review"], "evidence": sources, "scope": scope,
                                "x-rationale": item["rationale"]}
                synapses.append(artifact_reference(proposal["garden"], item["id"], digest_bytes(canonical_json(relationship))))
                files[f"synapses/{item['id']}.json"] = canonical_json(relationship)
            knowledge = {"schema": "mindgarden.knowledge/v1", "id": output["id"], "garden": proposal["garden"],
                         "title": output["title"], "kind": output["kind"], "status": output["status"],
                         "confidence": output["confidence"], "visibility": LEGACY_VISIBILITY[scope["visibility"]],
                         "owners": snapshot.manifest["owners"], "authors": output["authors"],
                         "review": output["review"], "created": proposal["created_at"][:10],
                         "updated": proposal["created_at"][:10], "domains": output["domains"],
                         "topics": output["topics"], "aliases": [], "tags": [],
                         "content": {"path": f"knowledge/{output['id']}.md", "sha256": body_digest},
                         "sources": sources, "claims": claims, "synapses": synapses,
                         "provenance": [artifact_reference(proposal["garden"], provenance["id"],
                                                          digest_bytes(canonical_json(provenance)))],
                         "supersedes": output.get("supersedes", []),
                         "publication": "eligible" if binding["scope"]["visibility"] == "public" else "excluded", "scope": scope,
                         "x-curation": {"candidate": candidate["id"], "action": candidate["action"],
                                        "rationale": candidate["rationale"], "attribution": output["attribution"],
                                        "epistemic_state": output["epistemic_state"], "caveats": output["caveats"],
                                        "uncertainty": output["uncertainty"], "contradictions": output["contradictions"]}}
            files[knowledge["content"]["path"]] = body
            if canonical_routing is not None:
                knowledge["x-routing"] = deepcopy(canonical_routing)
            files[f"knowledge/{output['id']}.json"] = canonical_json(knowledge)
            files[f"provenance/{provenance['id']}.json"] = canonical_json(provenance)
            output_reference = artifact_reference(proposal["garden"], output["id"], body_digest)
        decisions.append({"candidate": candidate["id"], "action": candidate["action"],
                          "rationale": candidate["rationale"], "sources": candidate["sources"],
                          "output": output_reference})
    receipt = {"schema": "mindgarden.curation-receipt/v1", "id": "curation-" + proposal["id"],
               "garden": proposal["garden"], "plan_sha256": input_digest,
               "scope": inherit_scope(all_scopes), "decisions": decisions}
    files[f"provenance/{receipt['id']}.json"] = canonical_json(receipt)
    prospective = dict(snapshot.records)
    from ..domain.contracts import strict_json

    for path, content in files.items():
        if not path.endswith(".json"):
            continue
        record = strict_json(content)
        if registry.errors(record, record["schema"]):
            raise ContractError("CURATION_OUTPUT: generated record does not conform")
        if record["id"] in prospective and canonical_json(prospective[record["id"]]) != content:
            raise ContractError("CURATION_CONFLICT: output identity already has different canonical content")
        prospective[record["id"]] = record
    for candidate in proposal["candidates"]:
        if "output" not in candidate:
            continue
        output = candidate["output"]
        references = list(output["contradictions"]) + list(output.get("supersedes", []))
        references += [item["target"] for item in output["synapses"]]
        references += [evidence["target"] for claim in output["claims"] for evidence in claim["evidence"]
                       if "source" not in evidence["target"]]
        for reference in references:
            if reference["garden"] != proposal["garden"] or reference["id"] not in prospective:
                raise ContractError("CURATION_RELATIONSHIP: proposed relationship has no authorized target")
    plan = ChangePlan("gardenize", proposal["garden"], root,
                      {"garden_revision": garden_fingerprint(root), "proposal_sha256": input_digest,
                       "bindings_sha256": digest_bytes(bindings.path.read_bytes()),
                       "scope": receipt["scope"], "proposal": proposal}, files,
                      source_checks=[(candidate_path.absolute(), input_digest),
                                     (bindings.path, digest_bytes(bindings.path.read_bytes()))])
    plan.verify(plan.digest)
    return plan


def apply_curation(plan: ChangePlan, reviewed_digest: str, bindings: LocalBindings) -> bool:
    def refuse_blob(_content: bytes) -> str:
        raise ContractError("CURATION_STORAGE: unexpected blob write")

    return plan.apply(reviewed_digest, validate=lambda stage: inspect_garden(
        plan.root, garden_root=stage, content_resolver=content_resolver(bindings)).require_valid(),
        put_blob=refuse_blob)


def run_gardenize(arguments: Namespace) -> int:
    bindings = LocalBindings.load(arguments.local_config)
    source = arguments.plan or arguments.apply
    plan = build_curation_plan(bindings, source)
    result = plan.document()
    if arguments.apply:
        if not arguments.plan_digest:
            raise ContractError("PLAN_DIGEST: --plan-digest is required with --apply")
        result["applied"] = apply_curation(plan, arguments.plan_digest, bindings)
    print(canonical_json(result).decode(), end="")
    return 0
