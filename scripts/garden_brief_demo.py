#!/usr/bin/env python3
"""Rehearse a reviewed human brief, agent entrypoint and exact evidence offline."""

from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
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

from mindgarden.application.pilot import private_control  # noqa: E402
from mindgarden.domain.contracts import canonical_json, digest_bytes, strict_json  # noqa: E402
from mindgarden.interfaces.cli import main as garden_cli  # noqa: E402
from mindgarden.interfaces.visit_demo import prepare_demo  # noqa: E402


def command(*arguments):
    with redirect_stdout(StringIO()) as stdout, redirect_stderr(StringIO()) as stderr:
        status = garden_cli(list(arguments))
    if status or stderr.getvalue():
        raise RuntimeError(f"Fictional {arguments[0]} failed. {stderr.getvalue().strip()}")
    return stdout.getvalue().encode("utf8")


def retain_output(path, content):
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        existing = private_control(path)
        if existing.stat().st_size != len(content) or existing.read_bytes() != content:
            raise ValueError(f"{path.name} already differs. Choose another disposable workspace.")
        return
    with os.fdopen(descriptor, "wb") as output:
        output.write(content)


def represented_citation(brief, entrypoint):
    _, fence, ledger = entrypoint.partition(b"```json\n")
    if not fence or not ledger.endswith(b"```\n"):
        raise RuntimeError("Agent entrypoint did not contain its versioned JSON ledger")
    document = strict_json(ledger.removesuffix(b"```\n"))
    if (document["schema"], document["trust"], document["scope"]["publication"]) != (
        "mindgarden.agent-entrypoint/v1", "untrusted-evidence", "never-exportable",
    ):
        raise RuntimeError("Agent entrypoint lost its schema, provenance or private scope")
    record = next((item for item in document["records"] if item["reference"]["id"] == "mock-career"), None)
    if record is None or record["review"]["state"] != "approved":
        raise RuntimeError("Expected a reviewed fictional record in the agent entrypoint")
    citation = record["sources"][0]
    source = citation["source"]
    parts = (f"{source['garden']}/{source['id']}", source["revision"], citation["locator"], citation["content_sha256"])
    if not any(all(f"`{part}`" in line for part in parts) for line in brief.decode("utf8").splitlines()):
        raise RuntimeError("The human brief did not include the agent entrypoint's exact citation")
    return record["reference"], citation


def run_demo(workspace):
    workspace = workspace.expanduser().absolute()
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
        patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")),
        patch("subprocess.run", side_effect=AssertionError("External process attempted")),
    ):
        bindings, scope = prepare_demo(workspace)
        auth = ("--local-config", str(bindings), "--scope", str(scope))
        brief = command("brief", *auth)
        entrypoint_args = ("llms", "--repository-root", str(bindings.parent / "garden"), *auth)
        entrypoint = command(*entrypoint_args)
        if command("brief", *auth) != brief or command(*entrypoint_args) != entrypoint:
            raise RuntimeError("Identical inputs did not rebuild identical projections")
        record, citation = represented_citation(brief, entrypoint)
        source = citation["source"]
        evidence_bytes = command(
            "evidence", *auth,
            "--garden-id", source["garden"], "--source-id", source["id"],
            "--revision", source["revision"], "--locator", citation["locator"],
            "--content-sha256", citation["content_sha256"],
        )
        evidence = strict_json(evidence_bytes)
        if (
            evidence["trust"] != "untrusted-evidence"
            or evidence["scope"]["publication"] != "never-exportable"
            or evidence["source_review"]["state"] != "unreviewed"
            or not any(item["reference"] == record for item in evidence["authorized_by"])
            or {key: evidence[key] for key in citation} != citation
            or digest_bytes(evidence["text"].encode("utf8")) != citation["content_sha256"]
        ):
            raise RuntimeError("The exact reviewed evidence did not resolve under the same authority")
        if any(str(workspace).encode() in output for output in (brief, entrypoint, evidence_bytes)):
            raise RuntimeError("A projection exposed the machine-local workspace")
        brief_path = workspace / "GARDEN-BRIEF.md"
        retain_output(brief_path, brief)
        retain_output(workspace / "llms.txt", entrypoint)
        command("brief", *auth, "--check", str(brief_path))
    return {
        "schema": "mindgarden.fictional-brief-proof/v1",
        "status": "passed-fictional-brief",
        "brief_sha256": digest_bytes(brief),
        "entrypoint_sha256": digest_bytes(entrypoint),
        "evidence_sha256": digest_bytes(evidence_bytes),
        "reviewed_reference": record,
        "citation": citation,
        "scope": evidence["scope"],
        "network": "blocked",
        "model_calls": 0,
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="New or existing owned fictional workspace outside Git")
    engine = parser.add_mutually_exclusive_group()
    engine.add_argument("--require-source", action="store_true")
    engine.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args()
    module = Path(mindgarden.__file__).resolve()
    source_engine = module.is_relative_to(ROOT / "src")
    if arguments.require_source and not source_engine:
        parser.error("Exact source engine required")
    if arguments.require_installed and (source_engine or not module.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("Installed engine required")
    try:
        receipt = run_demo(arguments.workspace)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
    print(canonical_json(receipt).decode("utf8"), end="")


if __name__ == "__main__":
    main()
