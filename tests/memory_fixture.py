"""Verbose authored synthetic memory inputs, compacted through all seven actions."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index, record_key
from tests import test_source_adapters as source_tests
from mindgarden.application.ingestion import apply_ingestion
from tests.support_v1 import add_knowledge, write_json, write_session


def setup(test):
    source_tests.SourceAdapterTests.setUp(test)
    plan = source_tests.SourceAdapterTests.plan(test)
    apply_ingestion(plan, plan.digest, test.bindings, "synthetic-vault")
    evidence = plan.inputs["normalized_sources"][0]["evidence"]
    review = None
    for number in range(8):
        record = add_knowledge(
            test.workspace,
            f"memory-{number}",
            body=(
                "Synthetic preference: use exact citations and short instructions. This is authored context, not evidence of expertise.\n"
                * 12
            ),
            sources=evidence,
        )
        review = record["review"]
    test.session_path = test.root / "session.json"
    session = write_session(test.session_path, test.configuration)
    session["budgets"]["max_context_bytes"] = 65536
    write_json(test.session_path, session)
    clock = lambda: datetime(2026, 11, 6, tzinfo=timezone.utc)
    test.context = QueryContext.load(test.configuration, test.session_path, clock=clock)
    index = build_index(test.context)
    records = {record_key(r["reference"]): r for r in index["records"]}
    scope = test.context.output_scope([index["records"][0]["scope"]])
    template = {
        "title": "Synthetic citation preference",
        "body": "Prefer short, cited answers.",
        "category": "preference",
        "scope": scope,
        "durability": "durable",
        "half_life_days": 365,
        "confidence": "low",
        "priority": 80,
        "inclusion_reason": "Recurring reviewed preference.",
        "last_reviewed": review["reviewed_at"],
        "stale_after": None,
        "supersedes": [],
        "merges": [],
    }

    def output(identity, **changes):
        return dict(deepcopy(template), id=identity, **changes)

    def candidate(action, source_numbers, outputs):
        return {
            "id": action + "-example",
            "action": action,
            "sources": [
                records[f"synthetic-garden/memory-{n}"]["reference"]
                for n in source_numbers
            ],
            "rationale": "Authored synthetic "
            + action
            + " review; preserve the canonical detail.",
            "outputs": outputs,
        }

    candidates = [
        candidate("keep", [0], [output("keep-snippet")]),
        candidate(
            "merge",
            [1, 2],
            [output("merged-snippet", merges=["prior-one", "prior-two"])],
        ),
        candidate(
            "rewrite", [3], [output("rewritten-snippet", supersedes=["prior-wording"])]
        ),
        candidate("demote", [4], []),
        candidate("expire", [5], []),
        candidate(
            "split",
            [6],
            [
                output("split-preference"),
                output(
                    "split-workflow",
                    category="workflow",
                    body="Keep task inputs explicit.",
                ),
            ],
        ),
        candidate(
            "pin",
            [7],
            [
                output(
                    "pinned-history",
                    category="historical",
                    body="An explicitly pinned synthetic historical detail.",
                )
            ],
        ),
    ]
    retention = json.loads(
        (
            Path(__file__).parent / "fixtures/compaction/retention-policy.json"
        ).read_text()
    )
    test.request = {
        "schema": "mindgarden.memory-plan/v1",
        "scope": scope,
        "retention": retention,
        "review": review,
        "review_authority": {"kind": "human", "id": "synthetic-reviewer"},
        "target": {
            "id": "provider-neutral/v1",
            "tokenizer": "unavailable",
            "max_snippet_bytes": 1024,
        },
        "budgets": {
            "max_total_bytes": 32768,
            "max_tokens": None,
            "max_snippets": 8,
            "minimum_priority": 50,
            "category_quotas": {
                c: 8
                for c in [
                    "preference",
                    "identity",
                    "workflow",
                    "project-direction",
                    "temporary",
                    "historical",
                    "one-off",
                    "sensitive",
                ]
            },
        },
        "candidates": candidates,
    }
