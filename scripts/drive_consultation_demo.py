#!/usr/bin/env python3
"""Synthetic Drive capture/refresh to the same reviewed packet and recovery path."""

from argparse import ArgumentParser
from copy import deepcopy
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "src"))
    import mindgarden

from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.scope import local_scope

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from consultation_demo import run_demo as run_packet_demo
from tests.consultation_fixture import cli
from tests.drive_capture_fixture import create_capture_fixture
from tests.support_v1 import write_json, write_session


def captured_fixture(workspace):
    fixture = create_capture_fixture(workspace)
    provider, config, garden = (
        fixture[key] for key in ("provider", "configuration", "garden")
    )
    original = None
    normalized = None
    for number in (1, 2):
        if number == 2:
            provider.items["file-a"]["name"] = "Renamed synthetic export.csv"
            provider.items["file-a"]["version"] = "2"
            fixture["binding"]["captured_at"] = "2026-11-05T00:00:00Z"
            write_json(fixture["binding_path"], fixture["binding"])
        destination = workspace / ("capture-" + str(number))
        args = [
            "capture",
            "drive",
            "--input",
            str(fixture["binding_path"]),
            "--local-config",
            str(config),
            "--vault-id",
            "synthetic-vault",
            "--output-directory",
            str(destination),
        ]
        if number == 2:
            args += [
                "--previous-checkpoint",
                str(workspace / "capture-1.capture-checkpoint.json"),
            ]
        plan = cli(args)
        with patch(
            "mindgarden.application.drive_capture.GoogleDriveProvider",
            return_value=provider,
        ):
            cli(
                args
                + ["--apply", "--allow-network", "--plan-digest", plan["plan_sha256"]]
            )
        archive = destination / "capture.zip"
        if number == 1:
            original = archive.read_bytes()
        else:
            assert (workspace / "capture-1/capture.zip").read_bytes() == original
            assert archive.read_bytes() != original
        ingest = [
            "ingest",
            "--repository-root",
            str(garden),
            "--local-config",
            str(config),
            "--vault-id",
            "synthetic-vault",
            "--input",
            str(archive),
            "--source-id",
            "synthetic-drive-collection",
            "--title",
            "Synthetic selected Drive capture",
            "--owner",
            "synthetic-owner",
            "--rights",
            "Wholly synthetic provider fixture.",
            "--origin",
            "urn:synthetic:drive-collection",
            "--captured",
            fixture["binding"]["captured_at"],
            "--media-type",
            "application/vnd.mindgarden.drive-capture+zip",
            "--adapter",
            "drive-capture",
            "--manifest-version",
            "1.0.0",
            "--source-scope",
            str(destination / "source-scope.json"),
        ]
        planned = cli(ingest)
        cli(ingest + ["--apply", "--plan-digest", planned["plan_sha256"]])
        current = [
            item["evidence"][0] for item in planned["inputs"]["normalized_sources"]
        ]
        if normalized is not None:
            assert current == normalized
        normalized = current
        repeat = cli(ingest)
        assert (
            cli(ingest + ["--apply", "--plan-digest", repeat["plan_sha256"]])["applied"]
            is False
        )
    assert provider.reads.count("file-a") == 2
    assert provider.reads.count("file-b") == 1
    assert provider.reads.count("file-overlap") == 1
    assert len(normalized) == 8
    for record in (garden / ".garden/sources").glob("*.json"):
        assert json.loads(record.read_bytes())["scope"]["execution"] == "offline"
    request = deepcopy(
        json.loads(
            (
                ROOT / "tests/fixtures/contracts/v1/valid/consultation-request.json"
            ).read_bytes()
        )
    )
    request["sources"] = sorted(normalized, key=lambda item: item["source"]["id"])
    path = workspace / "request.json"
    write_json(path, request)
    session_path = workspace / "session.json"
    session = write_session(session_path, config)
    session.update(
        request_scope=local_scope(publication="never-exportable"),
        source_grants=[item["source"] for item in request["sources"]],
    )
    session["projections"].append("source-evidence")
    session["budgets"]["max_context_bytes"] = 262144
    write_json(session_path, bind_session_revisions(config, session))
    return {
        **fixture,
        "session_path": session_path,
        "context": QueryContext.load(config, session_path),
        "request": request,
        "request_path": path,
    }


def run_demo(workspace):
    report = run_packet_demo(workspace, fixture_factory=captured_fixture)
    report["schema"] = "mindgarden.synthetic-drive-consultation-proof/v1"
    report["google"] = "synthetic-provider-only; no real account"
    report["capture"] = {
        "api": "Drive v3 fixture",
        "snapshots": 2,
        "provider_reads": 4,
        "unchanged_evidence_reused": 8,
        "old_snapshot": "retained",
        "capture_execution": "controlled-import",
        "garden_execution": "offline",
        "native_export_smoke": "not performed",
        "oauth_setup": "not performed",
    }
    return report


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
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
    encoded = canonical_json(run_demo(args.workspace))
    if (
        args.check_golden
        and encoded
        != (ROOT / "tests/fixtures/consultation/expected-drive-proof.json").read_bytes()
    ):
        raise AssertionError(
            "Complete synthetic Drive proof differs from its committed golden"
        )
    if args.report:
        with args.report.open("xb") as output:
            output.write(encoded)
    print(encoded.decode(), end="")


if __name__ == "__main__":
    main()
