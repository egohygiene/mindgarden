#!/usr/bin/env python3
"""Synthetic captured ledger, reviewed packet and replaceable CLI research clients."""

from argparse import ArgumentParser
from copy import deepcopy
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "src"))
    import mindgarden

from mindgarden.application.pilot import preflight
from mindgarden.application.query import QueryContext
from mindgarden.domain.contracts import canonical_json, digest_bytes

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from drive_consultation_demo import run_demo as drive_demo
from tests.consultation_fixture import cli
from tests.research_fixture import request_for
from tests.support_v1 import write_json


def run_demo(workspace):
    report = drive_demo(workspace)
    config, session = workspace / "clean-bindings.json", workspace / "session.json"
    context = QueryContext.load(config, session)
    outputs, plans = [], []
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
        patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")),
        patch("subprocess.run", side_effect=AssertionError("Process attempted")),
    ):
        for planner in (
            "search-first",
            "graph-first",
            "provider-removed-direct-search",
        ):
            request = request_for(context, [report["evidence"]], planner=planner)
            if planner == "provider-removed-direct-search":
                request["steps"] = request["steps"][:1]
            for step in request["steps"]:
                if step["operation"] == "graph":
                    step["start"] = "synthetic-garden/synthetic-financial-summary"
            path = workspace / (planner + ".json")
            write_json(path, request)
            result = cli(
                [
                    "research",
                    "--input",
                    str(path),
                    "--local-config",
                    str(config),
                    "--scope",
                    str(session),
                ]
            )
            assert result["status"] == "observations-available"
            assert (
                result["usage"]["model_calls"] == 0 and result["interpretations"] == []
            )
            assert result["scope"]["publication"] == "never-exportable"
            assert b"2259.76" in canonical_json(result)
            assert str(workspace).encode() not in canonical_json(result)
            outputs.append(result)
            plans.append(request)
        workspace.chmod(0o700)
        config.chmod(0o600)
        session.chmod(0o600)
        ready = preflight(
            config, session, "synthetic-garden", "synthetic-vault", "personal"
        )
        assert ready["status"] == "ready-to-attempt"
    evidence = next(
        item["payload"]
        for item in outputs[0]["observations"]
        if item["operation"] == "source-evidence"
    )
    assert evidence["source"] == report["evidence"]["source"]
    result = {
        "schema": "mindgarden.synthetic-research-proof/v1",
        "status": "passed-bounded-synthetic-workflow",
        "packet_proof": report,
        "callers": [
            {
                "id": item["planner"]["id"],
                "operations": [v["operation"] for v in item["observations"]],
                "request_sha256": digest_bytes(canonical_json(plan)),
                "result_sha256": digest_bytes(canonical_json(item)),
                "usage": item["usage"],
            }
            for plan, item in zip(plans, outputs, strict=True)
        ],
        "evidence": deepcopy(report["evidence"]),
        "preflight": ready,
        "codex_interface": "ordinary CLI exercised; Codex runtime/model unperformed",
        "model_accuracy": "not evaluated",
        "private_pilot": "not performed",
        "source_instructions": "untrusted data; no execution or publication authority",
    }
    return result


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="New synthetic private POSIX directory outside Git",
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--check-golden", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    args = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    if args.require_source and not engine.is_relative_to(ROOT / "src"):
        parser.error("Exact source engine required")
    if args.require_installed and (
        engine.is_relative_to(ROOT / "src")
        or not engine.is_relative_to(Path(sys.prefix).resolve())
    ):
        parser.error("Installed engine required")
    encoded = canonical_json(run_demo(args.workspace.absolute()))
    if (
        args.check_golden
        and encoded
        != (ROOT / "tests/fixtures/research/expected-proof.json").read_bytes()
    ):
        raise AssertionError("Complete research proof differs from committed golden")
    if args.report:
        with args.report.open("xb") as output:
            output.write(encoded)
    print(encoded.decode(), end="")


if __name__ == "__main__":
    main()
