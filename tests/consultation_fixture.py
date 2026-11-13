"""Synthetic account capture and authored review; never real financial input."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path

from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.ledger import transaction_key
from mindgarden.domain.scope import local_scope
from mindgarden.interfaces.cli import main
from tests.support_v1 import TIME, create_garden, write_json, write_session

FIXTURES = Path(__file__).parent / "fixtures/consultation"


def cli(args):
    with redirect_stdout(io.StringIO()) as output:
        status = main(args)
    if status:
        raise AssertionError("Synthetic ledger command failed")
    return json.loads(output.getvalue())


def create_fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    garden = root / "garden"
    create_garden(garden)
    config = root / "bindings.json"
    write_json(
        config,
        {
            "schema": "mindgarden.local-bindings/v1",
            "gardens": [
                {"id": "synthetic-garden", "root": str(garden), "scope": local_scope()}
            ],
            "vaults": [
                {
                    "id": "synthetic-vault",
                    "root": str(root / "vault"),
                    "adapter": "filesystem",
                }
            ],
            "revoked_sessions": [],
        },
    )
    args = [
        "vault",
        "init",
        "--local-config",
        str(config),
        "--vault-id",
        "synthetic-vault",
    ]
    planned = cli(args)
    cli(args + ["--apply", "--plan-digest", planned["plan_sha256"]])
    all_sources, imports = {}, []
    for filename in ("account-a.csv", "account-a-overlap.csv", "account-b.csv"):
        path = root / filename
        path.write_bytes((FIXTURES / filename).read_bytes())
        args = [
            "ingest",
            "--repository-root",
            str(garden),
            "--local-config",
            str(config),
            "--vault-id",
            "synthetic-vault",
            "--input",
            str(path),
            "--source-id",
            filename.removesuffix(".csv"),
            "--title",
            "Synthetic account export",
            "--origin",
            "urn:synthetic:" + filename,
            "--captured",
            TIME,
            "--owner",
            "synthetic-owner",
            "--rights",
            "Wholly synthetic test data.",
            "--media-type",
            "text/csv",
            "--adapter",
            "ledger-csv",
            "--manifest-version",
            "1.0.0",
        ]
        planned = cli(args)
        cli(args + ["--apply", "--plan-digest", planned["plan_sha256"]])
        imports.append({"arguments": args, "planned": planned})
        for unit in planned["inputs"]["normalized_sources"]:
            citation = unit["evidence"][0]
            all_sources[citation["source"]["id"]] = citation
    session_path = root / "session.json"
    session = write_session(session_path, config)
    session.update(
        request_scope=local_scope(publication="never-exportable"),
        source_grants=[item["source"] for item in all_sources.values()],
    )
    session["projections"].append("source-evidence")
    session["budgets"]["max_context_bytes"] = 262144
    write_json(session_path, bind_session_revisions(config, session))
    sources = sorted(all_sources.values(), key=lambda item: item["source"]["id"])
    rows = [
        ("account-a", "payroll", "income"),
        ("account-a", "groceries", "expense"),
        ("account-a", "transfer-out", "transfer"),
        ("account-a", "unclear", "uncategorized"),
        ("account-a", "refund", "refund"),
        ("account-a", "utilities", "expense"),
        ("account-b", "transfer-in", "transfer"),
        ("account-b", "supplies", "expense"),
    ]
    outgoing = transaction_key("account-a", "transfer-out")
    incoming = transaction_key("account-b", "transfer-in")
    decisions = [
        {
            "transaction": transaction_key(account, identity),
            "category": category,
            "paired_with": incoming
            if identity == "transfer-out"
            else outgoing
            if identity == "transfer-in"
            else None,
            "rationale": "Explicit authored synthetic review; uncertainty retained.",
        }
        for account, identity, category in rows
    ]
    request = {
        "schema": "mindgarden.consultation-request/v1",
        "id": "synthetic-consultation",
        "created_at": TIME,
        "scope": local_scope(publication="never-exportable"),
        "review_authority": {"kind": "human", "id": "synthetic-reviewer"},
        "review": {
            "state": "approved",
            "reviewers": ["synthetic-reviewer"],
            "reviewed_at": TIME,
            "rationale": "Synthetic human selects calculations and evidence for private preparation.",
        },
        "period": {"start": "2026-01-01", "end": "2026-01-31"},
        "accounts": ["account-a", "account-b", "missing-account"],
        "currencies": [{"code": "USD", "scale": 2}],
        "sources": sources,
        "decisions": decisions,
        "revisions": [],
        "selection": sorted(item["transaction"] for item in decisions),
        "attachments": [transaction_key("account-a", "groceries")],
        "coverage": [
            {
                "account": "account-a",
                "start": "2026-01-01",
                "end": "2026-01-31",
                "rationale": "Declared synthetic export coverage, not completeness certification.",
            },
            {
                "account": "account-b",
                "start": "2026-01-10",
                "end": "2026-01-31",
                "rationale": "Declared partial coverage; earlier transactions do not fill the declared gap.",
            },
        ],
        "questions": [
            "What explains the unclassified movement?",
            "Which missing accounts and statements are still needed?",
        ],
        "limits": {"max_rows": 1000, "max_bytes": 131072},
    }
    request_path = root / "request.json"
    request_path.write_bytes(canonical_json(request))
    return {
        "root": root,
        "garden": garden,
        "configuration": config,
        "session_path": session_path,
        "context": QueryContext.load(config, session_path),
        "request": request,
        "request_path": request_path,
        "imports": imports,
    }
