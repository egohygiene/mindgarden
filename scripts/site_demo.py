#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Reproduce the reviewed v1 site-content checkpoint without renderer setup."""

from argparse import ArgumentParser
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
    import mindgarden

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.adapters.site_files import read_site
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.site import verify_site
from mindgarden.interfaces.cli import main as mindgarden_main


def cli_json(arguments):
    with redirect_stdout(io.StringIO()) as output:
        status = mindgarden_main(arguments)
    if status:
        raise AssertionError("Synthetic site command failed")
    return json.loads(output.getvalue())


def workflow(workspace):
    sys.path.insert(0, str(REPOSITORY_ROOT))
    from tests.site_fixture import create_fixture

    workspace = workspace.absolute()
    if any(path.is_symlink() for path in (workspace, *workspace.parents)) or (workspace.exists() and any(workspace.iterdir())):
        raise ValueError("Synthetic demo requires a new or empty ordinary workspace")
    fixture = create_fixture(workspace)
    before = garden_fingerprint(fixture["workspace"])
    arguments = ["--repository-root", str(fixture["workspace"]), "--profile", str(fixture["profile_path"]),
                 "--local-config", str(fixture["configuration"]), "--scope", str(fixture["session_path"]),
                 "--output-directory", str(fixture["export"])]
    plan = cli_json(["publish", "project", *arguments, "--plan"])
    assert list(fixture["export"].iterdir()) == []
    assert cli_json(["publish", "project", *arguments, "--apply", "--plan-digest", plan["plan_sha256"]])["applied"]
    assert not cli_json(["publish", "project", *arguments, "--apply", "--plan-digest", plan["plan_sha256"]])["applied"]
    manifest = cli_json(["publish", "verify", *arguments])
    files = read_site(fixture["export"] / "garden")
    assert verify_site(files) == manifest
    page = files["notes/reviewed-prompt/index.md"]
    assert fixture["evidence"][0]["source"]["revision"].encode() in page and b"lines:1-1" in page
    public = b"".join(files.values())
    for canary in ("hidden-garden-canary", "hidden-root-canary", "unreviewed-body-canary", "private-review-rationale-canary", str(workspace)):
        assert canary.encode() not in public
    assert garden_fingerprint(fixture["workspace"]) == before
    return {"schema": "mindgarden.synthetic-site-proof/v1", "status": "passed", "engine_version": mindgarden.__version__,
            "kind": "content", "renderer": {"adapter": "quartz-v5", "commit": fixture["profile"]["x-site"]["commit"]},
            "revision": manifest["revision"], "files": len(files), "routes": manifest["routes"],
            "source_reference": fixture["evidence"][0], "prompt_page_sha256": digest_bytes(page),
            "integrations": {"network": "blocked-in-process", "subprocess": "blocked-in-process", "model": "unused", "google": "unused"},
            "checks": ["explicit-reviewed-public-session-and-profile", "read-only-plan", "digest-bound-create-and-repeat-verify",
                       "selected-only-typed-links", "exact-source-evidence", "no-private-metadata-or-paths", "canonical-inputs-unchanged"]}


def run_demo(workspace):
    with patch.dict(os.environ, {}, clear=True), patch("socket.socket", side_effect=AssertionError("Network attempted")), \
            patch("subprocess.run", side_effect=AssertionError("External process attempted")):
        return workflow(workspace)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    if arguments.require_source and not engine.is_relative_to(REPOSITORY_ROOT / "src"):
        parser.error("This proof requires the engine from this exact source checkout")
    if arguments.require_installed and (engine.is_relative_to(REPOSITORY_ROOT / "src") or not engine.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("This proof requires an installed engine in the interpreter prefix")
    report = run_demo(arguments.workspace)
    if arguments.report:
        with arguments.report.open("xb") as stream:
            stream.write(canonical_json(report))
    print(canonical_json(report).decode(), end="")


if __name__ == "__main__":
    main()
