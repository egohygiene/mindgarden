"""Explainable placement of authored candidates with one home and private fallback."""

from __future__ import annotations

from argparse import Namespace
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object, strict_json
from ..domain.garden import inspect_garden
from ..domain.publication import permits_publication
from ..domain.scope import LEGACY_VISIBILITY, PERSISTENCE_ORDER, inherit_scope, record_scope
from ..domain.validation import ContractError
from .bindings import LocalBindings, garden_fingerprint
from .changes import ChangePlan
from .curation import build_curation_plan, require_review_authority
from .records import AUTHOR, artifact_reference, provenance_record
from .storage import content_resolver
from .transactions import apply_group, recover_routing


def snapshots_for(bindings: LocalBindings, staged: dict | None = None, *, allow_locked: bool = False) -> dict:
    if not allow_locked and any((item["root"] / ".mindgarden-write.lock").exists() for item in bindings.gardens.values()):
        raise ContractError("WRITE_LOCKED: recover the interrupted operation before reading a combined garden state")
    resolver = content_resolver(bindings)
    first = {key: inspect_garden(value["root"], garden_root=(staged or {}).get(key), content_resolver=resolver,
                                allow_unavailable_references=True)
             for key, value in sorted(bindings.gardens.items())}
    result = {key: inspect_garden(bindings.garden(key)["root"], garden_root=(staged or {}).get(key),
                                content_resolver=resolver, authorized_gardens=first).require_valid()
            for key in first}
    from ..domain.routing_transitions import retired_references

    retired_references(record for snapshot in result.values() for record in snapshot.records.values())
    return result


@dataclass
class RoutingPlan:
    bindings: LocalBindings
    inputs: dict
    decisions: list[dict]
    changes: dict[str, ChangePlan]

    def payload(self) -> dict:
        return {"schema": "mindgarden.routing-preview/v1", "inputs": self.inputs,
                "decisions": self.decisions,
                "changes": [plan.document() for _key, plan in sorted(self.changes.items())]}

    @property
    def digest(self) -> str:
        return digest_bytes(canonical_json(self.payload()))

    def document(self) -> dict:
        return {**self.payload(), "plan_sha256": self.digest}

    def apply(self, digest: str) -> bool:
        def validate(staged):
            for garden, revision in self.inputs["garden_revisions"].items():
                if garden not in self.changes and garden_fingerprint(self.bindings.garden(garden)["root"]) != revision:
                    raise ContractError("PLAN_STALE: an authorized source garden changed")
            snapshots_for(self.bindings, staged, allow_locked=True)

        return apply_group(self.changes, digest, expected_digest=self.digest,
                           bindings=self.bindings, validate=validate)


