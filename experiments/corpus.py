"""Synthetic scoped multi-garden corpus shared by optional experiments only."""

from copy import deepcopy
import json
from pathlib import Path

from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.scope import local_scope
from tests.federation_fixture import create_fixture
from tests.support_v1 import (
    FIXTURES,
    add_knowledge,
    add_source,
    create_garden,
    reference,
    write_json,
    write_session,
)


def create_corpus(root: Path, per_garden=32):
    root.mkdir(parents=True, exist_ok=True)
    gardens = [
        create_fixture(root / identity, identity)
        for identity in ("public-alpha", "public-beta")
    ]
    for fixture in gardens:
        for n in range(per_garden):
            record = add_knowledge(
                fixture["workspace"],
                f"topic-{n:04d}",
                visibility="public",
                sources=fixture["evidence"],
                body=f"Synthetic topic {n}: reviewed source evidence for retirement planning and café long-term context.\n",
            )
            record["publication"] = "eligible"
            record["tags"] = ["long-term"]
            write_json(
                fixture["workspace"] / ".garden/knowledge" / (record["id"] + ".json"),
                record,
            )
    private = root / "private-input"
    create_garden(private, "personal-gamma")
    raw = b"denied-financial-canary remains personal.\n"
    source = add_source(private, raw)
    evidence = [
        {
            "source": reference(
                "personal-gamma", source["id"], source["artifact"]["sha256"]
            ),
            "locator": "lines:1-1",
            "content_sha256": digest_bytes(raw),
        }
    ]
    add_knowledge(private, "private-canary", body=raw.decode(), sources=evidence)
    edge = json.loads((FIXTURES / "synapse.json").read_text())
    edge.update(
        id="cross-garden-link",
        garden="public-alpha",
        visibility="public",
        type="supports",
        directed=True,
        source=reference("public-alpha", "reviewed-reference"),
        target=reference("public-beta", "reviewed-reference"),
        review=deepcopy(gardens[0]["profile"]["review"]),
        evidence=gardens[0]["evidence"],
    )
    write_json(
        gardens[0]["workspace"] / ".garden/synapses/cross-garden-link.json", edge
    )
    config = root / "bindings.json"
    write_json(
        config,
        {
            "schema": "mindgarden.local-bindings/v1",
            "gardens": [
                {
                    "id": g["profile"]["garden"],
                    "root": str(g["workspace"]),
                    "scope": local_scope("public", publication="publishable"),
                }
                for g in gardens
            ]
            + [{"id": "personal-gamma", "root": str(private), "scope": local_scope()}],
            "vaults": [],
            "revoked_sessions": [],
        },
    )
    public = root / "public-session.json"
    session = write_session(
        public, config, visibility=["public"], writable="public-alpha"
    )
    session.update(
        request_scope=local_scope("public", publication="publishable"),
        publication_authority="publishable",
    )
    session["budgets"]["max_context_bytes"] = 1000000
    write_json(public, bind_session_revisions(config, session))
    personal = root / "personal-session.json"
    session = write_session(
        personal, config, visibility=["public", "personal"], writable="public-alpha"
    )
    session.update(
        request_scope=local_scope(), publication_authority="never-exportable"
    )
    session["budgets"]["max_context_bytes"] = 1000000
    write_json(personal, bind_session_revisions(config, session))
    context = QueryContext.load(config, public)
    overlay = QueryContext.load(config, personal)
    public_index = build_index(context)
    personal_index = build_index(overlay)
    assert len(public_index["records"]) == 2 * (per_garden + 3)
    assert len(personal_index["records"]) == len(public_index["records"]) + 1
    return {
        "context": context,
        "personal_context": overlay,
        "index": public_index,
        "personal_index": personal_index,
        "configuration": config,
        "session": public,
        "private_workspace": private,
        "gardens": gardens,
    }
