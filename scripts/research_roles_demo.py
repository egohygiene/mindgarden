#!/usr/bin/env python3
"""Rehearse two assistant tasks against the same fictional garden."""

from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
import os
from pathlib import Path
import shlex
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from mock_garden_demo import create_file, mindgarden, run_demo as build_mock_garden

from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object
from mindgarden.interfaces.cli import main as garden_cli

ROLES = {
    "accounting-preparation": (
        "What reviewed amounts and limitations help prepare the consultation?",
        "net movement",
        "synthetic-financial-summary",
    ),
    "career-planning": (
        "What accessibility portfolio experiment is under consideration?",
        "keyboard-navigation",
        "mock-career",
    ),
}


def author_request(role, question, session, tools, steps, *, sources=()):
    return {
        "schema": "mindgarden.research-request/v1",
        "id": role + ("-evidence" if sources else "-read"),
        "question": question,
        "planner": {"id": role, "kind": "external-client"},
        "gardens": session["readable"],
        "sources": list(sources),
        "allowed_tools": tools,
        "expires_at": session["expires_at"],
        "budgets": {
            "max_steps": len(steps),
            "max_results": 4,
            "max_bytes": 24576,
            "max_elapsed_ms": 60000,
            "max_model_calls": 0,
        },
        "steps": steps,
    }


def arguments(config, session, request):
    return [
        "research",
        "--local-config",
        str(config),
        "--scope",
        str(session),
        "--input",
        str(request),
        "--diagnostic-format",
        "json",
    ]


def invoke(config, session, request, *, expected_error=None):
    with redirect_stdout(StringIO()) as stdout, redirect_stderr(StringIO()) as stderr:
        status = garden_cli(arguments(config, session, request))
    if expected_error:
        assert status == 3 and stdout.getvalue() == ""
        report = json.loads(stderr.getvalue())
        assert [item["code"] for item in report["diagnostics"]] == [expected_error]
        return report
    assert status == 0, stderr.getvalue()
    assert stderr.getvalue() == ""
    result = json.loads(stdout.getvalue())
    assert result["status"] == "observations-available"
    assert result["scope"]["publication"] == "never-exportable"
    assert result["usage"]["model_calls"] == 0 and result["interpretations"] == []
    return result


def plan_role(role, task, record, config, base_session, output):
    question, query, identity = task
    citation = record["sources"][0]
    session = deepcopy(base_session)
    session.update(
        id=role + "-fixture",
        writable=None,
        projections=["search", "context", "source-evidence"],
        source_grants=[citation["source"]],
    )
    session = bind_session_revisions(config, session)
    session_path = output / (role + "-session.json")
    create_file(session_path, canonical_json(session))
    federation = {
        "schema": "mindgarden.local-federation-query/v1",
        "gardens": session["readable"],
    }
    profile = {
        "schema": "mindgarden.context-profile/v1",
        "id": role,
        "garden": record["reference"]["garden"],
        "title": role.replace("-", " ").title(),
        "description": question,
        "query": query,
        "include": [record["reference"]],
        "exclude": [],
        "kinds": [],
        "max_items": 1,
        "max_bytes": 8192,
        "max_candidates": 1,
    }
    request = author_request(
        role,
        question,
        session,
        ["search", "context"],
        [
            {**federation, "operation": "search", "query": query, "limit": 1},
            {
                **federation,
                "operation": "context",
                "profile": profile,
                "format": "json",
            },
        ],
    )
    request_path = output / (role + "-read.json")
    create_file(request_path, canonical_json(request))
    result = invoke(config, session_path, request_path)
    search, context = (item["payload"] for item in result["observations"])
    assert [item["reference"]["id"] for item in search["results"]] == [identity]
    assert [item["reference"]["id"] for item in context["included"]] == [identity]
    assert search["results"][0]["selection_reasons"]
    assert context["included"][0]["selection_reason"] == "explicit-include"
    assert context["included"][0]["review"]["state"] == "approved"
    returned = context["included"][0]["sources"][0]
    assert returned == citation

    followup = author_request(
        role,
        question,
        session,
        ["source-evidence"],
        [{"operation": "source-evidence", "citation": returned}],
        sources=[returned],
    )
    followup_path = output / (role + "-evidence.json")
    create_file(followup_path, canonical_json(followup))
    evidence_result = invoke(config, session_path, followup_path)
    evidence = evidence_result["observations"][0]["payload"]
    assert all(evidence[field] == value for field, value in returned.items())
    assert digest_bytes(evidence["text"].encode()) == returned["content_sha256"]
    assert evidence["trust"] == "untrusted-evidence"
    assert evidence["source_review"]["state"] == "unreviewed"
    return {
        "session_path": session_path,
        "request_path": request_path,
        "followup_path": followup_path,
        "citation": citation,
        "proof": {
            "selected_knowledge": identity,
            "scope_sha256": result["authority_sha256"],
            "read_result_sha256": digest_bytes(canonical_json(result)),
            "evidence_result_sha256": digest_bytes(canonical_json(evidence_result)),
        },
    }


