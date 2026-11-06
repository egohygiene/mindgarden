#!/usr/bin/env python3
"""Reproduce the new product CLI checkpoints with disposable synthetic fixtures."""

from argparse import ArgumentParser
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
parser = ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument("--require-installed", action="store_true")
mode.add_argument("--require-source", action="store_true")
arguments = parser.parse_args()
if arguments.require_source:
    sys.path.insert(0, str(ROOT / "src"))
import mindgarden

EXPECTED = (
    Path(sys.prefix).resolve()
    if arguments.require_installed
    else (ROOT / "src").resolve()
)
if not Path(mindgarden.__file__).resolve().is_relative_to(EXPECTED):
    raise RuntimeError("The requested engine origin is unavailable")
sys.path.insert(0, str(ROOT))
from tests import dependency_fixture, memory_fixture
from tests import test_bookmarks as bookmark_tests
from mindgarden.domain.contracts import canonical_json

# The only inputs are fixtures created by this script. Freeze their review clock;
# no real session, archive or arbitrary CLI command is accepted by the demo.
CHILD = """
from datetime import datetime, timezone
from unittest.mock import patch
import sys
from mindgarden.application.query import QueryContext
from mindgarden.interfaces.cli import main
original = QueryContext.load
def fixed_load(*args, **kwargs):
    kwargs["clock"] = lambda: datetime(2026, 11, 6, tzinfo=timezone.utc)
    return original(*args, **kwargs)
with patch("socket.socket", side_effect=AssertionError("Network attempted")), patch.object(QueryContext, "load", side_effect=fixed_load):
    raise SystemExit(main(sys.argv[1:]))
"""


def cli(command):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    if arguments.require_source:
        environment["PYTHONPATH"] = str(ROOT / "src")
    flag = "-I" if arguments.require_installed else "-S"
    result = subprocess.run(
        [sys.executable, flag, "-c", CHILD, *command],
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode:
        raise RuntimeError("A synthetic product CLI checkpoint failed")
    return json.loads(result.stdout)


def prove_memory_and_store():
    case = unittest.TestCase()
    try:
        memory_fixture.setup(case)
        request = case.root / "memory.json"
        request.write_bytes(canonical_json(case.request))
        command = [
            "memory",
            "--local-config",
            str(case.configuration),
            "--scope",
            str(case.session_path),
            "--input",
            str(request),
        ]
        plan = cli(command)
        assert plan["metrics"] == json.loads(
            (ROOT / "tests/fixtures/memory/expected-metrics.json").read_text()
        )
        assert not plan["violations"]
        assert (
            cli(
                command
                + [
                    "--apply",
                    "--output-directory",
                    str(case.root / "memory-export"),
                    "--plan-digest",
                    plan["plan_sha256"],
                ]
            )["status"]
            == "created"
        )
        command = [
            "query-store",
            "--local-config",
            str(case.configuration),
            "--scope",
            str(case.session_path),
            "--cache-directory",
            str(case.root / "query-cache"),
        ]
        plan = cli(command + ["--operation", "plan"])
        assert (
            cli(
                command + ["--operation", "build", "--plan-digest", plan["plan_sha256"]]
            )["status"]
            == "rebuilt"
        )
        assert cli(command + ["--operation", "search", "--query", "citations"])[
            "results"
        ]
        assert cli(command + ["--operation", "audit"])["status"] == "verified"
    finally:
        case.doCleanups()


def prove_dependency_builds():
    case = unittest.TestCase()
    try:
        dependency_fixture.setup(case)
        request = case.root / "build.json"
        request.write_bytes(canonical_json(case.request))
        command = [
            "build-projections",
            "--local-config",
            str(case.configuration),
            "--scope",
            str(case.session_path),
            "--input",
            str(request),
        ]
        plan = cli(command)
        previous = case.root / "build-export"
        assert (
            cli(
                command
                + [
                    "--apply",
                    "--output-directory",
                    str(previous),
                    "--plan-digest",
                    plan["plan_sha256"],
                ]
            )["status"]
            == "created"
        )
        dependency_fixture.update(case)
        request.write_bytes(canonical_json(case.request))
        result = cli(
            command
            + ["--previous-manifest", str(previous / "projection-dependencies.json")]
        )
        assert {row["id"]: row["state"] for row in result["outputs"]} == {
            "agent-context": "stale",
            "professional-profile": "stale",
            "unrelated-view": "current",
        }
    finally:
        case.doCleanups()


def prove_bookmarks():
    case = bookmark_tests.BookmarkTests()
    try:
        case.setUp()
        request = case.root / "request.json"
        request.write_bytes(canonical_json(case.request))
        plan_file = case.root / "private-plan.json"
        command = [
            "bookmarks",
            "--classification",
            "personal",
            "--input",
            str(case.source),
            "--catalog",
            str(case.catalog),
            "--request",
            str(request),
            "--plan-file",
            str(plan_file),
        ]
        assert cli(command)["status"] == "private-plan-written"
        plan = json.loads(plan_file.read_text())
        destination = case.root / "private-export"
        result = cli(
            command
            + [
                "--apply",
                "--output-directory",
                str(destination),
                "--plan-digest",
                plan["plan_sha256"],
            ]
        )
        assert result["public_handoff"] == "unavailable"
        assert (
            len(
                json.loads((destination / "cleaned-bookmarks.json").read_text())[
                    "records"
                ]
            )
            == 3
        )
    finally:
        case.doCleanups()


with patch("socket.socket", side_effect=AssertionError("Network attempted")):
    prove_memory_and_store()
    prove_dependency_builds()
    prove_bookmarks()
for name in (
    "application.memory",
    "application.query_store",
    "adapters.sqlite_query",
    "application.dependency_builds",
    "application.bookmarks",
):
    if (
        not Path(importlib.import_module("mindgarden." + name).__file__)
        .resolve()
        .is_relative_to(EXPECTED)
    ):
        raise RuntimeError("A product service used an unexpected engine origin")
print(
    json.dumps(
        {
            "schema": "mindgarden.synthetic-product-checkpoint/v1",
            "memory": "passed",
            "query_store": "passed",
            "dependency_reconciliation": "passed",
            "private_bookmarks": "passed",
            "akashic_public_handoff": "unavailable",
            "unexpected_source_fallback": False,
            "network": "blocked-in-process",
            "clock": "synthetic-2026-11-06",
        },
        sort_keys=True,
        indent=2,
    )
)
