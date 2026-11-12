"""Data recipes shared by mixed-media tests and the standalone offline journey."""

from copy import deepcopy

from mindgarden.domain.contracts import canonical_json, strict_json
from tests.archive_fixture import FIXTURE_ROOT, diagram_members


def curation_members():
    members = diagram_members()
    conversation = strict_json(members["CONVERSATION.json"])
    conversation["messages"] += strict_json(
        (FIXTURE_ROOT / "diagram-journey/review-messages.json").read_bytes()
    )
    members["CONVERSATION.json"] = canonical_json(conversation)
    return members


def mixed_proposal(imported):
    recipe = strict_json(
        (FIXTURE_ROOT / "diagram-journey/curation-recipe.json").read_bytes()
    )
    proposal = deepcopy(recipe["proposal"])
    for candidate in proposal["candidates"]:
        evidence = []
        for suffix, locator in recipe["evidence_selection"][candidate["id"]]:
            kind, identity = suffix.lstrip(":").split(":", 1)
            key = "message_id" if kind == "message" else "asset_id"
            unit = next(
                item
                for item in imported.inputs["normalized_sources"]
                if item["metadata"].get(key) == identity
                and (
                    kind == "message"
                    or item["metadata"]["evidence_kind"]
                    == ("asset-catalog" if kind == "asset-catalog" else "asset-bytes")
                )
            )
            evidence.append(
                deepcopy(next(e for e in unit["evidence"] if e["locator"] == locator))
            )
        candidate["sources"] = evidence
        if candidate.get("output", {}).get("redactions"):
            candidate["output"]["redactions"][0]["source"] = deepcopy(evidence[1])
    return proposal
