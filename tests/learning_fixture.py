"""Authored synthetic study material over actual normalized source provenance."""

from copy import deepcopy
from datetime import datetime, timezone
import json

from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.learning import empty_history
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index, record_key
from tests import test_source_adapters as source_tests
from tests.support_v1 import (
    FIXTURES,
    add_knowledge,
    reference,
    write_json,
    write_session,
)

CLOCK = lambda: datetime(2026, 11, 7, tzinfo=timezone.utc)


def setup(test):
    source_tests.SourceAdapterTests.setUp(test)
    test.input.write_text(
        "Original sources stay immutable.\nReviewed knowledge remains portable.\nMark uncertainty explicitly.\n"
    )
    source = source_tests.SourceAdapterTests.plan(test)
    apply_ingestion(source, source.digest, test.bindings, "synthetic-vault")
    evidence = source.inputs["normalized_sources"][0]["evidence"]
    record = add_knowledge(
        test.workspace,
        "learning-facts",
        body="Original sources stay immutable.\nReviewed knowledge remains portable.\n",
        sources=evidence,
    )
    record["x-curation"] = {
        "epistemic_state": "observed",
        "attribution": "authored-synthetic-fixture",
        "caveats": [],
        "uncertainty": [],
        "contradictions": [],
    }
    write_json(test.workspace / ".garden/knowledge/learning-facts.json", record)
    claim = json.loads((FIXTURES / "claim.json").read_text())
    claim.update(
        id="learning-claim",
        garden="synthetic-garden",
        subject=reference("synthetic-garden", record["id"]),
        statement="Original sources stay immutable.",
        epistemic_state="observed",
        status="active",
        visibility="private",
        review=record["review"],
        evidence=[
            {
                "relationship": "supports",
                "target": evidence[0],
                "rationale": "Explicit synthetic study evidence.",
            }
        ],
    )
    write_json(test.workspace / ".garden/claims/learning-claim.json", claim)
    test.session_path = test.root / "session.json"
    session = write_session(test.session_path, test.configuration)
    session["budgets"]["max_context_bytes"] = 131072
    write_json(test.session_path, session)
    test.context = QueryContext.load(test.configuration, test.session_path, clock=CLOCK)
    index = build_index(test.context)
    by = {record_key(r["reference"]): r for r in index["records"]}
    test.knowledge = by["synthetic-garden/learning-facts"]
    test.claim = by["synthetic-garden/learning-claim"]
    scope = test.context.output_scope([test.knowledge["scope"]])
    base = {
        "title": "Keep the source",
        "objective": "Recall the exact source/knowledge boundary.",
        "difficulty": "introductory",
        "representation": "quoted",
        "uncertainty": [],
        "review": deepcopy(record["review"]),
        "lifecycle": "approved",
        "supersedes": [],
    }
    card = {
        "schema": "mindgarden.learning-card/v1",
        **deepcopy(base),
        "id": "source-card",
        "type": "factual",
        "prompt": "What happens to the original sources?",
        "answer": {
            "schema": "mindgarden.learning-answer/v1",
            "text": "Original sources stay immutable.",
            "rubric": "Recall the exact immutable-source boundary; do not infer deletion authority.",
            "certainty": "supported",
        },
    }
    cloze = {
        **deepcopy(card),
        "id": "portable-card",
        "title": "Portable reviewed knowledge",
        "type": "cloze",
        "prompt": "Reviewed knowledge remains {{c1::portable}}.",
    }
    cloze["answer"]["text"] = "portable"
    summary = {
        "schema": "mindgarden.learning-summary/v1",
        **deepcopy(base),
        "id": "boundary-summary",
        "representation": "paraphrase",
        "text": "Keep originals separate from reviewed portable knowledge.",
    }
    test.request = {
        "schema": "mindgarden.learning-plan/v1",
        "deck": {
            "schema": "mindgarden.learning-deck/v1",
            "id": "source-boundaries",
            "title": "Synthetic source boundaries",
            "objective": "Review exact source and knowledge ownership.",
        },
        "scope": scope,
        "generator": "authored",
        "review": deepcopy(record["review"]),
        "review_authority": {"kind": "human", "id": "synthetic-reviewer"},
        "scheduler": {
            "id": "fixed-intervals",
            "version": "1.0.0",
            "anchor": "2026-11-04T00:00:00Z",
        },
        "as_of": "2026-11-07T00:00:00Z",
        "max_bytes": 131072,
        "candidates": [
            {
                "schema": "mindgarden.learning-candidate/v1",
                "references": [test.claim["reference"]]
                if o["id"] == "source-card"
                else [test.knowledge["reference"]],
                "rationale": "Authored, bounded synthetic study item.",
                "output": o,
            }
            for o in [card, cloze, summary]
        ],
    }
    test.history = empty_history(test.request)
