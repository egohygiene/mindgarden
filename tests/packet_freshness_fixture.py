"""Authored synthetic correction; approval is fixture input, never inferred."""

from copy import deepcopy

from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import read_object
from mindgarden.domain.ledger import transaction_key
from tests.consultation_fixture import cli
from tests.support_v1 import write_json


def correct_fixture(fixture):
    original = fixture["root"] / "account-a.csv"
    original.write_bytes(original.read_bytes().replace(b"2500.00", b"2400.00"))
    arguments = fixture["imports"][0]["arguments"]
    preview = cli(arguments)
    cli(arguments + ["--apply", "--plan-digest", preview["plan_sha256"]])
    request = deepcopy(fixture["request"])
    old = {item["source"]["id"] for item in request["sources"]}
    changed = [
        item["evidence"][0]
        for item in preview["inputs"]["normalized_sources"]
        if item["source"]["id"] not in old
    ]
    assert len(changed) == 1
    request["sources"].extend(changed)
    request["revisions"] = [
        {
            "transaction": transaction_key("account-a", "payroll"),
            "source": changed[0]["source"],
            "rationale": "Author explicitly selects the corrected synthetic payroll; retain original evidence.",
        }
    ]
    request["review"]["rationale"] = (
        "New authored review of corrected synthetic evidence, classifications and output selection."
    )
    session = read_object(fixture["session_path"])
    session["source_grants"].extend(item["source"] for item in changed)
    write_json(
        fixture["session_path"],
        bind_session_revisions(fixture["configuration"], session),
    )
    write_json(fixture["request_path"], request)
    return {
        **fixture,
        "request": request,
        "context": QueryContext.load(fixture["configuration"], fixture["session_path"]),
    }
