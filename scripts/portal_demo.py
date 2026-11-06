#!/usr/bin/env python3
"""Prove deterministic local portal composition with synthetic public surfaces."""

from argparse import ArgumentParser
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

from mindgarden.application.portal import build_portal
from mindgarden.domain.contracts import canonical_json, digest_bytes


def run_demo(workspace):
    sys.path.insert(0, str(ROOT))
    from tests.portal_fixture import create_portal_fixture

    if any(path.is_symlink() for path in (workspace, *workspace.parents)) or (workspace.exists() and any(workspace.iterdir())):
        raise ValueError("Synthetic proof requires a new or empty ordinary workspace")
    with patch.dict(os.environ, {}, clear=True), patch("socket.socket", side_effect=AssertionError("Network attempted")):
        fixture = create_portal_fixture(workspace)
        def siblings():
            return {path.relative_to(fixture["portal"]).as_posix(): digest_bytes(path.read_bytes())
                    for surface in ("intelligence", "decisions", "history")
                    for path in (fixture["portal"] / surface).rglob("*") if path.is_file()}
        before = siblings()
        composition = build_portal(fixture["request"]); plan = composition.plan()
        assert not (fixture["portal"] / "garden").exists()
        assert composition.apply(plan["plan_sha256"])
        assert not composition.apply(plan["plan_sha256"])
        assert composition.verify() == composition.manifest
        assert siblings() == before
        return {"schema": "mindgarden.synthetic-portal-proof/v1", "status": "passed", "manifest": composition.manifest,
                "siblings": before, "renderer": "authored-contract-fixture-no-renderer-invocation",
                "checks": ["read-only-plan", "exact-source-manifest-pin", "owned-garden-only", "siblings-unchanged",
                           "idempotent-repeat", "final-receipt-required"], "deployment": "not-invoked"}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    if arguments.require_source and not engine.is_relative_to(ROOT / "src"):
        parser.error("Source engine from this checkout is required")
    if arguments.require_installed and (engine.is_relative_to(ROOT / "src") or not engine.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("An installed engine in this interpreter prefix is required")
    report = run_demo(arguments.workspace.absolute())
    if arguments.report:
        with arguments.report.open("xb") as stream: stream.write(canonical_json(report))
    print(canonical_json(report).decode(), end="")


if __name__ == "__main__":
    main()
