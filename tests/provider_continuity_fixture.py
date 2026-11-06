"""Authored synthetic records for the provider-switch conformance scenario."""

from copy import deepcopy
import json
from pathlib import Path

from mindgarden.adapters.filesystem import FilesystemVault
from mindgarden.application.bindings import LocalBindings
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.storage import content_resolver
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.scope import local_scope
from tests.support_v1 import FIXTURES, TIME, add_knowledge, create_garden, reference, write_json, write_session

FIXTURE = Path(__file__).parent / "fixtures/provider-continuity"
GARDEN = "continuity-garden"
DENIED_GARDEN = "out-of-scope-garden-canary"


def create_fixture(workspace):
    garden = workspace / "canonical"; create_garden(garden, GARDEN)
    denied = workspace / "out-of-scope"; create_garden(denied, DENIED_GARDEN)
    add_knowledge(denied, "denied-record-canary", body="denied-body-canary\n")
    bindings_path = workspace / "bindings.json"
    vault = FilesystemVault(workspace / "vault", "continuity-vault")
    write_json(bindings_path, {"schema": "mindgarden.local-bindings/v1", "gardens": [
        {"id": GARDEN, "root": str(garden), "scope": local_scope()},
        {"id": DENIED_GARDEN, "root": str(denied), "scope": local_scope()}],
        "vaults": [{"id": vault.vault_id, "root": str(vault.root), "adapter": "filesystem"}], "revoked_sessions": []})
    plan = vault.plan_init(digest_bytes(bindings_path.read_bytes())); vault.initialize(plan, plan["plan_sha256"])
    bindings = LocalBindings.load(bindings_path)
    captured = workspace / "captured.txt"
    captured.write_bytes(b"\xef\xbb\xbf" + (FIXTURE / "source.txt").read_bytes().replace(b"\n", b"\r\n"))
    plan = build_ingestion_plan(bindings, GARDEN, vault.vault_id, captured, {
        "source_id": "continuity-source", "title": "Synthetic continuity source", "owner": "synthetic-owner",
        "origin": "urn:synthetic:provider-continuity", "captured_at": TIME,
        "rights": "Authored synthetic fixture only.", "media_type": "text/plain"})
    apply_ingestion(plan, plan.digest, bindings, vault.vault_id)
    evidence = plan.inputs["normalized_sources"][0]["evidence"]
    notes = [
        ("preferences", "procedure", "Preference: answer in plain language and cite exact evidence.\n"),
        ("project-goal", "project", "Project goal: prepare a weekly synthetic project review from reviewed records.\n"),
        ("portable-brief", "reference", "Portable brief: scoped context rebuilds from canonical records.\nTransformation: normalize source text, then author this reviewed summary; preserve uncertainty.\n"),
        ("ledger-decision", "decision", "Original decision: keep a local review ledger.\nRationale: the ledger works offline.\nAlternative: a hosted ledger, deferred because remote access is unnecessary.\nOriginal schedule: daily; see the reviewed correction before using it.\n"),
    ]
    records = {}
    for record_id, kind, body in notes:
        record = add_knowledge(garden, record_id, body=body, sources=evidence)
        record.update(kind=kind, title=record_id.replace("-", " ").title())
        write_json(garden / f".garden/knowledge/{record_id}.json", record)
        records[record_id] = record
    claim = json.loads((FIXTURES / "claim.json").read_text())
    claim.update(id="daily-review-claim", garden=GARDEN, subject=reference(GARDEN, "project-goal", records["project-goal"]["content"]["sha256"]),
                 statement="Review the synthetic project daily.", epistemic_state="decided", status="deprecated",
                 visibility="private", review=deepcopy(records["project-goal"]["review"]),
                 evidence=[{"relationship": "supports", "target": evidence[0], "rationale": "Earlier synthetic decision, retained as history."}])
    write_json(garden / ".garden/claims/daily-review-claim.json", claim)
    old_claim = reference(GARDEN, claim["id"], digest_bytes(canonical_json(claim)))
    current = {**deepcopy(claim), "id": "weekly-review-claim", "statement": "Review the synthetic project weekly.", "status": "active"}
    current["evidence"].append({"relationship": "supersedes", "target": old_claim, "rationale": "Reviewed weekly correction replaces the earlier daily claim."})
    write_json(garden / ".garden/claims/weekly-review-claim.json", current)
    new_claim = reference(GARDEN, current["id"], digest_bytes(canonical_json(current)))
    body = ("Correction: review weekly, rather than daily.\nRationale: a weekly review meets the project goal without daily overhead.\n"
            "The old claim remains deprecated historical evidence, excluded from current claim ranking.\n"
            "Exact supersession chain (authored reviewed history):\n```json\n" + canonical_json({"superseded": old_claim, "current": new_claim}).decode() + "```\n")
    correction = add_knowledge(garden, "review-correction", body=body, sources=evidence)
    correction.update(kind="decision", title="Weekly review correction", supersedes=[reference(GARDEN, "ledger-decision", records["ledger-decision"]["content"]["sha256"])])
    provenance_path = garden / ".garden/provenance/provenance-review-correction.json"
    provenance = json.loads(provenance_path.read_text())
    provenance["inputs"] = [{"artifact": old_claim, "sha256": old_claim["revision"].split(":", 1)[1], "role": "previous-version"}]
    provenance["transformations"] = [{"order": 1, "name": "authored-reviewed-correction", "version": "1.0.0",
        "parameters": {"rationale": "Weekly review supersedes daily review; preserve the earlier claim and decision."},
        "performed_by": {"kind": "human", "id": "synthetic-reviewer"}}]
    write_json(provenance_path, provenance)
    correction["provenance"] = [reference(GARDEN, provenance["id"], digest_bytes(canonical_json(provenance)))]
    write_json(garden / ".garden/knowledge/review-correction.json", correction)
    records["review-correction"] = correction
    add_knowledge(garden, "unreviewed-canary", body="unreviewed-body-canary\n", reviewed=False)
    edge = json.loads((FIXTURES / "synapse.json").read_text())
    edge.update(id="brief-supports-project", garden=GARDEN, type="supports", directed=True, status="active",
                source=reference(GARDEN, "portable-brief", records["portable-brief"]["content"]["sha256"]),
                target=reference(GARDEN, "project-goal", records["project-goal"]["content"]["sha256"]),
                visibility="private", review=deepcopy(correction["review"]), evidence=evidence)
    write_json(garden / ".garden/synapses/brief-supports-project.json", edge)
    profile_path = garden / ".garden/context-packs/default.json"
    profile = json.loads(profile_path.read_text())
    selected = [reference(GARDEN, key) for key in records] + [reference(GARDEN, current["id"])]
    profile.update(title="Synthetic provider continuity", query="review project evidence", include=selected, max_items=10)
    write_json(profile_path, profile)
    session = workspace / "session.json"
    write_session(session, bindings_path, readable_ids=[GARDEN], writable=GARDEN)
    snapshot = inspect_garden(garden, content_resolver=content_resolver(bindings)).require_valid()
    return {"garden": garden, "denied": denied, "bindings": bindings_path, "session": session,
            "vault": vault, "evidence": evidence[0], "old_claim": old_claim, "new_claim": new_claim,
            "selected": [item["id"] for item in selected], "snapshot": snapshot}