def workflow(workspace, profile, command):
    config, base_path = (
        workspace / "clean-bindings.json",
        workspace / "mock-session.json",
    )
    output = workspace / "research-roles"
    output.mkdir(mode=0o700)
    create_file(output / "codex.md", profile.read_bytes())
    context = QueryContext.load(config, base_path)
    records = {item["id"]: item for item in build_index(context)["records"]}
    base_session = read_object(base_path)
    reports = {
        role: plan_role(role, task, records[task[2]], config, base_session, output)
        for role, task in ROLES.items()
    }
    accounting, career = (reports[role] for role in ROLES)
    assert accounting["citation"]["source"] != career["citation"]["source"]
    assert accounting["proof"]["scope_sha256"] != career["proof"]["scope_sha256"]
    # An accounting planner label and exact accounting citation do not grant
    # the career session the corresponding first-pass source permission.
    with patch.object(
        QueryContext, "snapshots", side_effect=AssertionError("Denied body read")
    ):
        denied = invoke(
            config,
            career["session_path"],
            accounting["followup_path"],
            expected_error="RESEARCH_SOURCE_DENIED",
        )
    diagnostic = canonical_json(denied)
    assert accounting["citation"]["source"]["id"].encode() not in diagnostic
    assert str(workspace).encode() not in diagnostic

    guide = [
        "# Fictional assistant tasks",
        "",
        "Use the [Codex profile](codex.md) as task instructions. All inputs are fictional.",
        "Start with one task and inspect its cited observations. The second command",
        "reads one exact cited source using the separate source grant in that task's session.",
    ]
    for role, result in reports.items():
        guide.extend(("", "## " + role.replace("-", " ").title(), "", "```sh"))
        guide.extend(
            shlex.join(
                [*command, *arguments(config, result["session_path"], result[key])]
            )
            for key in ("request_path", "followup_path")
        )
        guide.append("```")
    guide.extend(
        (
            "",
            "Both sessions can read reviewed knowledge in this fictional garden.",
            "The task chooses the context to return, and the session grants the exact",
            "first-pass source read. Try the accounting evidence plan with the career",
            "session to see the denial. Keep generated paths and session files local.",
        )
    )
    create_file(output / "START-HERE.md", ("\n".join(guide) + "\n").encode())
    return {
        "status": "passed-fictional-research-roles",
        "roles": {role: result["proof"] for role, result in reports.items()},
        "cross_session_citation": "RESEARCH_SOURCE_DENIED",
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--check-golden", action="store_true")
    origin = parser.add_mutually_exclusive_group()
    origin.add_argument("--require-source", action="store_true")
    origin.add_argument("--require-installed", action="store_true")
    args = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    source = engine.is_relative_to(ROOT / "src")
    if args.require_source and not source:
        parser.error("Exact source engine required")
    if args.require_installed and (
        source or not engine.is_relative_to(Path(sys.prefix).resolve())
    ):
        parser.error("Installed engine required")
    if source:
        profile = ROOT / "profiles/agent/codex.md"
        command = [
            "env",
            "PYTHONPATH=" + str(ROOT / "src"),
            sys.executable,
            "-m",
            "mindgarden",
        ]
    else:
        profile = Path(sys.prefix) / "share/mindgarden/profiles/agent/codex.md"
        command = [sys.executable, "-I", "-m", "mindgarden"]
    workspace = args.workspace.absolute()
    build_mock_garden(workspace)
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
        patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")),
        patch(
            "subprocess.run", side_effect=AssertionError("External process attempted")
        ),
    ):
        result = canonical_json(workflow(workspace, profile, command))
    golden = ROOT / "tests/fixtures/research/expected-roles-proof.json"
    if args.check_golden and result != golden.read_bytes():
        raise AssertionError(
            "Fictional research proof differs from the committed golden"
        )
    print(result.decode(), end="")


if __name__ == "__main__":
    main()
