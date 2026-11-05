"""Authored synthetic public-source/claim/graph fixture, independent of host paths."""

from copy import deepcopy
import json
from pathlib import Path

from mindgarden.application.federation import build_federation
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.scope import local_scope
from tests.support_v1 import FIXTURES, add_knowledge, add_source, create_garden, reference, write_json, write_session

FEDERATION_FIXTURES = Path(__file__).parent / "fixtures/federation"


def create_fixture(root: Path, garden_id: str = "repository-garden") -> dict:
    root.mkdir(parents=True, exist_ok=True)
    workspace = root / "canonical"
    garden = create_garden(workspace, garden_id, "public")
    manifest = json.loads((garden / "garden.json").read_text())
    manifest["publication"].update(allowed_visibilities=["public"], allow={
        "kinds": ["procedure", "claim"], "domains": ["knowledge-systems"], "topics": ["prompt-bank"]})
    write_json(garden / "garden.json", manifest)
    content = (FEDERATION_FIXTURES / "source.txt").read_bytes()
    source = add_source(workspace, content, record_id="public-source")
    source.update(visibility="public")
    write_json(garden / "sources/public-source.json", source)
    evidence = [{"source": reference(garden_id, source["id"], source["artifact"]["sha256"]),
                 "locator": "lines:1-1", "content_sha256": digest_bytes(content.splitlines(keepends=True)[0])}]
    first = add_knowledge(workspace, "reviewed-prompt", visibility="public", sources=evidence)
    first["publication"] = "eligible"
    first["x-curation"] = {"epistemic_state": "proposed", "attribution": "Synthetic assistant suggestion.",
                            "caveats": ["Review does not establish factual certainty."],
                            "uncertainty": ["Synthetic fixture only."], "contradictions": []}
    write_json(garden / "knowledge/reviewed-prompt.json", first)
    second = add_knowledge(workspace, "reviewed-reference", visibility="public", body="Keep the canonical home explicit.\n", sources=evidence)
    second["publication"] = "eligible"
    write_json(garden / "knowledge/reviewed-reference.json", second)
    add_knowledge(workspace, "unreviewed", visibility="public", reviewed=False, body="unreviewed-body-canary\n")
    edge = json.loads((FIXTURES / "synapse.json").read_text())
    edge.update(id="reviewed-link", garden=garden_id, type="supports", directed=True,
                source=reference(garden_id, first["id"]), target=reference(garden_id, second["id"]),
                visibility="public", status="active", review=deepcopy(first["review"]), evidence=evidence)
    write_json(garden / "synapses/reviewed-link.json", edge)
    claim = json.loads((FIXTURES / "claim.json").read_text())
    claim.update(id="reviewed-claim", garden=garden_id, statement="Exact evidence is retained in the synthetic prompt.",
                 subject=reference(garden_id, first["id"]), visibility="public", status="active",
                 review=deepcopy(first["review"]), evidence=[{"relationship": "supports", "target": evidence[0],
                                                            "rationale": "Authored synthetic evidence."}])
    write_json(garden / "claims/reviewed-claim.json", claim)
    configuration = root / "bindings.json"
    write_json(configuration, {"schema": "mindgarden.local-bindings/v1", "gardens": [
        {"id": garden_id, "root": str(workspace), "scope": local_scope("public", publication="publishable")},
        {"id": "hidden-garden-canary", "root": str(root / "hidden-root-canary"), "scope": local_scope()}],
        "vaults": [{"id": "hidden-vault-canary", "root": str(root / "hidden-vault-canary"), "adapter": "filesystem"}],
        "revoked_sessions": []})
    session_path = root / "session.json"
    session = write_session(session_path, configuration, visibility=["public"], writable=garden_id)
    session.update(request_scope=local_scope("public", publication="publishable"), publication_authority="publishable")
    write_json(session_path, bind_session_revisions(configuration, session))
    context = QueryContext.load(configuration, session_path)
    index = build_index(context)
    profile = json.loads((FEDERATION_FIXTURES / "profile.json").read_text())
    profile.update(garden=garden_id, base_uri=f"https://{garden_id}.example.test/garden/",
                   source_revision=next(item["revision"] for item in index["inputs"] if item["garden"] == garden_id),
                   inputs=[record["reference"] for record in index["records"]])
    profile_path = root / "profile.json"
    write_json(profile_path, profile)
    export = root / "exports"
    export.mkdir()
    return {"workspace": workspace, "configuration": configuration, "session_path": session_path,
            "profile": profile, "profile_path": profile_path, "context": context, "export": export,
            "evidence": evidence, "bundle": build_federation(context, profile)}
