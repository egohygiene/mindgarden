"""Committed recipe generator for bounded, entirely synthetic projection corpora."""

import json
from pathlib import Path

from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.scope import local_scope
from tests.support_v1 import FIXTURES, add_knowledge, add_source, create_garden, reference, write_json, write_session


def create_corpus(root: Path, count: int) -> tuple[QueryContext, dict]:
    if type(count) is not int or not 2 <= count <= 4096:
        raise ValueError("Synthetic corpus count must be between 2 and 4096")
    root = root.absolute()
    garden = root / "garden"; create_garden(garden)
    source = add_source(garden, b"Synthetic corpus evidence.\n")
    evidence = [{"source":reference("synthetic-garden", source["id"], source["artifact"]["sha256"]),
                 "locator":"artifact", "content_sha256":source["artifact"]["sha256"]}]
    notes = []
    for number in range(count):
        record = add_knowledge(garden, f"corpus-{number:05d}", body=f"Synthetic modular garden procedure needle{number:05d}.\n", sources=evidence)
        record["title"] = f"Synthetic corpus note {number:05d}"
        write_json(garden / f".garden/knowledge/{record['id']}.json", record)
        notes.append(record)
    claim = json.loads((FIXTURES / "claim.json").read_text())
    claim.update(id="corpus-claim", garden="synthetic-garden", statement="Synthetic claimneedle is a proposed corpus claim.",
                 subject=reference("synthetic-garden", notes[0]["id"], notes[0]["content"]["sha256"]),
                 visibility="private", scope=local_scope(), status="active", review=notes[0]["review"],
                 evidence=[{"relationship":"supports", "target":evidence[0], "rationale":"Exact synthetic evidence."}])
    write_json(garden / ".garden/claims/corpus-claim.json", claim)
    edge = json.loads((FIXTURES / "synapse.json").read_text())
    edge.update(id="corpus-edge", garden="synthetic-garden", type="supports", directed=True,
                source=reference("synthetic-garden", notes[0]["id"], notes[0]["content"]["sha256"]),
                target=reference("synthetic-garden", notes[1]["id"], notes[1]["content"]["sha256"]),
                visibility="private", scope=local_scope(), status="active", review=notes[0]["review"], evidence=evidence)
    write_json(garden / ".garden/synapses/corpus-edge.json", edge)
    bindings = root / "bindings.json"
    write_json(bindings, {"schema":"mindgarden.local-bindings/v1", "gardens":[{"id":"synthetic-garden", "root":str(garden), "scope":local_scope()}], "vaults":[], "revoked_sessions":[]})
    session = root / "session.json"; document = write_session(session, bindings)
    document["budgets"].update(max_candidates=count + 1, max_context_bytes=8192)
    write_json(session, bind_session_revisions(bindings, document))
    profile = json.loads((garden / ".garden/context-packs/default.json").read_text())
    profile.update(max_bytes=4096, max_candidates=count + 1, max_items=8, query="synthetic")
    return QueryContext.load(bindings, session), profile
