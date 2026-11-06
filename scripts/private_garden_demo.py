#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Reproduce the finite synthetic private-garden milestone without integrations."""

from argparse import ArgumentParser
from contextlib import redirect_stdout
import importlib.util
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

from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.storage import content_resolver, open_vault
from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object, safe_path
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.scope import local_scope
from mindgarden.interfaces.cli import main as mindgarden_main

TIME = "2026-11-04T00:00:00Z"


def cli(arguments):
    with redirect_stdout(io.StringIO()) as output:
        result = mindgarden_main(arguments)
    if result != 0:
        raise AssertionError("Synthetic command failed: " + arguments[0])
    return output.getvalue()


def cli_json(arguments):
    return json.loads(cli(arguments))


def reviewed_apply(arguments):
    plan = cli_json(arguments + ["--plan"])
    return cli_json(arguments + ["--apply", "--plan-digest", plan["plan_sha256"]])


def write_json(path, value):
    path.write_bytes(canonical_json(value))
    path.chmod(0o600)


def synthetic_archive():
    # This helper packages committed synthetic members; it contains no engine
    # behavior. An installed-engine run never adds source modules to sys.path.
    location = REPOSITORY_ROOT / "tests/archive_fixture.py"
    spec = importlib.util.spec_from_file_location("synthetic_archive_fixture", location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.package_bytes(module.package_members())


def workflow(workspace: Path) -> dict:
    workspace = workspace.absolute()
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError("Synthetic demo requires a new or empty workspace")
    workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
    workspace.chmod(0o700)
    garden = workspace / "garden"; garden.mkdir(mode=0o700)
    bindings_path = workspace / "bindings.json"
    session_path = workspace / "session.json"
    source_vault = workspace / "source-vault"
    initialization = ["init", "--repository-root", str(garden), "--visibility", "private", "--kind", "personal",
                      "--garden-id", "synthetic-garden", "--title", "Synthetic private garden", "--owner", "synthetic-owner",
                      "--canonical-uri", "urn:mindgarden:garden:synthetic-garden", "--domain", "knowledge-systems", "--topic", "prompt-bank"]
    plan = cli_json(initialization)
    cli(initialization + ["--apply", "--plan-digest", plan["plan_sha256"]])
    write_json(bindings_path, {"schema": "mindgarden.local-bindings/v1", "gardens": [{"id": "synthetic-garden",
        "root": str(garden), "scope": local_scope()}], "vaults": [{"id": "synthetic-vault", "adapter": "filesystem",
        "root": str(source_vault)}], "revoked_sessions": []})
    reviewed_apply(["vault", "init", "--local-config", str(bindings_path), "--vault-id", "synthetic-vault"])
    archive = workspace / "synthetic-archive.zip"; archive.write_bytes(synthetic_archive()); archive.chmod(0o600)
    ingest = ["ingest", "--repository-root", str(garden), "--local-config", str(bindings_path), "--vault-id", "synthetic-vault",
              "--input", str(archive), "--source-id", "synthetic-archive", "--title", "Synthetic conversation archive",
              "--origin", "urn:synthetic:conversation", "--captured", TIME, "--owner", "synthetic-owner",
              "--rights", "Authored synthetic fixtures only.", "--media-type", "application/zip",
              "--adapter", "conversation-archive", "--manifest-version", "3.2.3"]
    imported = reviewed_apply(ingest)
    assert imported["applied"] is True
    assert reviewed_apply(ingest)["applied"] is False
    proposal = REPOSITORY_ROOT / "tests/fixtures/conversation-archives/authored-plan.json"
    preview = cli_json(["gardenize", "--local-config", str(bindings_path), "--plan", str(proposal)])
    curated = cli_json(["gardenize", "--local-config", str(bindings_path), "--apply", str(proposal),
                        "--plan-digest", preview["plan_sha256"]])
    assert curated["applied"] is True
    cli_json(["scope", "--local-config", str(bindings_path), "--session-id", "synthetic-session",
              "--readable-garden", "synthetic-garden", "--writable-garden", "synthetic-garden",
              "--allowed-visibility", "personal", "--expires-at", "2099-01-01T00:00:00Z", "--output", str(session_path)])
    shared = ["--repository-root", str(garden), "--local-config", str(bindings_path), "--scope", str(session_path)]
    validation = cli_json(["validate", "--repository-root", str(garden), "--local-config", str(bindings_path), "--format", "json"])
    assert validation["status"] == "valid"
    search = cli_json(["search", *shared, "--query", "evidence"])
    entry = search["results"][0]
    assert entry["reference"]["id"] == "reviewed-prompt" and entry["review"]["state"] == "approved"
    citation = entry["sources"][0]
    evidence_arguments = ["evidence", "--scope", str(session_path), "--garden-id", citation["source"]["garden"],
                          "--source-id", citation["source"]["id"], "--revision", citation["source"]["revision"],
                          "--locator", citation["locator"], "--content-sha256", citation["content_sha256"]]
    evidence = cli_json([*evidence_arguments, "--local-config", str(bindings_path)])
    assert evidence["text"] == "Cite exact evidence; preserve uncertainty."
    assert evidence["origin"]["speaker"] == "assistant"
    assert evidence["origin"]["original_selector"]["json_pointer"] == "/messages/1"
    assert evidence["source_review"]["state"] == "unreviewed"
    index = cli_json(["index", *shared, "--write"])
    cli_json(["index", *shared, "--check"])
    context = cli_json(["context", *shared, "--pack", "default", "--format", "json"])
    context_markdown = cli(["context", *shared, "--pack", "default", "--format", "markdown"])
    assert context["included"][0]["sources"] == entry["sources"]
    assert len(canonical_json(context)) <= context["budget"]["max_bytes"]
    assert len(context_markdown.encode()) <= context["budget"]["max_bytes"]
    assert "synthetic-malicious-command" not in context_markdown
    assert cli_json(["verify", *shared])["status"] == "verified"
    before = garden_fingerprint(garden)
    bindings = LocalBindings.load(bindings_path)
    original_vault = open_vault(bindings, "synthetic-vault")
    original_bundle = original_vault.export_bundle()
    original_archive = archive.read_bytes()
    backup = workspace / "vault-backup.zip"
    reviewed_apply(["vault", "export", "--local-config", str(bindings_path), "--vault-id", "synthetic-vault", "--output", str(backup)])
    assert backup.read_bytes() == original_bundle
    relocated = workspace / "relocated-vault"
    reviewed_apply(["vault", "relocate", "--local-config", str(bindings_path), "--vault-id", "synthetic-vault", "--destination", str(relocated)])
    assert source_vault.is_dir() and original_vault.export_bundle() == original_bundle
    assert cli_json([*evidence_arguments, "--local-config", str(bindings_path)]) == evidence
    relocated_index = cli_json(["index", *shared])
    assert canonical_json(relocated_index) == canonical_json(index)
    assert before == garden_fingerprint(garden)
    restored = workspace / "restored-vault"
    reviewed_apply(["vault", "restore", "--local-config", str(bindings_path), "--vault-id", "synthetic-vault",
                    "--input", str(backup), "--destination", str(restored)])
    clean_garden = workspace / "clean-garden"; clean_garden.mkdir(mode=0o700)
    shutil.copytree(garden / ".garden", clean_garden / ".garden")
    manifest = read_object(clean_garden / ".garden/garden.json")
    for generated in manifest["roots"]["generated"]:
        path = safe_path(clean_garden / ".garden", generated)
        if path.exists():
            shutil.rmtree(path)
    clean_bindings_path = workspace / "clean-bindings.json"
    clean_bindings = read_object(bindings_path)
    clean_bindings["gardens"][0]["root"] = str(clean_garden)
    clean_bindings["vaults"][0]["root"] = str(restored)
    write_json(clean_bindings_path, clean_bindings)
    clean_shared = ["--repository-root", str(clean_garden), "--local-config", str(clean_bindings_path), "--scope", str(session_path)]
    rebuilt = cli_json(["index", *clean_shared, "--write"])
    assert canonical_json(rebuilt) == canonical_json(index)
    assert cli_json([*evidence_arguments, "--local-config", str(clean_bindings_path)]) == evidence
    assert cli_json(["context", *clean_shared, "--pack", "default", "--format", "json"]) == context
    assert cli_json(["verify", *clean_shared])["status"] == "verified"
    audit = cli_json(["vault", "audit", "--local-config", str(clean_bindings_path), "--vault-id", "synthetic-vault"])
    assert audit["status"] == "verified"
    inspect_garden(clean_garden, content_resolver=content_resolver(LocalBindings.load(clean_bindings_path))).require_valid()
    assert archive.read_bytes() == original_archive
    for record in (clean_garden / ".garden").rglob("*.json"):
        assert str(workspace).encode() not in record.read_bytes()
    return {"schema": "mindgarden.synthetic-workflow-proof/v1", "engine_version": mindgarden.__version__,
            "status": "passed", "integrations": {"network": "blocked-in-process", "google": "unused", "model": "unused"},
            "archive_spec_version": "3.2.3", "archive_profile": "full-source", "archive_sha256": digest_bytes(original_archive),
            "knowledge": {"id": "reviewed-prompt", "review": "approved", "topic": "prompt-bank",
                          "epistemic_state": entry["qualifications"]["epistemic_state"]},
            "source_reference": citation, "original_selector": evidence["origin"]["original_selector"],
            "speaker": evidence["origin"]["speaker"], "source_review": evidence["source_review"]["state"],
            "index_sha256": digest_bytes(canonical_json(index)), "context_sha256": digest_bytes(canonical_json(context)),
            "context_bytes": len(canonical_json(context)), "context_max_bytes": context["budget"]["max_bytes"],
            "vault_backup_sha256": digest_bytes(original_bundle), "vault_objects": len(audit["objects"]),
            "checks": ["private-init-and-general-validation", "archive-original-preserved", "repeat-import-no-duplicates",
                       "authored-human-review", "exact-source-search-and-evidence", "bounded-json-and-markdown-context",
                       "deterministic-index", "vault-export", "relocation-same-reference", "restore-clean-vault",
                       "rebuild-clean-garden-without-caches", "original-vault-retained", "no-physical-paths-in-records"]}


def run_demo(workspace: Path) -> dict:
    with patch.dict(os.environ, {}, clear=True), patch("socket.socket", side_effect=AssertionError("Network attempted")), \
            patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")), \
            patch("subprocess.run", side_effect=AssertionError("External process attempted")):
        return workflow(workspace)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="New or empty private synthetic workspace")
    parser.add_argument("--report", type=Path, help="Write the public-safe synthetic JSON report")
    engine = parser.add_mutually_exclusive_group()
    engine.add_argument("--require-installed", action="store_true", help="Require the engine inside the current interpreter's installation prefix")
    engine.add_argument("--require-source", action="store_true", help="Require the engine from this exact source checkout")
    arguments = parser.parse_args()
    engine_path = Path(mindgarden.__file__).resolve()
    if arguments.require_installed and (engine_path.is_relative_to(REPOSITORY_ROOT / "src")
                                       or not engine_path.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("This verification requires an installed engine in a clean environment")
    if arguments.require_source and not engine_path.is_relative_to(REPOSITORY_ROOT / "src"):
        parser.error("This verification requires the engine from this exact source checkout")
    report = run_demo(arguments.workspace)
    if report != read_object(REPOSITORY_ROOT / "tests/fixtures/conversation-archives/expected-proof.json"):
        raise AssertionError("Synthetic private-workflow golden differs")
    if arguments.report:
        with arguments.report.open("xb") as output:
            output.write(canonical_json(report))
    print(canonical_json(report).decode(), end="")


if __name__ == "__main__":
    main()
