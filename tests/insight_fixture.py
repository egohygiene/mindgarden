"""Public synthetic producer data; no renderer or publishing service."""

from copy import deepcopy

from tests.federation_fixture import create_fixture
from tests.support_v1 import write_json
from mindgarden.application.query import QueryContext


def setup(root):
    fixture = create_fixture(root)
    context = fixture["context"]
    session = deepcopy(context.session)
    session["budgets"]["max_context_bytes"] = 131072
    write_json(fixture["session_path"], session)
    context = QueryContext.load(fixture["configuration"], fixture["session_path"])
    fixture["context"] = context
    records = fixture["bundle"].files["index.json"]
    import json

    records = json.loads(records)["records"]
    refs = [
        r["reference"]
        for r in records
        if r["reference"]["id"] in {"reviewed-prompt", "reviewed-claim"}
    ]
    review = {
        "state": "approved",
        "reviewers": ["synthetic-reviewer"],
        "reviewed_at": "2026-11-07T00:00:00Z",
        "rationale": "Authored synthetic rights and content review.",
    }
    rights = {
        "status": "approved",
        "license": "CC0-1.0 (synthetic fixture declaration)",
        "attribution": "Synthetic fixture author",
        "review": deepcopy(review),
    }
    candidate = {
        "schema": "mindgarden.insight-candidate/v1",
        "id": "evidence-insight",
        "garden": "repository-garden",
        "objective": "Keep exact evidence attached to reviewed knowledge.",
        "audience": "Knowledge tool builders",
        "intended_use": "A reviewed teaching handoff; no posting authority.",
        "claims": [
            {
                "id": "evidence-claim",
                "text": "Retain exact source evidence with reviewed knowledge.",
                "representation": "paraphrase",
                "certainty": "qualified",
                "references": refs,
                "rights": deepcopy(rights),
            }
        ],
        "uncertainty": ["Synthetic example, not a factual research conclusion."],
        "review": review,
        "publication": "eligible-for-reviewed-handoff",
        "rights": rights,
        "visual": {
            "form": "single-insight",
            "hierarchy": ["Teaching objective", "Qualified claim", "Evidence trail"],
        },
        "caption": "A synthetic example of evidence-backed knowledge.",
        "alt_text": "A teaching claim linked to its exact synthetic evidence.",
        "channel": {"name": "unassigned", "format": "renderer-independent"},
        "lifecycle": "approved",
        "supersedes": [],
    }
    request = {
        "schema": "mindgarden.insight-plan/v1",
        "review": deepcopy(review),
        "review_authority": {"kind": "human", "id": "synthetic-reviewer"},
        "max_bytes": 131072,
        "candidates": [candidate],
        "series": [],
        "artifact_events": [],
    }
    return fixture, request
