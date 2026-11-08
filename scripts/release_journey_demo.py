#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Compose the synthetic archive, reviewed routing, scoped context and public export journey."""

from argparse import ArgumentParser
from copy import deepcopy
import json
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

from mindgarden.application.bindings import LocalBindings
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.routing import snapshots_for
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.records import provenance_record
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.scope import local_scope


def workflow(workspace):
    workspace = workspace.absolute()
    if any(path.is_symlink() for path in (workspace, *workspace.parents)) or (workspace.exists() and any(workspace.iterdir())):
        raise ValueError("Synthetic journey requires a new or empty ordinary workspace")
    workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT))
    from scripts.private_garden_demo import cli_json, reviewed_apply, run_demo as private_workflow
    from tests.federation_fixture import FEDERATION_FIXTURES
    from tests.site_fixture import create_fixture
    from tests.support_v1 import reference, write_json, write_session

    private = private_workflow(workspace / "archive")
    public = create_fixture(workspace / "public")
    configuration = workspace / "bindings.json"
    document = json.loads((workspace / "archive/bindings.json").read_bytes())
    public_binding = json.loads(public["configuration"].read_bytes())["gardens"][0]
    document["gardens"].append(public_binding)
    write_json(configuration, document)
    raw = json.loads((public["workspace"] / ".garden/sources/public-source.json").read_bytes())
    normalized = deepcopy(raw)
    normalized.update(id="reviewed-public-source", kind="normalized", publication="eligible", scope=local_scope("public", publication="publishable"),
        inputs=[reference(public_binding["id"], raw["id"], raw["artifact"]["sha256"])],
        review={"state": "approved", "reviewers": ["synthetic-reviewer"], "reviewed_at": "2026-11-04T00:00:00Z",
                "rationale": "Explicit synthetic review of the separately public source."})
    provenance = provenance_record(public_binding["id"], "provenance-reviewed-public-source", normalized["id"], raw["artifact"]["sha256"],
        inputs=[{"artifact": normalized["inputs"][0], "sha256": raw["artifact"]["sha256"], "role": "source"}],
        transformations=({"name": "authored-public-normalization", "version": "1.0.0", "parameters": {"result": "already canonical LF text"}},),
        created_at="2026-11-04T00:00:00Z", rights="Explicit public synthetic fixture.", origin="urn:synthetic:public-source",
        scope=local_scope("public", publication="publishable"))
    normalized["provenance"] = [reference(public_binding["id"], provenance["id"], digest_bytes(canonical_json(provenance)))]
    write_json(public["workspace"] / ".garden/provenance/provenance-reviewed-public-source.json", provenance)
    write_json(public["workspace"] / ".garden/sources/reviewed-public-source.json", normalized)
    public["evidence"] = [{**public["evidence"][0], "source": reference(public_binding["id"], normalized["id"], normalized["artifact"]["sha256"])}]
    bindings = LocalBindings.load(configuration)
    snapshots = snapshots_for(bindings)
    catalog = {"schema": "mindgarden.garden-catalog/v1", "id": "release-catalog", "private_fallback": "synthetic-garden",
        "gardens": [{"id": identity, "scope": bindings.garden(identity)["scope"],
            **{field: snapshot.manifest[field] for field in ("kind", "owners", "canonical_uri", "contracts")},
            "domains": snapshot.manifest["routing"]["domains"]} for identity, snapshot in sorted(snapshots.items())]}
    catalog_path = workspace / "catalog.json"; write_json(catalog_path, catalog)
    proposal = json.loads((ROOT / "tests/fixtures/conversation-archives/authored-plan.json").read_bytes())
    template = proposal["candidates"][0]
    personal = deepcopy(template); personal.update(id="release-personal", action="summarize")
    personal["output"].update(id="release-private-insight", title="Private release checklist insight",
        body="For this release checklist, preserve cited archive evidence and its uncertainty in the private garden.\n")
    selected_public = deepcopy(template); selected_public.update(id="release-public", sources=public["evidence"])
    selected_public["output"].update(id="release-public-procedure", title="Reviewed public source procedure",
        body=(FEDERATION_FIXTURES / "source.txt").read_text().splitlines(keepends=True)[0])
    proposal.update(id="release-journey-curation", candidates=[personal, selected_public])
    request = {"schema": "mindgarden.routing-plan/v1", "id": "release-journey-routing", "curation": proposal, "routes": [
        {"candidate": item["id"], "preferred_gardens": [public_binding["id"]], "relevant_gardens": [],
         "confidence": "medium", "rationale": "Explicit synthetic source/sensitivity routing review.",
         "public_review": deepcopy(item["output"]["review"])} for item in proposal["candidates"]]}
    request_path = workspace / "routing.json"; write_json(request_path, request)
    routing = ["route", "--local-config", str(configuration), "--catalog", str(catalog_path), "--input", str(request_path)]
    preview = cli_json(routing + ["--plan"])
    first = cli_json(routing + ["--apply", "--plan-digest", preview["plan_sha256"]])
    repeat_preview = cli_json(routing + ["--plan"])
    repeat = cli_json(routing + ["--apply", "--plan-digest", repeat_preview["plan_sha256"]])
    assert first["applied"] and not repeat["applied"]
    decisions = {item["candidate"]: item for item in preview["decisions"]}
    assert decisions["release-personal"]["state"] == "private-fallback"
    assert decisions["release-public"]["canonical_home"]["garden"] == public_binding["id"]

    session_path = workspace / "public-session.json"
    session = write_session(session_path, configuration, visibility=["public"], readable_ids=[public_binding["id"]], writable=public_binding["id"])
    session.update(request_scope=local_scope("public", publication="publishable"), publication_authority="publishable")
    write_json(session_path, bind_session_revisions(configuration, session))
    context = QueryContext.load(configuration, session_path)
    index = build_index(context)
    public_note = next(item for item in index["records"] if item["id"] == "release-public-procedure")
    assert public_note["sources"] == public["evidence"]
    profile = public["profile"]
    profile.update(inputs=[item["reference"] for item in index["records"]], source_revision=index["inputs"][0]["revision"])
    write_json(public["profile_path"], profile)
    shared = ["--repository-root", str(public["workspace"]), "--local-config", str(configuration), "--scope", str(session_path)]
    # Explicit selection is scoped to already-public, separately supplied
    # evidence. No private archive fact is silently declassified for this fork.
    pack_path = public["workspace"] / ".garden/context-packs/default.json"
    pack = json.loads(pack_path.read_bytes()); pack.update(include=[reference(public_binding["id"], "release-public-procedure")], query="", max_items=1)
    write_json(pack_path, pack)
    write_json(session_path, bind_session_revisions(configuration, session))
    context_pack = cli_json(["context", *shared, "--pack", "default", "--format", "json"])
    public_profile = ["--profile", str(public["profile_path"]), "--output-directory", str(public["export"])]
    reviewed_apply(["publish", "project", *shared, *public_profile])
    site_manifest = cli_json(["publish", "verify", *shared, *public_profile])
    for _ in range(2):
        search = cli_json(["search", *shared, "--query", "evidence"])
        assert any(item["reference"]["id"] == "release-public-procedure" for item in search["results"])
    public_bytes = b"".join(path.read_bytes() for path in public["export"].rglob("*") if path.is_file())
    federation_profile = json.loads((FEDERATION_FIXTURES / "profile.json").read_bytes())
    federation_profile.update(garden=public_binding["id"], source_revision=profile["source_revision"], inputs=profile["inputs"])
    federation_path = workspace / "federation-profile.json"; write_json(federation_path, federation_profile)
    federation_export = workspace / "federation-export"; federation_export.mkdir()
    federation_arguments = ["federation", "build", "--local-config", str(configuration), "--scope", str(session_path),
        "--profile", str(federation_path), "--output-directory", str(federation_export)]
    federation_plan = cli_json([*federation_arguments, "--plan"])
    descriptor = cli_json([*federation_arguments, "--apply", "--plan-digest", federation_plan["plan_sha256"]])
    assert cli_json([*federation_arguments, "--check"]) == descriptor
    public_bytes += b"".join(path.read_bytes() for path in federation_export.rglob("*") if path.is_file())
    for canary in ("synthetic-garden", "synthetic-archive", "release-private-insight", "release-personal", "hidden-root-canary", str(workspace)):
        assert canary.encode() not in public_bytes
        assert canary.encode() not in canonical_json(context_pack)
    return {"schema": "mindgarden.synthetic-release-journey/v1", "status": "supported-synthetic-journey-passed",
        "engine_version": mindgarden.__version__, "archive_private_workflow": private,
        "routing": {"private": decisions["release-personal"]["state"], "public": decisions["release-public"]["state"], "repeat": "verified-no-op"},
        "public_reference": public_note["reference"], "public_evidence": public_note["sources"],
        "public_context_bytes": len(canonical_json(context_pack)), "public_context_budget": context_pack["budget"]["max_bytes"],
        "site": {"kind": site_manifest["kind"], "routes": site_manifest["routes"], "revision": site_manifest["revision"]},
        "federation": {"garden": descriptor["garden"], "revision": descriptor["revision"], "visibility": context_pack["scope"]["visibility"]},
        "public_fork": "separately supplied reviewed-public evidence; private archive remains private",
        "checks": ["archive-review-search-exact-evidence-context-restore-relocation-rebuild", "explained-private-fallback",
            "explicit-reviewed-public-route", "duplicate-safe-routing-repeat", "public-source-identity-and-revision-preserved",
            "no-private-content-id-count-or-path-in-public-projections"],
        "limitations": ["Authored synthetic agent proposal and human review, not live AI/real-person approval.",
            "Content projection verified; actual renderer/deployment, approved real pilot and upstream Empathy acceptance are separate."],
        "deployment": "not-performed", "model": "unused", "google": "unused"}


def run_demo(workspace):
    with patch.dict(os.environ, {}, clear=True), patch("socket.socket", side_effect=AssertionError("Network attempted")), \
            patch("subprocess.run", side_effect=AssertionError("External process attempted")):
        return workflow(workspace)


def main():
    parser = ArgumentParser(description=__doc__); parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    group = parser.add_mutually_exclusive_group(); group.add_argument("--require-source", action="store_true"); group.add_argument("--require-installed", action="store_true")
    args = parser.parse_args(); engine = Path(mindgarden.__file__).resolve()
    if args.require_source and not engine.is_relative_to(ROOT / "src"): parser.error("Exact source engine required")
    if args.require_installed and (engine.is_relative_to(ROOT / "src") or not engine.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("Installed engine in this interpreter prefix required")
    report = run_demo(args.workspace)
    if args.report:
        with args.report.open("xb") as stream: stream.write(canonical_json(report))
    print(canonical_json(report).decode(), end="")


if __name__ == "__main__": main()
