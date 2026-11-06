#!/usr/bin/env python3
"""Prove archive/PDF/media review and retained-original recovery without services."""

from argparse import ArgumentParser
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

REPOSITORY = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(REPOSITORY / "src"))
    import mindgarden

from mindgarden.application.assets import RETAIN
from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.documents import build_document_plan
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.storage import content_resolver, open_vault
from mindgarden.application.vault_recovery import build_vault_recovery_plan
from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object, safe_path
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.scope import local_scope
from mindgarden.interfaces.cli import main as cli_main

TIME = "2026-11-04T00:00:00Z"
FIXTURES = REPOSITORY / "tests/fixtures"


def cli(arguments):
    with redirect_stdout(io.StringIO()) as output:
        status = cli_main(arguments)
    assert status == 0, "Synthetic mixed-vault command failed"
    content = output.getvalue()
    return json.loads(content) if content.lstrip().startswith("{") else content


def apply(arguments):
    preview = cli([*arguments, "--plan"])
    return cli([*arguments, "--apply", "--plan-digest", preview["plan_sha256"]])


def write(path, document):
    path.write_bytes(canonical_json(document)); path.chmod(0o600)


def evidence(config, session, citation):
    source = citation["source"]
    return cli(["evidence", "--local-config", str(config), "--scope", str(session),
                "--garden-id", source["garden"], "--source-id", source["id"], "--revision", source["revision"],
                "--locator", citation["locator"], "--content-sha256", citation["content_sha256"]])


def scope(config, path, *, assets=False):
    arguments = ["scope", "--local-config", str(config), "--session-id", "synthetic-assets" if assets else "synthetic-mixed-knowledge",
                 "--readable-garden", "synthetic-garden", "--writable-garden", "synthetic-garden", "--allowed-visibility", "personal",
                 "--expires-at", "2099-01-01T00:00:00Z", "--output", str(path)]
    if assets: arguments += ["--projection", "assets", "--allowed-review-state", "approved", "--allowed-review-state", "unreviewed"]
    cli(arguments)


class RecordedSyntheticPDF:
    """An explicit test port, not a claim that the host has PDF tools."""
    source_checks = []

    def read(self, captured):
        assert digest_bytes(captured) == digest_bytes((FIXTURES / "documents/complete.pdf").read_bytes())
        return read_object(FIXTURES / "documents/layout.json")


