"""Authored GitHub-activity interpretation; no remote capture or expertise inference."""

from copy import deepcopy
import json
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index, record_key
from tests.support_v1 import (
    FIXTURES,
    add_knowledge,
    reference,
    write_json,
    write_session,
)
from tests import test_source_adapters as source_tests


def setup(test):
    source_tests.SourceAdapterTests.setUp(test)
    test.input.write_text(
        "Synthetic GitHub activity: commit 1111111 implements one deployment.\nNot evidence of expertise.\n"
    )
    test.metadata["origin"] = "https://example.test/synthetic/repository/commit/1111111"
    plan = source_tests.SourceAdapterTests.plan(test)
    apply_ingestion(plan, plan.digest, test.bindings, "synthetic-vault")
    evidence = plan.inputs["normalized_sources"][0]["evidence"]
    first = add_knowledge(test.workspace, sources=evidence)
    add_knowledge(
        test.workspace,
        "unrelated-procedure",
        body="Synthetic unrelated procedure.\n",
        sources=evidence,
    )
    claim = json.loads((FIXTURES / "claim.json").read_text())
    claim.update(
        id="work-claim",
        garden="synthetic-garden",
        subject=reference("synthetic-garden", first["id"]),
        statement="Implemented one synthetic deployment; no expertise claim.",
        visibility="private",
        status="active",
        review=first["review"],
        evidence=[
            {
                "relationship": "supports",
                "target": evidence[0],
                "rationale": "Exact bounded synthetic GitHub event.",
            }
        ],
    )
    write_json(test.workspace / ".garden/claims/work-claim.json", claim)
    test.session_path = test.root / "session.json"
    write_session(test.session_path, test.configuration)
    test.context = QueryContext.load(test.configuration, test.session_path)
    test.request = make_request(test.context)


def make_request(context):
    index = build_index(context)
    by = {record_key(r["reference"]): r for r in index["records"]}
    claim = by["synthetic-garden/work-claim"]
    review = deepcopy(claim["review"])
    scope = context.output_scope([claim["scope"]])
    observation = {
        "schema": "mindgarden.observation/v1",
        "id": "observed-deployment",
        "state": "reviewed",
        "kind": "implemented",
        "interpretation": "One synthetic commit implements one deployment; scope is bounded.",
        "claim": claim["reference"],
        "evidence": claim["sources"],
        "scope": scope,
        "confidence": "high",
        "review": review,
        "uncertainty": ["A commit is not a claim of expertise."],
        "first_supported_at": None,
        "last_supported_at": None,
        "stale_after": None,
        "relationships": [],
    }
    base = {
        "version": "1.0.0",
        "required_kinds": ["claim", "procedure"],
        "minimum_confidence": "low",
        "scope": scope,
        "redaction": "none",
        "renderer": "json-records/v1",
        "output_schema": "mindgarden.reviewed-record-view/v1",
        "max_bytes": 16384,
        "observations": [observation],
        "records": ["synthetic-garden/work-claim"],
    }
    outputs = [
        dict(deepcopy(base), id="professional-profile"),
        dict(deepcopy(base), id="agent-context"),
    ]
    unrelated = dict(
        deepcopy(base),
        id="unrelated-view",
        observations=[],
        records=["synthetic-garden/unrelated-procedure"],
    )
    return {
        "schema": "mindgarden.dependency-build-request/v1",
        "review_authority": {"kind": "human", "id": "synthetic-reviewer"},
        "review": review,
        "outputs": outputs + [unrelated],
    }


def update(test):
    test.input.write_text(
        "Synthetic GitHub activity: commit 2222222 revises the bounded deployment.\n"
    )
    test.metadata["origin"] = "https://example.test/synthetic/repository/commit/2222222"
    plan = source_tests.SourceAdapterTests.plan(test)
    apply_ingestion(plan, plan.digest, test.bindings, "synthetic-vault")
    evidence = plan.inputs["normalized_sources"][0]["evidence"]
    path = test.workspace / ".garden/claims/work-claim.json"
    claim = json.loads(path.read_text())
    claim["statement"] = (
        "Revised the bounded synthetic deployment; no expertise inferred."
    )
    claim["evidence"] = [
        {
            "relationship": "supports",
            "target": evidence[0],
            "rationale": "Reviewed replacement source revision.",
        }
    ]
    write_json(path, claim)
    write_session(test.session_path, test.configuration)
    test.context = QueryContext.load(test.configuration, test.session_path)
    test.request = make_request(test.context)
