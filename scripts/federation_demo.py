#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Reproduce the bounded synthetic public-discovery checkpoint without integrations."""

from argparse import ArgumentParser
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request
from unittest.mock import patch

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
    import mindgarden

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.interfaces.cli import main as mindgarden_main


def cli_json(arguments):
    with redirect_stdout(io.StringIO()) as output:
        result = mindgarden_main(arguments)
    if result != 0:
        raise AssertionError("Synthetic federation command failed")
    return json.loads(output.getvalue())


def workflow(workspace: Path) -> dict:
    # Only fixture authoring is imported from tests; the selected engine remains
    # the installed package under -I, or this exact checkout under -S.
    sys.path.insert(0, str(REPOSITORY_ROOT))
    from tests.federation_fixture import FEDERATION_FIXTURES, create_fixture

    workspace = workspace.absolute()
    if any(path.is_symlink() for path in (workspace, *workspace.parents)) or (workspace.exists() and any(workspace.iterdir())):
        raise ValueError("Synthetic demo requires a new or empty ordinary workspace")
    workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
    fixtures = [create_fixture(workspace / "repository", "repository-garden"),
                create_fixture(workspace / "organization", "organization-garden")]
    expected = {path.name: path.read_bytes() for path in (FEDERATION_FIXTURES / "expected").iterdir()}
    before = [garden_fingerprint(fixture["workspace"]) for fixture in fixtures]
    request = {"schema": "mindgarden.federation-catalog-request/v1", "bundles": []}
    descriptors = []
    for fixture in fixtures:
        command = ["federation", "build", "--local-config", str(fixture["configuration"]),
                   "--scope", str(fixture["session_path"]), "--profile", str(fixture["profile_path"]),
                   "--output-directory", str(fixture["export"])]
        plan = cli_json([*command, "--plan"])
        assert list(fixture["export"].iterdir()) == []
        descriptor = cli_json([*command, "--apply", "--plan-digest", plan["plan_sha256"]])
        assert cli_json([*command, "--check"]) == descriptor
        assert cli_json([*command, "--apply", "--plan-digest", plan["plan_sha256"]]) == descriptor
        descriptors.append(descriptor)
        directory = fixture["export"] / fixture["profile"]["output_root"]
        if descriptor["garden"] == "repository-garden":
            assert {path.name: path.read_bytes() for path in directory.iterdir()} == expected
        request["bundles"].append({"directory": str(directory), "expected_revision": descriptor["revision"]})
    request_path = workspace / "catalog-request.json"
    request_path.write_bytes(canonical_json(request))
    catalog = cli_json(["federation", "catalog", "--input", str(request_path)])
    assert catalog["status"] == "complete" and len(catalog["gardens"]) == 2 and len(catalog["records"]) == 6
    first = fixtures[0]
    shared = ["--repository-root", str(first["workspace"]), "--local-config", str(first["configuration"]),
              "--scope", str(first["session_path"])]
    search = cli_json(["search", *shared, "--query", "evidence", "--limit", "3"])
    prompt = next(item for item in search["results"] if item["reference"]["id"] == "reviewed-prompt")
    assert any(record["reference"] == prompt["reference"] for record in catalog["records"])
    context = cli_json(["context", *shared, "--pack", "default", "--format", "json"])
    included = next(item for item in context["included"] if item["reference"] == prompt["reference"])
    assert included["sources"] == first["evidence"] and context["scope"]["visibility"] == "public"
    assert len(canonical_json(context)) <= context["budget"]["max_bytes"]
    relocated = workspace / "relocated-public-bundle"
    shutil.copytree(request["bundles"][0]["directory"], relocated)
    request["bundles"][0]["directory"] = str(relocated)
    request["bundles"].reverse()
    request_path.write_bytes(canonical_json(request))
    assert cli_json(["federation", "catalog", "--input", str(request_path)]) == catalog
    clean = create_fixture(workspace / "clean-rebuild", "repository-garden")
    assert clean["bundle"].files == expected
    assert [garden_fingerprint(fixture["workspace"]) for fixture in fixtures] == before
    public = b"".join(expected.values()) + canonical_json(catalog)
    for canary in json.loads((FEDERATION_FIXTURES / "negative-cases.json").read_text())["canaries"]:
        assert canary.encode() not in public
    assert str(workspace).encode() not in public
    return {"schema": "mindgarden.synthetic-federation-proof/v1", "status": "passed",
            "engine_version": mindgarden.__version__,
            "integrations": {"network": "blocked-in-process", "google": "unused", "model": "unused"},
            "descriptors": [{"garden": descriptor["garden"], "revision": descriptor["revision"]}
                            for descriptor in sorted(descriptors, key=lambda descriptor: descriptor["garden"])],
            "source_reference": fixtures[0]["evidence"][0],
            "catalog_sha256": digest_bytes(canonical_json(catalog)), "public_gardens": 2, "public_records": 6,
            "search_reference": prompt["reference"], "context_sha256": digest_bytes(canonical_json(context)),
            "context_bytes": len(canonical_json(context)), "context_max_bytes": context["budget"]["max_bytes"],
            "artifacts": [{"path": name, "sha256": digest_bytes(content)} for name, content in sorted(expected.items())],
            "checks": ["explicit-reviewed-profile-and-public-session", "read-only-plan", "digest-bound-create-and-repeat-verify",
                       "exact-source-reference", "typed-public-graph", "no-control-or-denied-metadata", "order-independent-catalog",
                       "catalog-to-scoped-search-and-bounded-context",
                       "relocated-export-same-references", "clean-garden-rebuild", "canonical-inputs-unchanged"]}


def run_demo(workspace: Path) -> dict:
    with patch.dict(os.environ, {}, clear=True), patch("socket.socket", side_effect=AssertionError("Network attempted")), \
            patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")), \
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
    if arguments.require_installed and (engine.is_relative_to(REPOSITORY_ROOT / "src")
                                       or not engine.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("This proof requires an installed engine in the current interpreter's prefix")
    report = run_demo(arguments.workspace)
    if arguments.report:
        with arguments.report.open("xb") as stream:
            stream.write(canonical_json(report))
    print(canonical_json(report).decode(), end="")


if __name__ == "__main__":
    main()
