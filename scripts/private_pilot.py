#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Plan and run an explicitly classified private archive pilot outside version control."""

from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import io
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

from mindgarden.adapters.registry_files import control_path, create_control, private_parent, read_control
from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.ingestion import captured_bytes
from mindgarden.application.storage import content_resolver
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main as mindgarden_main

MARKER = "pilot-owner.json"


class PilotError(ValueError): pass


def explicit(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts or any(part.is_symlink() for part in (path, *path.parents)):
        raise PilotError("PILOT_PATH: supply explicit ordinary absolute locations")
    if path.is_relative_to(ROOT):
        raise PilotError("PILOT_PUBLIC_REPOSITORY: keep private pilot inputs and outputs outside this repository")
    return path


def state(workspace):
    control_path(workspace / MARKER)
    marker = read_control(workspace / MARKER, missing_ok=True)
    if workspace.exists() and any(workspace.iterdir()) and marker is None:
        raise PilotError("PILOT_OWNERSHIP: refusing an existing unowned workspace")
    if marker is None: return None, None
    owner = json.loads(marker)
    if owner.get("schema") != "mindgarden.private-pilot-owner/v1":
        raise PilotError("PILOT_OWNERSHIP: unsupported private workspace marker")
    return owner, garden_fingerprint(workspace / "garden")


def plan(archive, workspace, *, classification, manifest_version, owner, captured_at, proposal=None, expires_at=None):
    # Explicit classification precedes even opening or probing the input source.
    if classification != "personal":
        raise PilotError("PILOT_RUNTIME_UNAVAILABLE: restricted or unknown classification needs verified confidential processing")
    archive, workspace = explicit(archive), explicit(workspace)
    observed, fingerprint = state(workspace)
    content_hash = digest_bytes(captured_bytes(archive))
    if observed and observed["source_sha256"] != content_hash:
        raise PilotError("PILOT_SOURCE_CHANGED: use a separately reviewed workspace for a different original")
    if observed and observed["captured_at"] != captured_at:
        raise PilotError("PILOT_CAPTURE_CHANGED: preserve the reviewed capture timestamp on continuation")
    proposal = explicit(proposal) if proposal else None
    return {"schema": "mindgarden.private-pilot-plan/v1", "engine_version": mindgarden.__version__,
            "archive": str(archive), "workspace": str(workspace), "classification": classification,
            "manifest_version": manifest_version, "owner": owner, "captured_at": captured_at, "source_sha256": content_hash,
            "proposal": str(proposal) if proposal else None,
            "proposal_sha256": digest_bytes(proposal.read_bytes()) if proposal else None,
            "before": fingerprint,
            "expires_at": expires_at or (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")}


def cli(arguments, *, json_output=True):
    with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()):
        code = mindgarden_main(arguments)
    if code: raise PilotError("PILOT_OPERATION: " + arguments[0] + " rejected the supplied private inputs; inspect them locally")
    return json.loads(output.getvalue()) if json_output else None


def reviewed_apply(arguments):
    preview = cli(arguments + ["--plan"])
    return cli(arguments + ["--apply", "--plan-digest", preview["plan_sha256"]])


def apply(document, reviewed_digest):
    if digest_bytes(canonical_json(document)) != reviewed_digest:
        raise PilotError("PILOT_PLAN_STALE: inspect the saved plan and supply its exact digest")
    if document.get("schema") != "mindgarden.private-pilot-plan/v1" or document.get("engine_version") != mindgarden.__version__:
        raise PilotError("PILOT_PLAN_STALE: unsupported plan or changed engine")
    current = plan(document["archive"], document["workspace"], classification=document["classification"],
                   manifest_version=document["manifest_version"], owner=document["owner"], captured_at=document["captured_at"],
                   proposal=document["proposal"], expires_at=document["expires_at"])
    workspace = explicit(document["workspace"])
    previous, _ = state(workspace)
    receipt = (previous or {}).get("receipts", {}).get(reviewed_digest)
    if ({key: value for key, value in current.items() if key != "before"}
            != {key: value for key, value in document.items() if key != "before"}
            or current["before"] != document["before"] and (receipt is None or current["before"] != receipt["after"])):
        raise PilotError("PILOT_PLAN_STALE: source, proposal or canonical inputs changed")
    if datetime.now(timezone.utc) >= datetime.fromisoformat(document["expires_at"].replace("Z", "+00:00")):
        raise PilotError("PILOT_EXPIRED: review a fresh bounded pilot plan")
    private_parent(workspace / MARKER)
    garden, vault = workspace / "garden", workspace / "vault"
    configuration, session = workspace / "bindings.json", workspace / "session.json"
    if previous is None:
        garden.mkdir(mode=0o700)
        init = ["init", "--repository-root", str(garden), "--garden-id", "pilot-garden", "--title", "Private pilot garden",
                "--visibility", "private", "--kind", "personal", "--owner", document["owner"],
                "--canonical-uri", "urn:mindgarden:garden:private-pilot", "--domain", "knowledge-systems", "--topic", "prompt-bank"]
        preview = cli(init); cli(init + ["--apply", "--plan-digest", preview["plan_sha256"]], json_output=False)
        create_control(configuration, canonical_json({"schema": "mindgarden.local-bindings/v1", "gardens": [{
            "id": "pilot-garden", "root": str(garden), "scope": local_scope()}],
            "vaults": [{"id": "pilot-vault", "root": str(vault), "adapter": "filesystem"}], "revoked_sessions": []}))
        reviewed_apply(["vault", "init", "--local-config", str(configuration), "--vault-id", "pilot-vault"])
        # Mark the exact owned workspace before import so a rejected package can
        # be inspected/retried without deleting partial private state.
        previous = {"schema": "mindgarden.private-pilot-owner/v1", "source_sha256": document["source_sha256"],
                    "captured_at": document["captured_at"], "receipts": {}}
        create_control(workspace / MARKER, canonical_json(previous))
    with patch("socket.socket", side_effect=AssertionError("Network attempted")), \
            patch("subprocess.run", side_effect=AssertionError("External process attempted")):
        imported = reviewed_apply(["ingest", "--repository-root", str(garden), "--local-config", str(configuration),
            "--vault-id", "pilot-vault", "--input", document["archive"], "--source-id", "pilot-archive",
            "--title", "Private pilot conversation archive", "--origin", "urn:mindgarden:private-pilot", "--captured", document["captured_at"],
            "--owner", document["owner"], "--rights", "Private reference only; no publication grant.", "--media-type", "application/zip",
            "--adapter", "conversation-archive", "--manifest-version", document["manifest_version"]])
        if document["proposal"]:
            preview = cli(["gardenize", "--local-config", str(configuration), "--plan", document["proposal"]])
            cli(["gardenize", "--local-config", str(configuration), "--apply", document["proposal"], "--plan-digest", preview["plan_sha256"]])
        # Session files are immutable private controls. A new reviewed plan gets
        # its own session and never overwrites a previous authority document.
        session = workspace / ("session-" + reviewed_digest + ".json")
        if not session.exists():
            cli(["scope", "--local-config", str(configuration), "--session-id", "pilot-" + reviewed_digest[:16],
                 "--readable-garden", "pilot-garden", "--writable-garden", "pilot-garden", "--allowed-visibility", "personal",
                 "--expires-at", document["expires_at"], "--output", str(session)])
        validation = cli(["validate", "--repository-root", str(garden), "--local-config", str(configuration), "--format", "json"])
        context = cli(["context", "--repository-root", str(garden), "--local-config", str(configuration), "--scope", str(session),
                       "--pack", "default", "--format", "json"])
        create_control(workspace / ("context-" + reviewed_digest + ".json"), canonical_json(context))
    bindings = LocalBindings.load(configuration)
    inspect_garden(garden, content_resolver=content_resolver(bindings)).require_valid()
    unchanged = digest_bytes(captured_bytes(Path(document["archive"]))) == document["source_sha256"]
    if not unchanged: raise PilotError("PILOT_SOURCE_CHANGED: original changed during the operation")
    report = {"schema": "mindgarden.private-pilot-report/v1", "engine_version": mindgarden.__version__,
              "status": "private-checkpoint-passed" if context["included"] else "partial-awaiting-reviewed-knowledge",
              "classification": "personal", "publication": "not-performed", "source_details": "omitted",
              "normalization": "passed", "canonical_validation": validation["status"], "original_unchanged": unchanged,
              "curation": "applied-explicit-plan" if document["proposal"] else "not-run",
              "reviewed_context": "available" if context["included"] else "not-yet-available",
              "public_federation_empathy": "separate-acceptance", "report_review": "private-until-owner-approves-sharing"}
    create_control(workspace / ("redacted-report-" + reviewed_digest + ".json"), canonical_json(report))
    previous_sha256 = digest_bytes(canonical_json(previous))
    previous["receipts"][reviewed_digest] = {"after": garden_fingerprint(garden)}
    # Owner metadata is machine-local, outside canonical records, and updated
    # under the same private atomic-control adapter as the registry.
    from mindgarden.adapters.registry_files import registry_writer, replace_registry

    with registry_writer(workspace / MARKER):
        replace_registry(workspace / MARKER, canonical_json(previous), expected_sha256=previous_sha256, verify_inputs=lambda: None)
    return report


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "apply"))
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--classification", default="restricted", choices=("personal", "restricted"))
    parser.add_argument("--manifest-version")
    parser.add_argument("--owner")
    parser.add_argument("--captured-at")
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--plan-file", type=Path, required=True)
    parser.add_argument("--plan-digest")
    args = parser.parse_args()
    try:
        target = explicit(args.plan_file)
        if args.operation == "plan":
            if not all((args.archive, args.workspace, args.manifest_version, args.owner, args.captured_at)):
                parser.error("plan requires --archive, --workspace, --manifest-version, --owner and --captured-at")
            document = plan(args.archive, args.workspace, classification=args.classification, manifest_version=args.manifest_version,
                            owner=args.owner, captured_at=args.captured_at, proposal=args.proposal)
            create_control(target, canonical_json(document))
            result = {"status": "private-plan-created", "plan_sha256": digest_bytes(canonical_json(document)), "publication": "not-performed"}
        else:
            document = json.loads(read_control(target))
            result = apply(document, args.plan_digest)
    except (PilotError, ContractError, OSError, ValueError, KeyError):
        print("private-pilot: input or private state was rejected; inspect the plan and supported runtime locally", file=sys.stderr); return 2
    print(canonical_json(result).decode(), end=""); return 0


if __name__ == "__main__": raise SystemExit(main())