def workflow(workspace, tool_directory):
    workspace = workspace.absolute()
    if workspace.exists() and any(workspace.iterdir()): raise ValueError("Supply a new empty synthetic workspace")
    workspace.mkdir(parents=True, exist_ok=True, mode=0o700); workspace.chmod(0o700)
    # Load only the fixture/proof helper explicitly, never another engine checkout.
    spec = importlib.util.spec_from_file_location("synthetic_private_proof", REPOSITORY / "scripts/private_garden_demo.py")
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    baseline = helper.run_demo(workspace / "archive")
    assert baseline == read_object(FIXTURES / "conversation-archives/expected-proof.json")
    garden = workspace / "archive/garden"; config = workspace / "archive/bindings.json"
    bindings = LocalBindings.load(config)
    pdf = FIXTURES / "documents/complete.pdf"; review_path = workspace / "pdf-classification.json"
    write(review_path, {"schema": "mindgarden.document-classification/v1", "kind": "initial-classification",
        "source_sha256": digest_bytes(pdf.read_bytes()), "scope": local_scope(), "authority": {"kind": "human", "id": "synthetic-owner"},
        "review": {"state": "approved", "reviewers": ["synthetic-owner"], "reviewed_at": TIME,
                   "rationale": "New wholly synthetic ordinary fixture."}})
    metadata = {"source_id": "synthetic-pdf", "title": "Synthetic document", "origin": "urn:synthetic:pdf", "owner": "synthetic-owner",
                "rights": "Wholly synthetic fixture.", "captured_at": TIME}
    plan = build_document_plan(bindings, "synthetic-garden", "synthetic-vault", pdf, metadata, review_path,
        tool_directory=tool_directory, reader=None if tool_directory else RecordedSyntheticPDF())
    assert apply_ingestion(plan, plan.digest, bindings, "synthetic-vault")
    for filename, media_type in (("synthetic.png", "image/png"), ("synthetic.wav", "audio/wav")):
        arguments = ["ingest", "--repository-root", str(garden), "--local-config", str(config), "--vault-id", "synthetic-vault",
                     "--input", str(FIXTURES / "assets" / filename), "--source-id", "source-" + filename.replace(".", "-"),
                     "--title", "Synthetic opaque media", "--origin", "urn:synthetic:" + filename, "--captured", TIME,
                     "--owner", "synthetic-owner", "--rights", "Wholly synthetic fixture.", "--media-type", media_type]
        assert apply(arguments)["applied"] is True
        assert apply(arguments)["applied"] is False
    alias = workspace / "renamed-synthetic.png"; alias.write_bytes((FIXTURES / "assets/synthetic.png").read_bytes())
    assert apply(["ingest", "--repository-root", str(garden), "--local-config", str(config), "--vault-id", "synthetic-vault",
        "--input", str(alias), "--source-id", "synthetic-image-alias", "--title", "Synthetic alias", "--origin", "urn:synthetic:alias",
        "--captured", TIME, "--owner", "synthetic-owner", "--rights", "Wholly synthetic fixture.", "--media-type", "image/png"])["applied"] is True
    proposal = FIXTURES / "assets/pdf-curation-plan.json"
    preview = cli(["gardenize", "--local-config", str(config), "--plan", str(proposal)])
    assert cli(["gardenize", "--local-config", str(config), "--apply", str(proposal), "--plan-digest", preview["plan_sha256"]])["applied"] is True
    asset_session = workspace / "assets-before-review.json"; scope(config, asset_session, assets=True)
    inventory = cli(["asset", "inventory", "--local-config", str(config), "--scope", str(asset_session)])
    assert len(inventory["assets"]) == 4
    png = next(item for item in inventory["assets"] if item["media_types"] == ["image/png"])
    assert len(png["sources"]) == 2
    original_vault = open_vault(LocalBindings.load(config), "synthetic-vault"); before_bundle = original_vault.export_bundle()
    for media_type, state in (("image/png", "keep"), ("audio/wav", "discard-proposed")):
        asset = next(item for item in inventory["assets"] if item["media_types"] == [media_type])
        request = workspace / (state + ".json")
        write(request, {"schema": "mindgarden.asset-review-request/v1", "id": "synthetic-" + state,
            "source": asset["sources"][0], "state": state, "previous": None, "copy_policy": "reference-only", "retention": RETAIN,
            "authority": {"kind": "human", "id": "synthetic-owner"}, "review": {"state": "approved", "reviewers": ["synthetic-owner"],
            "reviewed_at": TIME, "rationale": "Synthetic metadata-only triage; preserve every original."}})
        assert apply(["asset", "review", "--local-config", str(config), "--garden-id", "synthetic-garden", "--input", str(request)])["applied"] is True
    assert original_vault.export_bundle() == before_bundle
    asset_session = workspace / "assets-session.json"; scope(config, asset_session, assets=True)
    inventory = cli(["asset", "inventory", "--local-config", str(config), "--scope", str(asset_session)])
    assert {item["state"] for item in inventory["assets"]} == {"unreviewed", "keep", "discard-proposed"}
    session = workspace / "knowledge-session.json"; scope(config, session)
    shared = ["--repository-root", str(garden), "--local-config", str(config), "--scope", str(session)]
    search = cli(["search", *shared, "--query", "evidence"])
    entries = {entry["reference"]["id"]: entry for entry in search["results"]}
    assert {"reviewed-prompt", "reviewed-pdf-prompt"} <= entries.keys()
    citations = {identity: entries[identity]["sources"][0] for identity in sorted(entries)}
    assert citations["reviewed-prompt"] == baseline["source_reference"]
    resolved = {identity: evidence(config, session, citation) for identity, citation in citations.items()}
    assert resolved["reviewed-pdf-prompt"]["origin"]["original_selector"]["page"] == 1
    index = cli(["index", *shared, "--write"])
    context = cli(["context", *shared, "--pack", "default", "--format", "json"])
    markdown_arguments = ["context", *shared, "--pack", "default", "--format", "markdown"]
    with redirect_stdout(io.StringIO()) as output: assert cli_main(markdown_arguments) == 0
    assert len(output.getvalue().encode()) <= context["budget"]["max_bytes"]
    assert "reviewed-prompt" in json.dumps(context) and "reviewed-pdf-prompt" in json.dumps(context)
    fingerprint = garden_fingerprint(garden); bindings = LocalBindings.load(config)
    backup = workspace / "mixed-backup.zip"
    export = build_vault_recovery_plan(bindings, "synthetic-vault", "export", backup); assert export.apply(export.digest)
    relocated = workspace / "mixed-relocated-vault"
    relocation = build_vault_recovery_plan(bindings, "synthetic-vault", "relocate", relocated)
    with patch("mindgarden.application.vault_recovery.replace_bindings", side_effect=OSError("Synthetic rebind interruption")):
        try: relocation.apply(relocation.digest)
        except OSError: pass
        else: raise AssertionError("Synthetic fault was not exercised")
    assert original_vault.export_bundle() == before_bundle
    assert relocation.apply(relocation.digest) is True
    assert relocation.apply(relocation.digest) is False
    assert {identity: evidence(config, session, citation) for identity, citation in citations.items()} == resolved
    assert garden_fingerprint(garden) == fingerprint
    restore_root = workspace / "mixed-restored-vault"
    restore = build_vault_recovery_plan(LocalBindings.load(config), "synthetic-vault", "restore", restore_root, input_path=backup)
    assert restore.apply(restore.digest); assert restore.apply(restore.digest) is False
    clean = workspace / "clean-garden"; clean.mkdir(mode=0o700); shutil.copytree(garden / ".garden", clean / ".garden")
    for root in read_object(clean / ".garden/garden.json")["roots"]["generated"]:
        path = safe_path(clean / ".garden", root)
        if path.exists(): shutil.rmtree(path)
    clean_config = workspace / "clean-bindings.json"; document = read_object(config)
    document["gardens"][0]["root"] = str(clean); document["vaults"][0]["root"] = str(restore_root); write(clean_config, document)
    clean_shared = ["--repository-root", str(clean), "--local-config", str(clean_config), "--scope", str(session)]
    assert cli(["index", *clean_shared, "--write"]) == index
    assert cli(["context", *clean_shared, "--pack", "default", "--format", "json"]) == context
    assert cli(["asset", "inventory", "--local-config", str(clean_config), "--scope", str(asset_session)]) == inventory
    assert {identity: evidence(clean_config, session, citation) for identity, citation in citations.items()} == resolved
    clean_bindings = LocalBindings.load(clean_config)
    audit = cli(["vault", "audit", "--local-config", str(clean_config), "--vault-id", "synthetic-vault"])
    assert audit["status"] == "verified"; inspect_garden(clean, content_resolver=content_resolver(clean_bindings)).require_valid()
    for path in (clean / ".garden").rglob("*.json"): assert str(workspace).encode() not in path.read_bytes()
    assert original_vault.export_bundle() == before_bundle
    return {"schema": "mindgarden.mixed-vault-proof/v1", "status": "passed",
        "pdf_reader_mode": "real-local-poppler" if tool_directory else "recorded-synthetic-reader-port",
        "network": "blocked-in-process", "google": "unused", "model": "unused", "assets": len(inventory["assets"]),
        "asset_states": {item["content_id"]: item["state"] for item in inventory["assets"]}, "source_references": citations,
        "index_sha256": digest_bytes(canonical_json(index)), "context_sha256": digest_bytes(canonical_json(context)),
        "context_bytes": len(canonical_json(context)), "context_max_bytes": context["budget"]["max_bytes"],
        "inventory_sha256": digest_bytes(canonical_json(inventory)), "backup_sha256": digest_bytes(backup.read_bytes()),
        "vault_objects": len(audit["objects"]), "originals": "retained", "rebind_interruption": "exact-retry-recovered",
        "restore": "clean-location-verified", "projections": "rebuilt-with-identical-index-context-inventory",
        "restricted_runtime": "unavailable", "destructive_gc": "unavailable"}


