#!/usr/bin/env python3
"""Verify optional real local PDF tools against synthetic committed fixtures."""

from argparse import ArgumentParser
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

REPOSITORY = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(REPOSITORY / "src"))
    import mindgarden

from mindgarden.adapters.pdf_tools import LocalPDFReader
from mindgarden.application.bindings import LocalBindings
from mindgarden.application.storage import content_resolver, open_vault
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.scope import local_scope
from mindgarden.interfaces.cli import main as cli_main

TIME = "2026-11-04T00:00:00Z"


def cli(arguments):
    with redirect_stdout(io.StringIO()) as output:
        status = cli_main(arguments)
    assert status == 0, "Synthetic document command failed"
    content = output.getvalue()
    return json.loads(content) if content.lstrip().startswith("{") else content


def run(workspace, tool_directory):
    workspace = workspace.absolute()
    if workspace.exists() and any(workspace.iterdir()): raise ValueError("Supply a new empty synthetic workspace")
    workspace.mkdir(parents=True, exist_ok=True, mode=0o700); workspace.chmod(0o700)
    garden = workspace / "garden"; garden.mkdir(mode=0o700)
    config = workspace / "bindings.json"
    initialize = ["init", "--repository-root", str(garden), "--garden-id", "synthetic-garden", "--visibility", "private",
                  "--kind", "personal", "--title", "Synthetic PDF garden", "--owner", "synthetic-owner",
                  "--canonical-uri", "urn:synthetic:document-garden", "--domain", "knowledge-systems", "--topic", "prompt-bank"]
    plan = cli(initialize); cli([*initialize, "--apply", "--plan-digest", plan["plan_sha256"]])
    config.write_bytes(canonical_json({"schema": "mindgarden.local-bindings/v1", "gardens": [
        {"id": "synthetic-garden", "root": str(garden), "scope": local_scope()}], "vaults": [
        {"id": "synthetic-vault", "root": str(workspace / "vault"), "adapter": "filesystem"}], "revoked_sessions": []}))
    config.chmod(0o600)
    vault_args = ["vault", "init", "--local-config", str(config), "--vault-id", "synthetic-vault"]
    plan = cli([*vault_args, "--plan"]); cli([*vault_args, "--apply", "--plan-digest", plan["plan_sha256"]])
    bindings = LocalBindings.load(config); vault = open_vault(bindings, "synthetic-vault")
    fixture = REPOSITORY / "tests/fixtures/documents/complete.pdf"
    review = workspace / "classification.json"
    review.write_bytes(canonical_json({"schema": "mindgarden.document-classification/v1", "kind": "initial-classification",
        "source_sha256": digest_bytes(fixture.read_bytes()), "scope": local_scope(),
        "authority": {"kind": "human", "id": "synthetic-owner"}, "review": {"state": "approved",
        "reviewers": ["synthetic-owner"], "reviewed_at": TIME, "rationale": "New wholly synthetic ordinary fixture."}}))
    review.chmod(0o600)
    arguments = ["document", "--local-config", str(config), "--garden-id", "synthetic-garden", "--vault-id", "synthetic-vault",
                 "--input", str(fixture), "--source-id", "synthetic-pdf", "--title", "Synthetic document", "--origin", "urn:synthetic:pdf",
                 "--owner", "synthetic-owner", "--rights", "Wholly synthetic fixture.", "--captured", TIME,
                 "--classification-review", str(review), "--tool-directory", str(tool_directory)]
    preview = cli([*arguments, "--plan"])
    assert cli([*arguments, "--apply", "--plan-digest", preview["plan_sha256"]])["applied"] is True
    assert cli([*arguments, "--apply", "--plan-digest", cli([*arguments, "--plan"])["plan_sha256"]])["applied"] is False
    states = {}
    for name, expected in (("complete.pdf", "complete"), ("ocr-needed.pdf", "ocr-needed"), ("partial.pdf", "partial"),
                           ("encrypted.pdf", "encrypted"), ("malformed.pdf", "malformed"), ("unsupported.txt", "unsupported")):
        result = LocalPDFReader(tool_directory, vault.root).read((fixture.parent / name).read_bytes())
        assert result["status"] == expected; states[name] = expected
    snapshot = inspect_garden(garden, content_resolver=content_resolver(bindings)).require_valid()
    pages = [json.loads(content_resolver(bindings)(item["artifact"])) for item in snapshot.records.values()
             if item["schema"] == "mindgarden.source/v1" and ":page:" in item.get("x-source-identity", "")]
    golden = json.loads((fixture.parent / "layout.json").read_bytes())
    assert [{key: page[key] for key in ("page", "width", "height", "text", "words")} for page in sorted(pages, key=lambda p:p["page"])] == golden["pages"]
    assert vault.audit()["status"] == "verified"
    assert not list(vault.root.glob(".document-work-*"))
    bundle = next(item["x-adapter"]["metadata"]["document_bundle"] for item in snapshot.records.values()
                  if item["schema"] == "mindgarden.source/v1" and item["kind"] == "captured")
    return {"schema": "mindgarden.document-proof/v1", "status": "passed", "states": states,
            "original_sha256": digest_bytes(fixture.read_bytes()), "page_sha256": [digest_bytes(canonical_json(page)) for page in pages],
            "parser": bundle["parser"], "classification": "explicit-initial-personal-synthetic",
            "restricted_runtime": "unavailable", "temporary_state": "owned-vault-removed", "originals": "preserved",
            "network": "blocked-in-process; no acquisition", "google": "unused", "model": "unused"}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--tool-directory", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true"); mode.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args(); engine = Path(mindgarden.__file__).resolve()
    if arguments.require_source and not engine.is_relative_to(REPOSITORY / "src"): parser.error("Source engine required")
    if arguments.require_installed and (engine.is_relative_to(REPOSITORY / "src") or not engine.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("Isolated installed engine required")
    with patch.dict(os.environ, {}, clear=True), patch("socket.socket", side_effect=AssertionError("Network attempted")):
        report = run(arguments.workspace, arguments.tool_directory)
    content = canonical_json(report)
    if arguments.report:
        with arguments.report.open("xb") as output: output.write(content)
    print(content.decode(), end="")


if __name__ == "__main__": main()
