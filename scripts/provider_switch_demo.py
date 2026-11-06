#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Prove scoped context recovery after deleting a synthetic provider and its caches."""

from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
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

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import projection_directory
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.interfaces.cli import main as mindgarden_main


def cli_json(arguments):
    with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()):
        status = mindgarden_main(arguments)
    if status:
        raise AssertionError("Synthetic scoped command failed: " + arguments[0])
    return json.loads(output.getvalue())


def retrieve(fixture, *, write_index=False):
    shared = ["--repository-root", str(fixture["garden"]), "--local-config", str(fixture["bindings"]), "--scope", str(fixture["session"])]
    index = cli_json(["index", *shared, *(["--write"] if write_index else [])])
    context = cli_json(["context", *shared, "--pack", "default", "--format", "json"])
    graph = cli_json(["graph", *shared])
    citation = fixture["evidence"]
    evidence = cli_json(["evidence", "--local-config", str(fixture["bindings"]), "--scope", str(fixture["session"]),
                         "--garden-id", citation["source"]["garden"], "--source-id", citation["source"]["id"],
                         "--revision", citation["source"]["revision"], "--locator", citation["locator"],
                         "--content-sha256", citation["content_sha256"]])
    assert {item["reference"]["id"] for item in context["included"]} == set(fixture["selected"])
    assert "daily-review-claim" not in {item["id"] for item in index["records"]}
    assert len(canonical_json(context)) <= context["budget"]["max_bytes"]
    return {"context": context, "graph": graph, "evidence": evidence}


def load_adapter(path):
    spec = importlib.util.spec_from_file_location("synthetic_provider_adapter", path)
    adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
    return adapter


def workflow(workspace):
    workspace = workspace.absolute()
    if any(path.is_symlink() for path in (workspace, *workspace.parents)) or (workspace.exists() and any(workspace.iterdir())):
        raise ValueError("Synthetic demo requires a new or empty ordinary workspace")
    workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
    sys.path.insert(0, str(REPOSITORY_ROOT))
    from tests.provider_continuity_fixture import FIXTURE, create_fixture

    fixture = create_fixture(workspace)
    before = garden_fingerprint(fixture["garden"])
    source_before = fixture["vault"].export_bundle()
    adapter_root = workspace / "disposable-providers"
    first_root = adapter_root / "alpha"; first_root.mkdir(parents=True)
    second_root = adapter_root / "beta"; second_root.mkdir()
    shutil.copyfile(FIXTURE / "adapters/alpha.py", first_root / "adapter.py")
    shutil.copyfile(FIXTURE / "adapters/beta.py", second_root / "adapter.py")
    original_open = Path.open

    def selected_only(path, *args, **kwargs):
        if path.is_relative_to(fixture["denied"]):
            raise AssertionError("Out-of-scope root was opened")
        return original_open(path, *args, **kwargs)

    with patch.object(Path, "open", selected_only):
        state = retrieve(fixture, write_index=True)
        alpha = load_adapter(first_root / "adapter.py")
        alpha_descriptor = alpha.DESCRIPTOR
        first_wire = alpha.project(state)
        expected = canonical_json(alpha.recover(first_wire))
        (first_root / "context-cache.json").write_bytes(first_wire)
        (first_root / "provider-memory.txt").write_text("Volatile provider memory is disposable.\n")
        del alpha
        context = QueryContext.load(fixture["bindings"], fixture["session"])
        cache = projection_directory(context, fixture["garden"])
        assert cache.is_relative_to(fixture["garden"] / ".garden") and cache.is_dir()
        shutil.rmtree(first_root)
        shutil.rmtree(cache)
        assert not first_root.exists() and not cache.exists()
        recovered = retrieve(fixture)
        beta = load_adapter(second_root / "adapter.py")
        second_wire = beta.project(recovered)
        assert first_wire != second_wire
        assert canonical_json(beta.recover(second_wire)) == expected
        assert canonical_json(retrieve(fixture)) == expected

    for content in (first_wire, second_wire, canonical_json(recovered)):
        for canary in ("out-of-scope-garden-canary", "denied-record-canary", "denied-body-canary", "unreviewed-canary", "unreviewed-body-canary", str(workspace)):
            assert canary.encode() not in content
    assert garden_fingerprint(fixture["garden"]) == before
    assert fixture["vault"].export_bundle() == source_before
    assert any(
        fixture["old_claim"]["revision"] in item["content"] for item in recovered["context"]["included"])
    assert any(edge["type"] == "supersedes" for edge in recovered["graph"]["edges"])
    assert recovered["evidence"]["source_identity"] and recovered["evidence"]["lineage"]
    context = recovered["context"]
    return {"schema": "mindgarden.synthetic-provider-continuity-proof/v1", "status": "passed", "engine_version": mindgarden.__version__,
            "policy": context["policy"], "scope": context["scope"], "inputs": context["inputs"],
            "adapters": [alpha_descriptor, beta.DESCRIPTOR], "first_adapter_removed": not first_root.exists(),
            "structured_context_sha256": digest_bytes(expected), "context_bytes": len(canonical_json(context)),
            "context_max_bytes": context["budget"]["max_bytes"],
            "selected": [{"reference": item["reference"], "sources": item["sources"], "review": item["review"]["state"]} for item in context["included"]],
            "supersession": {"previous": fixture["old_claim"], "current": fixture["new_claim"]},
            "omission_policy": "Unselected gardens and unapproved records are not enumerated; deprecated claims are historical, not current answers.",
            "limitations": ["Local adapter conformance, not live provider inference or equivalent model behavior.",
                            "Deprecated claim identity is retained in authored reviewed decision history; current claim ranking excludes it."],
            "canonical_inputs_unchanged": True, "source_assets_unchanged": True,
            "integrations": {"network": "blocked-in-process", "subprocess": "blocked-in-process", "google": "unused", "model": "unused"},
            "checks": ["same-explicit-policy-and-scoped-request", "distinct-local-adapter-envelopes", "first-adapter-and-owned-cache-removed",
                       "clean-rebuild-equivalent-structured-context", "preferences-goals-artifact-decision-and-correction-recovered",
                       "exact-source-identity-revision-and-evidence", "typed-supersession-retained", "denied-root-never-opened",
                       "no-denied-body-id-count-or-path-leak", "canonical-knowledge-review-and-originals-unchanged"]}


def run_demo(workspace):
    with patch.dict(os.environ, {}, clear=True), patch("socket.socket", side_effect=AssertionError("Network attempted")), \
            patch("urllib.request.urlopen", side_effect=AssertionError("Remote acquisition attempted")), \
            patch("subprocess.run", side_effect=AssertionError("External process attempted")):
        return workflow(workspace)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    args = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    if args.require_source and not engine.is_relative_to(REPOSITORY_ROOT / "src"):
        parser.error("This proof requires this source checkout's engine")
    if args.require_installed and (engine.is_relative_to(REPOSITORY_ROOT / "src") or not engine.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("This proof requires the installed engine in the interpreter prefix")
    report = run_demo(args.workspace)
    if args.report:
        with args.report.open("xb") as stream: stream.write(canonical_json(report))
    print(canonical_json(report).decode(), end="")


if __name__ == "__main__":
    main()
