#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Prove non-destructive synthetic registry management through the ordinary CLI."""

from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import urllib.request
from unittest.mock import patch

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
    import mindgarden

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.adapters.registry_files import create_control
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.interfaces.cli import main as mindgarden_main


def cli_json(arguments, *, expected_status=0):
    with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
        result = mindgarden_main(arguments)
    if result != expected_status:
        raise AssertionError("Synthetic registry command returned an unexpected status")
    if expected_status:
        return errors.getvalue()
    return json.loads(output.getvalue())


def workflow(workspace: Path, control: Path) -> dict:
    # Only synthetic authoring helpers come from tests. Under -I the engine
    # remains the installed wheel, rather than being replaced with checkout src.
    sys.path.insert(0, str(REPOSITORY_ROOT))
    from tests.federation_fixture import FEDERATION_FIXTURES
    from tests.registry_fixture import create_roots

    workspace = workspace.absolute()
    if any(path.is_symlink() for path in (workspace, *workspace.parents)) or (workspace.exists() and any(workspace.iterdir())):
        raise ValueError("Synthetic demo requires a new or empty ordinary workspace")
    workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
    fixture = create_roots(workspace / "gardens")
    roots = [Path(binding["root"]) for binding in fixture["bindings"]]
    before = [garden_fingerprint(root) for root in roots]
    vault_before = {path.name: path.read_bytes() for path in fixture["vault_root"].iterdir()}
    registry = control / "registry.json"
    create_control(registry, canonical_json({"schema": "mindgarden.local-bindings/v1", "gardens": [],
                                            "vaults": fixture["vaults"], "revoked_sessions": []}))
    sequence = 0

    def mutate(operation, arguments):
        nonlocal sequence
        sequence += 1
        plan_path = control / "plans" / (str(sequence) + ".json")
        previous = registry.read_bytes() if registry.exists() else None
        plan = cli_json(["registry", operation, "--registry", str(registry), "--plan", "--output", str(plan_path), *arguments])
        assert (registry.read_bytes() if registry.exists() else None) == previous
        assert plan_path.read_bytes() == canonical_json(plan)
        apply = ["registry", "apply", "--registry", str(registry), "--plan", str(plan_path), "--plan-digest", plan["plan_sha256"]]
        result = cli_json(apply)
        assert result["applied"] == (plan["before_sha256"] != plan["after_sha256"])
        assert cli_json(apply)["applied"] is False
        return plan

    mutate("init", [])
    for binding in fixture["bindings"]:
        arguments = ["--root", binding["root"], "--garden-id", binding["id"]]
        for name in ("visibility", "persistence", "execution", "publication"):
            arguments += ["--" + name, binding["scope"][name]]
        mutate("register", arguments)
    # Duplicate registration is a verified no-op across separate CLI calls.
    mutate("register", arguments)
    mutate("set-view", ["--view-id", "private-view-canary", "--garden", "repository-garden", "--garden", "personal-garden"])
    doctor = cli_json(["registry", "doctor", "--registry", str(registry)])
    assert doctor["status"] == "ready" and doctor["content_integrity"] == "not-checked"
    listing = cli_json(["registry", "list", "--registry", str(registry)])
    assert {entry["id"] for entry in listing["gardens"]} == {"repository-garden", "personal-garden"}
    inspection = cli_json(["registry", "inspect", "--registry", str(registry), "--garden-id", "personal-garden"])
    assert len(inspection["gardens"]) == 1 and "root" not in inspection["gardens"][0]
    assert listing["publication"] == "never-exportable"

    def session(name, *, public=False):
        path = control / (name + ".json")
        arguments = ["scope", "--local-config", str(registry), "--registry-view", "private-view-canary", "--session-id", name,
                     "--allowed-visibility", "public", "--expires-at", "2099-01-01T00:00:00Z", "--output", str(path),
                     "--request-visibility", "public" if public else "personal",
                     "--publication-authority", "publishable" if public else "never-exportable"]
        if public:
            arguments += ["--writable-garden", "repository-garden"]
        else:
            arguments += ["--allowed-visibility", "personal"]
        cli_json(arguments)
        return ["--local-config", str(registry), "--scope", str(path)]

    public_session = session("public-session", public=True)
    private_session = session("private-session")
    search = cli_json(["search", *public_session, "--query", "evidence"])
    private_search = cli_json(["search", *private_session, "--query", "evidence"])
    assert {item["reference"]["garden"] for item in private_search["results"]} == {"repository-garden", "personal-garden"}
    prompt = next(item for item in search["results"] if item["reference"]["id"] == "reviewed-prompt")
    links = cli_json(["backlinks", *private_session, "--artifact", "repository-garden/reviewed-prompt"])
    assert any(item["from"] == "personal-garden/personal-prompt" for item in links["links"])
    assert cli_json(["backlinks", *public_session, "--artifact", "repository-garden/reviewed-prompt"])["links"] == []
    public = fixture["public"]
    context = cli_json(["context", *public_session, "--repository-root", str(public["workspace"]), "--pack", "default", "--format", "json"])
    included = next(item for item in context["included"] if item["reference"] == prompt["reference"])
    assert included["sources"] == public["evidence"]
    assert len(canonical_json(context)) <= context["budget"]["max_bytes"]
    private_context = cli_json(["context", *private_session, "--repository-root", str(fixture["personal_root"]),
                                "--pack", "default", "--format", "json"])
    assert private_context["scope"]["visibility"] == "personal"
    assert b"personal-content-canary" in canonical_json(private_context)
    assert len(canonical_json(private_context)) <= private_context["budget"]["max_bytes"]

    build = ["federation", "build", *public_session, "--profile", str(public["profile_path"]), "--output-directory", str(public["export"])]
    plan = cli_json([*build, "--plan"])
    descriptor = cli_json([*build, "--apply", "--plan-digest", plan["plan_sha256"]])
    directory = public["export"] / public["profile"]["output_root"]
    expected = {path.name: path.read_bytes() for path in (FEDERATION_FIXTURES / "expected").iterdir()}
    assert {path.name: path.read_bytes() for path in directory.iterdir()} == expected
    snapshot = digest_bytes(registry.read_bytes())
    mutate("unregister", ["--garden-id", "personal-garden"])
    diagnostic = cli_json(["search", *private_session, "--query", "evidence"], expected_status=3)
    assert "SESSION_VIEW_STALE" in diagnostic and str(workspace) not in diagnostic
    fresh_public = session("fresh-public-session", public=True)
    assert cli_json(["search", *fresh_public, "--query", "evidence"]) == search
    assert cli_json(["federation", "build", *fresh_public, "--profile", str(public["profile_path"]),
                     "--output-directory", str(public["export"]), "--check"]) == descriptor
    mutate("restore", ["--revision", snapshot])
    assert "SESSION_VIEW_STALE" in cli_json(["search", *private_session, "--query", "evidence"], expected_status=3)
    refreshed = session("refreshed-private-session")
    assert cli_json(["search", *refreshed, "--query", "evidence"]) == private_search
    assert [garden_fingerprint(root) for root in roots] == before
    assert {path.name: path.read_bytes() for path in fixture["vault_root"].iterdir()} == vault_before
    public_bytes = canonical_json(search) + canonical_json(context) + b"".join(expected.values())
    for canary in ("private-view-canary", "personal-content-canary", "personal-garden", "registry.json", str(workspace), str(control)):
        assert canary.encode() not in public_bytes
    capabilities = cli_json(["registry", "capabilities"])
    assert not capabilities["canonical_writes"] and not capabilities["restricted_registration"]
    return {"schema": "mindgarden.synthetic-registry-proof/v1", "status": "passed", "engine_version": mindgarden.__version__,
            "integrations": {"network": "blocked-in-process", "subprocess": "blocked-in-process", "google": "unused", "model": "unused"},
            "synthetic_registered_gardens": 2, "private_view_gardens": 2,
            "public_reference": prompt["reference"], "source_reference": public["evidence"][0],
            "context_sha256": digest_bytes(canonical_json(context)), "context_bytes": len(canonical_json(context)),
            "context_max_bytes": context["budget"]["max_bytes"], "public_bundle_revision": descriptor["revision"],
            "canonical_files_preserved": True,
            "checks": ["saved-read-only-plan-and-exact-digest-apply", "duplicate-registration-no-op", "manifest-only-doctor",
                       "private-union-with-explicit-session-grants", "private-to-public-reference-without-public-backlink",
                       "public-projection-matches-pre-registry-golden", "exact-evidence-and-bounded-context",
                       "unregister-preserves-gardens-and-vaults", "unregistered-session-fails-closed",
                       "private-membership-change-does-not-change-public-output", "owned-snapshot-restore-and-repeat-verify",
                       "restore-does-not-revive-old-view-session", "canonical-inputs-unchanged"]}


def run_demo(workspace: Path) -> dict:
    # Managed control data never enters even an ignored folder inside Git.
    with TemporaryDirectory(prefix="mindgarden-registry-proof-") as directory, patch.dict(os.environ, {}, clear=True), \
            patch("socket.socket", side_effect=AssertionError("Network attempted")), \
            patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")), \
            patch("subprocess.run", side_effect=AssertionError("External process attempted")):
        return workflow(workspace, Path(directory))


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