def main():
    parser = ArgumentParser(description=__doc__); parser.add_argument("--workspace", type=Path, required=True)
    reader = parser.add_mutually_exclusive_group(required=True)
    reader.add_argument("--tool-directory", type=Path); reader.add_argument("--recorded-synthetic-pdf", action="store_true")
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group(); mode.add_argument("--require-source", action="store_true"); mode.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args(); engine = Path(mindgarden.__file__).resolve()
    if arguments.require_source and not engine.is_relative_to(REPOSITORY / "src"): parser.error("Exact source engine required")
    if arguments.require_installed and (engine.is_relative_to(REPOSITORY / "src") or not engine.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("Isolated installed engine required")
    with patch.dict(os.environ, {}, clear=True), patch("socket.socket", side_effect=AssertionError("Network attempted")), \
            patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")):
        report = workflow(arguments.workspace, arguments.tool_directory)
    expected = read_object(FIXTURES / "assets/expected-proof.json")
    comparison = {**report, "pdf_reader_mode": "recorded-synthetic-reader-port"}
    assert comparison == expected, "Mixed-vault golden differs"
    content = canonical_json(report)
    if arguments.report:
        with arguments.report.open("xb") as output: output.write(content)
    print(content.decode(), end="")


if __name__ == "__main__": main()
