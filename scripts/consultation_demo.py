#!/usr/bin/env python3
"""Synthetic declared ledger to reviewed knowledge/context and portable packet."""

from argparse import ArgumentParser
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "src"))
    import mindgarden

from mindgarden.application.bindings import LocalBindings
from mindgarden.application.consultation import plan_packet
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.source_evidence import resolve_source_evidence
from mindgarden.application.storage import open_vault
from mindgarden.domain.contracts import canonical_json, digest_bytes, safe_path

sys.path.insert(0, str(ROOT))
from tests.consultation_fixture import cli, create_fixture
from tests.support_v1 import TIME, write_json


def apply_reviewed(arguments):
    preview = cli(arguments)
    cli(arguments + ["--apply", "--plan-digest", preview["plan_sha256"]])
    return preview


def workflow(workspace, *, fixture_factory=create_fixture):
    workspace = workspace.absolute()
    if (
        any(path.is_symlink() for path in (workspace, *workspace.parents))
        or workspace.exists()
        and any(workspace.iterdir())
    ):
        raise ValueError("Use a new or empty synthetic workspace")
    fixture = fixture_factory(workspace)
    config, session, garden = (
        fixture[key] for key in ("configuration", "session_path", "garden")
    )
    _, files = plan_packet(fixture["context"], fixture["request"])
    packet = json.loads(files["packet.json"])
    assert packet["totals"][0]["net_movement"] == "2259.76"
    output = {
        "id": "synthetic-financial-summary",
        "title": "Synthetic consultation preparation overview",
        "kind": "insight",
        "body": "Synthetic January consultation preparation: USD net movement 2259.76. Income 2500.00; expenses -230.25; refund 10.00; unresolved movement -19.99. Internal transfer pairs are reviewed separately. These are movements, not balances. Missing account and coverage remain unresolved.\n",
        "authors": [{"kind": "human", "id": "synthetic-reviewer"}],
        "review": deepcopy(fixture["request"]["review"]),
        "status": "active",
        "confidence": "medium",
        "epistemic_state": "proposed",
        "attribution": "inferred",
        "domains": ["financial-records"],
        "topics": ["consultation-preparation"],
        "caveats": packet["limitations"],
        "uncertainty": [
            "Missing account and incomplete declared coverage; source statements remain unverified."
        ],
        "contradictions": [],
        "claims": [],
        "synapses": [],
    }
    proposal = {
        "schema": "mindgarden.curation-plan/v1",
        "id": "synthetic-consultation-curation",
        "garden": "synthetic-garden",
        "created_at": TIME,
        "producer": {"kind": "human", "id": "synthetic-reviewer"},
        "review_authority": {"kind": "human", "id": "synthetic-reviewer"},
        "candidates": [
            {
                "id": "synthetic-summary",
                "action": "summarize",
                "sources": fixture["request"]["sources"],
                "rationale": "Authored synthetic summary of independently checked exact-decimal calculations; no model or completeness inference.",
                "merge_inputs": [],
                "output": output,
            }
        ],
    }
    proposal_path = workspace / "curation.json"
    write_json(proposal_path, proposal)
    planned = cli(
        ["gardenize", "--local-config", str(config), "--plan", str(proposal_path)]
    )
    cli(
        [
            "gardenize",
            "--local-config",
            str(config),
            "--apply",
            str(proposal_path),
            "--plan-digest",
            planned["plan_sha256"],
        ]
    )
    write_json(
        session, bind_session_revisions(config, json.loads(session.read_bytes()))
    )
    context = QueryContext.load(config, session)
    shared = [
        "--repository-root",
        str(garden),
        "--local-config",
        str(config),
        "--scope",
        str(session),
    ]
    search = cli(["search", *shared, "--query", "consultation"])
    context_pack = cli(["context", *shared, "--pack", "default", "--format", "json"])
    assert b"synthetic-financial-summary" in canonical_json(search)
    assert b"synthetic-financial-summary" in canonical_json(context_pack)
    index = cli(["index", *shared, "--write"])
    citation = fixture["request"]["sources"][0]
    evidence = resolve_source_evidence(context, **citation)
    assert evidence["source_review"]["state"] == "unreviewed"
    args = [
        "packet",
        "--local-config",
        str(config),
        "--scope",
        str(session),
        "--input",
        str(fixture["request_path"]),
        "--output-directory",
        str(workspace / "packet"),
    ]
    apply_reviewed(args)
    assert cli(args + ["--check"])["status"] == "verified-no-op"
    _, baseline = plan_packet(context, fixture["request"])
    original = open_vault(LocalBindings.load(config), "synthetic-vault")
    backup_bytes = original.export_bundle()
    backup = workspace / "vault-backup.zip"
    apply_reviewed(
        [
            "vault",
            "export",
            "--local-config",
            str(config),
            "--vault-id",
            "synthetic-vault",
            "--output",
            str(backup),
        ]
    )
    assert backup.read_bytes() == backup_bytes
    apply_reviewed(
        [
            "vault",
            "relocate",
            "--local-config",
            str(config),
            "--vault-id",
            "synthetic-vault",
            "--destination",
            str(workspace / "relocated-vault"),
        ]
    )
    assert original.export_bundle() == backup_bytes
    restored = workspace / "restored-vault"
    apply_reviewed(
        [
            "vault",
            "restore",
            "--local-config",
            str(config),
            "--vault-id",
            "synthetic-vault",
            "--input",
            str(backup),
            "--destination",
            str(restored),
        ]
    )
    clean = workspace / "clean-garden"
    clean.mkdir(mode=0o700)
    shutil.copytree(garden / ".garden", clean / ".garden")
    for relative in json.loads((clean / ".garden/garden.json").read_bytes())["roots"][
        "generated"
    ]:
        generated = safe_path(clean / ".garden", relative)
        if generated.exists():
            shutil.rmtree(generated)
    bindings = json.loads(config.read_bytes())
    bindings["gardens"][0]["root"] = str(clean)
    bindings["vaults"][0]["root"] = str(restored)
    clean_config = workspace / "clean-bindings.json"
    write_json(clean_config, bindings)
    recovered = QueryContext.load(clean_config, session)
    _, rebuilt = plan_packet(recovered, fixture["request"])
    assert baseline == rebuilt
    assert resolve_source_evidence(recovered, **citation) == evidence
    clean_shared = [
        "--repository-root",
        str(clean),
        "--local-config",
        str(clean_config),
        "--scope",
        str(session),
    ]
    assert cli(["index", *clean_shared, "--write"]) == index
    assert (
        cli(["context", *clean_shared, "--pack", "default", "--format", "json"])
        == context_pack
    )
    assert str(workspace).encode() not in b"".join(baseline.values())
    return {
        "schema": "mindgarden.synthetic-consultation-proof/v1",
        "status": "passed-bounded-synthetic-workflow",
        "unique_transactions": len(packet["evidence"]),
        "immutable_objects": original.audit()["objects"],
        "totals": packet["totals"],
        "coverage": packet["coverage"],
        "packet_sha256": digest_bytes(baseline["packet.json"]),
        "markdown_sha256": digest_bytes(baseline["packet.md"]),
        "context_sha256": digest_bytes(canonical_json(context_pack)),
        "context_bytes": len(canonical_json(context_pack)),
        "evidence": citation,
        "source_review": "unreviewed",
        "knowledge_review": "approved",
        "knowledge_epistemic_state": "proposed",
        "recovery": "exact packet, index, context and evidence after relocation/restore/clean rebuild",
        "originals": "retained",
        "network": "blocked",
        "models": "unused",
        "google": "unused",
        "private_pilot": "not performed",
    }


def run_demo(workspace, *, fixture_factory=create_fixture):
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
        patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")),
        patch(
            "subprocess.run", side_effect=AssertionError("External process attempted")
        ),
    ):
        return workflow(workspace, fixture_factory=fixture_factory)


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
    result = canonical_json(run_demo(args.workspace))
    if (
        args.check_golden
        and result
        != (ROOT / "tests/fixtures/consultation/expected-proof.json").read_bytes()
    ):
        raise AssertionError("Synthetic proof differs from complete committed golden")
    if args.report:
        with args.report.open("xb") as output:
            output.write(result)
    print(result.decode(), end="")


if __name__ == "__main__":
    main()