def build_routing_plan(bindings: LocalBindings, catalog_path: Path, request_path: Path) -> RoutingPlan:
    if catalog_path.is_symlink() or request_path.is_symlink():
        raise ContractError("ROUTE_PATH: routing inputs must be regular explicit files")
    catalog, request = read_object(catalog_path), read_object(request_path)
    registry = ContractRegistry()
    if registry.errors(catalog, "garden-catalog") or registry.errors(request, "routing-plan"):
        raise ContractError("ROUTE_INVALID: catalog or authored routing request does not conform")
    snapshots = snapshots_for(bindings)
    entries = {}
    for entry in catalog["gardens"]:
        if entry["id"] in entries:
            raise ContractError("ROUTE_CATALOG: duplicate garden identity")
        entries[entry["id"]] = entry
        manifest = snapshots[entry["id"]].manifest if entry["id"] in snapshots else None
        if manifest is None or any(entry[field] != manifest[field] for field in ("id", "kind", "owners", "canonical_uri", "contracts")):
            raise ContractError("ROUTE_CATALOG: explicit catalog differs from an available target contract")
        if entry["scope"] != bindings.garden(entry["id"])["scope"] or entry["domains"] != manifest["routing"]["domains"]:
            raise ContractError("ROUTE_CATALOG: target scope or routing domains changed")
    fallback = catalog["private_fallback"]
    if fallback is not None and (fallback not in entries or entries[fallback]["scope"]["visibility"] != "personal"):
        raise ContractError("ROUTE_FALLBACK: fallback must name an explicitly bound personal garden")
    curation = request["curation"]
    authority = curation["review_authority"]
    candidates = {item["id"]: item for item in curation["candidates"]}
    routes = {item["candidate"]: item for item in request["routes"]}
    if (len(candidates) != len(curation["candidates"]) or len(routes) != len(request["routes"])
            or set(candidates) != set(routes)):
        raise ContractError("ROUTE_IDENTITY: every candidate needs exactly one routing decision")
    request_digest, catalog_digest = digest_bytes(request_path.read_bytes()), digest_bytes(catalog_path.read_bytes())
    for owner in snapshots.values():
        receipt = owner.records.get("routing-" + request["id"])
        if receipt is not None and receipt.get("request_sha256") != request_digest:
            raise ContractError("ROUTE_REVISION_REQUIRED: this request was placed; use an explicit new unit or a separately reviewed transfer")
    checks = [(request_path.absolute(), request_digest), (catalog_path.absolute(), catalog_digest),
              (bindings.path, digest_bytes(bindings.path.read_bytes()))]
    changes: dict[str, ChangePlan] = {}
    decisions = []
    receipts: dict[str, list] = {}

    def add_files(garden: str, files: dict[str, bytes]) -> None:
        if garden not in changes:
            changes[garden] = ChangePlan("route", garden, bindings.garden(garden)["root"], {
                "garden_revision": garden_fingerprint(bindings.garden(garden)["root"]),
                "request_sha256": request_digest, "catalog_sha256": catalog_digest}, {}, source_checks=checks)
        for path, content in files.items():
            if path in changes[garden].files and changes[garden].files[path] != content:
                raise ContractError("ROUTE_DUPLICATE: two candidates attempt to create different content at one identity")
            changes[garden].files[path] = content

    for candidate_id, candidate in sorted(candidates.items()):
        route = routes[candidate_id]
        decision = {"candidate": candidate_id, "canonical_home": None, "state": "unresolved",
                    "confidence": route["confidence"], "rationale": route["rationale"],
                    "policy_decisions": [], "rejected_alternatives": [], "references": []}
        decisions.append(decision)
        if "output" not in candidate:
            decision.update(state="history-only", policy_decisions=["Authored defer/exclude creates no placed knowledge."])
            continue
        output = candidate["output"]
        if output["review"]["state"] != "approved" or output["status"] != "active":
            decision["policy_decisions"].append("Only explicitly reviewed active candidates may be routed.")
            continue
        require_review_authority(output["review"], authority)
        scopes = []
        for reference in [item["source"] for item in candidate["sources"]] + candidate["merge_inputs"]:
            owner = snapshots.get(reference["garden"])
            record = owner.records.get(reference["id"]) if owner else None
            if record is None or reference["revision"] != "sha256:" + owner.hashes[reference["id"]]:
                raise ContractError("PLAN_STALE: routing evidence requires an exact authorized revision")
            scopes.append(record_scope(record, bindings.garden(reference["garden"])["scope"]))

        def rejection(garden: str, *, relevant=False) -> str | None:
            if garden not in entries:
                return "Target is not available in the explicit catalog."
            target = entries[garden]
            inherited = inherit_scope([target["scope"], *scopes])
            if (inherited["visibility"] != target["scope"]["visibility"]
                    or inherited["persistence"] == "encrypted-vault"
                    or PERSISTENCE_ORDER[inherited["persistence"]] > PERSISTENCE_ORDER[target["scope"]["persistence"]]):
                return "Contributing restrictions do not permit this storage boundary."
            if not relevant and not set(output["domains"]) <= set(target["domains"]):
                return "Candidate domains are outside the target routing scope."
            required_contracts = {"mindgarden.knowledge/v1", "mindgarden.provenance/v1"}
            required_contracts |= ({"mindgarden.synapse/v1"} if relevant else
                                   {"mindgarden.curation-receipt/v1", "mindgarden.routing-receipt/v1"})
            if any(not required_contracts <= set(target["contracts"][field]) for field in ("reads", "writes")):
                return "Target does not declare every required read/write contract."
            if target["scope"]["visibility"] == "public":
                controller = entries.get(curation["garden"])
                if controller is None or controller["scope"]["visibility"] != "personal":
                    return "Public placement requires an explicit personal controller for private routing audit metadata."
                review = route["public_review"]
                if review is None or review["state"] != "approved" or inherited["publication"] == "never-exportable":
                    return "Public placement requires explicit human publication review."
                require_review_authority(review, authority)
                if not permits_publication(snapshots[garden].manifest["publication"], kind=output["kind"],
                                           domains=output["domains"], topics=output["topics"]):
                    return "The target publication allowlist denies this candidate; empty lists grant no publication."
                for evidence in candidate["sources"]:
                    source = snapshots[evidence["source"]["garden"]].records[evidence["source"]["id"]]
                    if source.get("kind") == "captured" or source.get("publication") != "eligible":
                        return "Public placement requires separately reviewed normalized public evidence; raw captures remain excluded."
            return None

        preferred = route["preferred_gardens"]
        accepted = []
        for garden in preferred:
            reason = rejection(garden)
            if reason:
                decision["rejected_alternatives"].append({"garden": garden, "reason": reason})
            else:
                accepted.append(garden)
        if len(accepted) == 1:
            home = accepted[0]; decision["state"] = "routed"
        elif fallback is not None and rejection(fallback) is None:
            home = fallback; decision["state"] = "private-fallback"
            decision["policy_decisions"].append("Ambiguous, absent or prohibited preferred homes use the explicit private fallback.")
            for garden in accepted:
                decision["rejected_alternatives"].append({"garden": garden, "reason": "Ambiguous preferred homes; private fallback selected."})
        else:
            decision["policy_decisions"].append("No permitted explicit private fallback; candidate remains unresolved.")
            continue
        decision["policy_decisions"].append("One canonical home; originals remain immutable and private sources are never copied.")
        home_reference = artifact_reference(home, output["id"], digest_bytes(output["body"].encode()))
        unit = request["id"] + ":" + candidate_id
        for owner in snapshots.values():
            prior_receipt = owner.records.get("routing-" + request["id"], {})
            for previous in prior_receipt.get("decisions", []):
                if previous["candidate"] == candidate_id and previous["canonical_home"] != home_reference:
                    raise ContractError("ROUTE_TRANSFER_REQUIRED: the existing reviewed placement has another canonical home")
            for record in owner.records.values():
                prior = record.get("x-routing", {})
                if prior.get("unit") == unit and prior.get("role") == "canonical" and prior["canonical_home"] != home_reference:
                    raise ContractError("ROUTE_TRANSFER_REQUIRED: this unit already has another canonical home; explicit transfer is deferred")
        proposal = {**deepcopy(curation), "id": curation["id"] + "-" + candidate_id,
                    "garden": home, "candidates": [deepcopy(candidate)]}
        public_digest = None
        portable_unit = unit
        if entries[home]["scope"]["visibility"] == "public":
            # Public lineage represents the reviewed public selection. Private
            # request/catalog hashes, labels and rejected routes stay private.
            public_candidate = proposal["candidates"][0]
            public_candidate.update(id="public-candidate", rationale="Explicitly reviewed public derivative.")
            proposal.update(id="public-placement", producer=dict(AUTHOR), created_at=route["public_review"]["reviewed_at"])
            selection = digest_bytes(canonical_json(proposal))
            proposal["id"] += "-" + selection[:24]
            public_candidate["id"] += "-" + selection[:24]
            public_digest = digest_bytes(canonical_json(proposal))
            portable_unit = "public-selection:" + public_digest
        curated = build_curation_plan(bindings, request_path, supplied_proposal=proposal,
                                      authorized_snapshots=snapshots, public_review=route["public_review"],
                                      canonical_routing={"unit": portable_unit, "role": "canonical", "canonical_home": home_reference},
                                      portable_proposal_digest=public_digest)
        knowledge_path = f"knowledge/{output['id']}.json"
        knowledge = strict_json(curated.files[knowledge_path])
        add_files(home, curated.files)
        decision["canonical_home"] = home_reference
        scopes.append(knowledge["scope"])
        for garden in sorted(set(route["relevant_gardens"]) - {home}):
            reason = rejection(garden, relevant=True)
            if reason:
                decision["rejected_alternatives"].append({"garden": garden, "reason": reason})
                continue
            reference_id = "reference-" + digest_bytes(canonical_json(home_reference))[:24]
            body = ("Canonical knowledge: " + home + "/" + output["id"] + " at " + home_reference["revision"] + ".\n").encode()
            scope = inherit_scope([entries[garden]["scope"], knowledge["scope"]])
            provenance = provenance_record(garden, "provenance-" + reference_id, reference_id, digest_bytes(body),
                inputs=[{"artifact": home_reference, "sha256": home_reference["revision"][7:], "role": "source"}],
                transformations=({"name": "reference-canonical-home", "version": "1.0.0", "parameters": {}},),
                created_at=proposal["created_at"], rights="Reference only; canonical rights remain authoritative.", origin=None, scope=scope)
            edge_id = "synapse-" + reference_id
            edge = {"schema": "mindgarden.synapse/v1", "id": edge_id, "garden": garden, "type": "references",
                    "source": artifact_reference(garden, reference_id, digest_bytes(body)), "target": home_reference,
                    "directed": True, "status": "active", "confidence": route["confidence"],
                    "visibility": LEGACY_VISIBILITY[scope["visibility"]], "owners": entries[garden]["owners"],
                    "authors": output["authors"], "review": output["review"], "evidence": [], "scope": scope}
            reference = {**deepcopy(knowledge), "id": reference_id, "garden": garden, "kind": "reference",
                         "title": "Reference to " + output["title"], "scope": scope,
                         "visibility": LEGACY_VISIBILITY[scope["visibility"]], "owners": entries[garden]["owners"],
                         "content": {"path": "knowledge/" + reference_id + ".md", "sha256": digest_bytes(body)},
                         "claims": [], "synapses": [artifact_reference(garden, edge_id, digest_bytes(canonical_json(edge)))],
                         "sources": [], "supersedes": [], "publication": "excluded",
                         "provenance": [artifact_reference(garden, provenance["id"], digest_bytes(canonical_json(provenance)))],
                         "x-routing": {"unit": portable_unit, "role": "reference", "canonical_home": home_reference}}
            add_files(garden, {reference["content"]["path"]: body, "knowledge/" + reference_id + ".json": canonical_json(reference),
                               "synapses/" + edge_id + ".json": canonical_json(edge),
                               "provenance/" + provenance["id"] + ".json": canonical_json(provenance)})
            decision["references"].append(artifact_reference(garden, reference_id, digest_bytes(body)))
        audit_home = curation["garden"] if entries[home]["scope"]["visibility"] == "public" else home
        receipts.setdefault(audit_home, []).append(decision)
    for home, placed in receipts.items():
        receipt = {"schema": "mindgarden.routing-receipt/v1", "id": "routing-" + request["id"], "garden": home,
                   "request_sha256": request_digest, "catalog_sha256": catalog_digest,
                   "scope": inherit_scope([entries[home]["scope"], *[
                       strict_json(content)["scope"] for path, content in (changes[home].files if home in changes else {}).items()
                       if path.startswith("knowledge/") and path.endswith(".json")]]), "decisions": placed}
        # Rejected private alternatives belong to the private reviewed preview,
        # never to portable public metadata.
        receipt = deepcopy(receipt)
        for item in receipt["decisions"]:
            item["rejected_alternatives"] = []
            item["references"] = [ref for ref in item["references"]
                                  if entries[ref["garden"]]["scope"]["visibility"] in {"public", entries[home]["scope"]["visibility"]}]
        add_files(home, {"provenance/" + receipt["id"] + ".json": canonical_json(receipt)})
    for plan in changes.values():
        written_contracts = set()
        for path, content in plan.files.items():
            if path.endswith(".json"):
                record = strict_json(content)
                if registry.errors(record, record["schema"]):
                    raise ContractError("ROUTE_OUTPUT: generated routing record does not conform")
                written_contracts.add(record["schema"])
        if any(not written_contracts <= set(snapshots[plan.garden_id].manifest["contracts"][field]) for field in ("reads", "writes")):
            raise ContractError("CAPABILITY_UNDECLARED: every routing target must declare all generated record contracts")
        plan.verify(plan.digest)
    return RoutingPlan(bindings, {"request_sha256": request_digest, "catalog_sha256": catalog_digest,
                                  "bindings_sha256": digest_bytes(bindings.path.read_bytes()),
                                  "garden_revisions": {key: garden_fingerprint(value["root"]) for key, value in sorted(bindings.gardens.items())}},
                       decisions, changes)


