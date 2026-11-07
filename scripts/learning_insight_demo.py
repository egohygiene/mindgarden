#!/usr/bin/env python3
"""Reproduce authored learning/insight CLI goldens in source or installed mode.

Only disposable synthetic fixtures are accepted; no arbitrary source path/CLI.
"""

from argparse import ArgumentParser
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
parser = ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument("--require-source", action="store_true")
mode.add_argument("--require-installed", action="store_true")
arguments = parser.parse_args()
if arguments.require_source:
    sys.path.insert(0, str(ROOT / "src"))
import mindgarden

expected = (
    (ROOT / "src").resolve() if arguments.require_source else Path(sys.prefix).resolve()
)
if not Path(mindgarden.__file__).resolve().is_relative_to(expected):
    raise RuntimeError("Requested engine origin is unavailable")
sys.path.insert(0, str(ROOT))
from mindgarden.domain.contracts import canonical_json, digest_bytes
from tests import learning_fixture, insight_fixture

CHILD = """
from datetime import datetime, timezone
from unittest.mock import patch
import sys
from mindgarden.application.query import QueryContext
from mindgarden.interfaces.cli import main
original=QueryContext.load
def fixed(*args,**kwargs):
 kwargs["clock"]=lambda:datetime(2026,11,7,tzinfo=timezone.utc)
 return original(*args,**kwargs)
with patch("socket.socket",side_effect=AssertionError("Network attempted")),patch.object(QueryContext,"load",side_effect=fixed):
 raise SystemExit(main(sys.argv[1:]))
"""


def cli(command):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    if arguments.require_source:
        environment["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-S" if arguments.require_source else "-I",
            "-c",
            CHILD,
            *command,
        ],
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode:
        raise RuntimeError("Synthetic authored-plan CLI failed: " + result.stderr)
    return json.loads(result.stdout)


def prove(command, configuration, scope, request, root, golden):
    path = root / "authored-plan.json"
    path.write_bytes(canonical_json(request))
    argv = [
        command,
        "--local-config",
        str(configuration),
        "--scope",
        str(scope),
        "--input",
        str(path),
    ]
    preview = cli(argv)
    output = root / "projection"
    applied = cli(
        argv
        + [
            "--apply",
            "--plan-digest",
            preview["plan_sha256"],
            "--output-directory",
            str(output),
        ]
    )
    assert applied["status"] == "created"
    actual = {
        name: digest_bytes((output / name).read_bytes()) for name in golden["files"]
    }
    assert actual == golden["files"]
    assert (
        sum((output / name).stat().st_size for name in golden["files"])
        == golden["total_bytes"]
    )
    return output, preview


def main():
    case = unittest.TestCase()
    try:
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            learning_fixture.setup(case)
            golden = json.loads(
                (ROOT / "tests/fixtures/learning/expected-proof.json").read_text()
            )
            output, preview = prove(
                "learning",
                case.configuration,
                case.session_path,
                case.request,
                case.root,
                golden,
            )
            imported = cli(
                [
                    "learning",
                    "--local-config",
                    str(case.configuration),
                    "--scope",
                    str(case.session_path),
                    "--import-projection",
                    str(output / "learning-projection.json"),
                    "--events",
                    str(output / "learning-review-history.json"),
                ]
            )
            assert imported["projection"] == preview["projection"]
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                fixture, request = insight_fixture.setup(root / "fixture")
                golden = json.loads(
                    (ROOT / "tests/fixtures/insights/expected-proof.json").read_text()
                )
                prove(
                    "insights",
                    fixture["configuration"],
                    fixture["session_path"],
                    request,
                    root,
                    golden,
                )
        modules = [
            module
            for name, module in list(sys.modules.items())
            if name == "mindgarden" or name.startswith("mindgarden.")
        ]
        assert all(
            Path(module.__file__).resolve().is_relative_to(expected)
            for module in modules
            if getattr(module, "__file__", None)
        )
        print(
            json.dumps(
                {
                    "status": "passed",
                    "engine": "source" if arguments.require_source else "installed",
                    "learning": "exact golden + CLI apply/import",
                    "insights": "exact golden + CLI apply",
                    "network": "Python socket guards in parent and CLI children",
                    "models": "not-used",
                    "real_inputs": "not-accepted",
                },
                sort_keys=True,
            )
        )
    finally:
        case.doCleanups()


if __name__ == "__main__":
    main()
