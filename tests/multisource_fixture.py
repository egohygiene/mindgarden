"""Reuse the committed fictional garden's correction, dialogue and career sources."""

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.query import QueryContext
from mindgarden.domain.contracts import digest_bytes, read_object
from mindgarden.domain.garden import evidence_bytes
from mindgarden.domain.scope import local_scope
from tests import test_source_adapters as source_fixture
from tests.support_v1 import TIME, add_knowledge, write_json, write_session

FIXTURE_ROOT = Path(__file__).parent / "fixtures/compaction"
SEED = Path(__file__).parents[1] / "examples/mock-garden/seed"


def capture(test, name, revised=False):
    settings = test.quality["correction"] if revised else test.quality["sources"][name]
    content = (SEED / settings["file"]).read_bytes()
    path = test.root / (name + ".md")
    path.write_bytes(content)
    metadata = {**test.metadata, "source_id": name, "origin": "urn:fictional:" + name}
    imported = build_ingestion_plan(
        test.bindings, "synthetic-garden", "synthetic-vault", path, metadata
    )
    apply_ingestion(imported, imported.digest, test.bindings, "synthetic-vault")
    citation = deepcopy(imported.inputs["normalized_sources"][0]["evidence"][0])
    first, last = settings["lines"]
    citation["locator"] = f"lines:{first}-{last}"
    selected = evidence_bytes(content, citation["locator"])
    citation["content_sha256"] = digest_bytes(selected)
    add_knowledge(
        test.workspace,
        "anchor-" + name + ("-corrected" if revised else ""),
        body="Authored fictional evidence anchor; no factual adjudication.\n",
        sources=[citation],
    )
    test.citations[name] = citation
    test.text[name] = selected.decode()


def bind(test):
    session = write_session(test.session_path, test.configuration)
    session["budgets"]["max_context_bytes"] = 65536
    write_json(test.session_path, session)
    test.context = QueryContext.load(test.configuration, test.session_path)
    test.context.clock = lambda: datetime(2026, 11, 13, tzinfo=timezone.utc)


def setup(test):
    source_fixture.SourceAdapterTests.setUp(test)
    test.quality = read_object(FIXTURE_ROOT / "multisource-quality.json")
    test.citations, test.text = {}, {}
    for name in test.quality["sources"]:
        capture(test, name)
    test.session_path = test.root / "summary-session.json"
    test.revised = False
    bind(test)


def statement(test, name, text, identity):
    return {
        "id": identity,
        "text": text,
        "evidence": [deepcopy(test.citations[name])],
        "attribution": "quoted" if name == "conversation" else "user-report",
        "epistemic_state": "proposed",
        "uncertainty": [
            "Authored fictional material; interpretation remains unverified."
        ],
        "contradictions": []
        if name == "career"
        else ["Dates remain disputed; the underlying agreement is unavailable."],
        "validity": {
            "state": "unknown" if name == "career" else "conflicting",
            "valid_from": None,
            "valid_until": None,
            "reason": "Explicit authored qualification, not factual adjudication.",
        },
    }


def plan(test):
    nodes = []
    summaries = {}
    for name in test.quality["sources"]:
        segment = {
            "id": name + "-segment",
            "layer": "normalized-segment",
            "action": "keep",
            "inputs": [],
            "rationale": "Retain exact fictional evidence.",
            "curation_candidate": None,
            "supersedes": [],
            "statements": [statement(test, name, test.text[name], name + "-quoted")],
        }
        key = "business-corrected" if name == "business" and test.revised else name
        summary = {
            **deepcopy(segment),
            "id": name + "-summary",
            "layer": "source-summary",
            "action": "summarize",
            "inputs": [segment["id"]],
            "rationale": "Authored bounded summary retaining qualifications.",
            "statements": [
                statement(
                    test,
                    name,
                    test.quality["summary"][key],
                    name + "-summary-statement",
                )
            ],
        }
        summaries[name] = summary
        nodes += [segment, summary]
    synthesis = {
        **deepcopy(summaries["business"]),
        "id": "synthesis",
        "layer": "cross-source-synthesis",
        "action": "merge",
        "inputs": ["business-summary", "conversation-summary"],
        "statements": [
            deepcopy(summaries[name]["statements"][0])
            for name in ("business", "conversation")
        ],
    }
    for index, value in enumerate(synthesis["statements"]):
        value["id"] = "synthesis-" + str(index)
    context = {
        **deepcopy(synthesis),
        "id": "context",
        "layer": "context",
        "action": "summarize",
        "inputs": ["synthesis"],
    }
    for index, value in enumerate(context["statements"]):
        value["id"] = "context-" + str(index)
    unrelated = {
        **deepcopy(summaries["career"]),
        "id": "unrelated-context",
        "layer": "context",
        "inputs": ["career-summary"],
    }
    unrelated["statements"][0]["id"] = "unrelated-context-statement"
    nodes += [synthesis, context, unrelated]
    return {
        "schema": "mindgarden.compaction-plan/v1",
        "id": "fictional-multisource-refresh",
        "garden": "synthetic-garden",
        "created_at": TIME,
        "scope": local_scope(publication="never-exportable"),
        "budget_profile": "personal",
        "retention": read_object(FIXTURE_ROOT / "retention-policy.json"),
        "nodes": nodes,
        "outputs": ["context", "unrelated-context"],
        "curation_plan_sha256": None,
    }