def run_route(arguments: Namespace) -> int:
    bindings = LocalBindings.load(arguments.local_config, allow_interrupted=arguments.recover)
    if arguments.recover:
        if not arguments.plan_digest:
            raise ContractError("RECOVERY_DIGEST: --plan-digest identifies the interrupted operation")
        result = recover_routing(bindings, arguments.plan_digest)
    else:
        if arguments.transition:
            from .routing_lifecycle import build_transition_plan

            plan = build_transition_plan(bindings, arguments.transition)
            result = plan.document()
            if arguments.apply:
                if not arguments.plan_digest:
                    raise ContractError("PLAN_DIGEST: --plan-digest is required with --apply")
                result["applied"] = plan.apply(arguments.plan_digest)
            print(canonical_json(result).decode(), end="")
            return 0
        if not arguments.catalog or not arguments.input:
            raise ContractError("ROUTE_INPUT: --catalog and --input are required")
        plan = build_routing_plan(bindings, arguments.catalog, arguments.input)
        result = plan.document()
        if arguments.apply:
            if not arguments.plan_digest:
                raise ContractError("PLAN_DIGEST: --plan-digest is required with --apply")
            result["applied"] = plan.apply(arguments.plan_digest)
        if arguments.check:
            result["check"] = "resolved" if all(item["state"] != "unresolved" for item in plan.decisions) else "unresolved"
    print(canonical_json(result).decode(), end="")
    return 3 if arguments.check and result.get("check") == "unresolved" else 0
