#!/usr/bin/env python3
"""Reproduce the selected pipeline with authored proposals and relocated evidence."""

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

from mindgarden.adapters.registry_files import control_path
from mindgarden.application.bindings import LocalBindings
from mindgarden.application.extraction import produce_batch
from mindgarden.application.query import QueryContext
from mindgarden.application.storage import open_vault
from mindgarden.domain.contracts import (
    canonical_json,
    digest_bytes,
    read_object,
    safe_path,
)
from mindgarden.domain.scope import local_scope

sys.path.insert(0, str(ROOT / "scripts"))
from private_garden_demo import (
    cli,
    cli_json,
    reviewed_apply,
    workflow as baseline_workflow,
    write_json,
    TIME,
)


FIXTURES = ROOT / "tests/fixtures"


def scope(configuration, path, *, source_grants=None):
    args = [
        "scope",
        "--local-config",
        str(configuration),
        "--session-id",
        "synthetic-pipeline-session",
        "--readable-garden",
        "synthetic-garden",
        "--writable-garden",
        "synthetic-garden",
        "--allowed-visibility",
        "personal",
        "--expires-at",
        "2099-01-01T00:00:00Z",
        "--request-visibility",
        "personal",
        "--publication-authority",
        "never-exportable",
        "--output",
        str(path),
    ]
    if source_grants:
        args += [
            "--source-grants",
            str(source_grants),
            "--projection",
            "source-evidence",
            "--projection",
            "index",
            "--max-context-bytes",
            "65536",
        ]
    else:
        args += ["--readable-garden", "project-garden"]
    cli(args)


def workflow(workspace):
    if any(path.is_symlink() for path in (workspace, *workspace.parents)):
        raise ValueError("Synthetic proof requires an ordinary new or empty workspace")
    control_path(workspace / "source-grants.json")
    baseline = baseline_workflow(workspace)
    configuration = workspace / "bindings.json"
    garden = workspace / "garden"
    # Reuse committed data recipes, not test classes or a model. The engine has
    # already been imported, including in installed-only verification mode.
    sys.path.insert(0, str(ROOT))
    from tests.archive_fixture import package_bytes, v2_members

    inputs = []
    for name, captured, media, adapter, version in (
        (
            "archive",
            package_bytes(v2_members()),
            "application/zip",
            "conversation-archive",
            "2.0.2",
        ),
        (
            "bookmarks",
            (FIXTURES / "captured-source/synthetic-source.zip").read_bytes(),
            "application/vnd.mindcap.captured-source+zip",
            "captured-source-bundle",
            "1",
        ),
        (
            "page",
            (FIXTURES / "extraction/page.txt").read_bytes(),
            "text/plain",
            "plain-text",
            None,
        ),
    ):
        path = workspace / ("pipeline-" + name + ".capture")
        path.write_bytes(captured)
        arguments = [
            "ingest",
            "--repository-root",
            str(garden),
            "--local-config",
            str(configuration),
            "--vault-id",
            "synthetic-vault",
            "--input",
            str(path),
            "--source-id",
            "pipeline-" + name,
            "--title",
            "Synthetic pipeline " + name,
            "--origin",
            "urn:synthetic:pipeline:" + name,
            "--captured",
            TIME,
            "--owner",
            "synthetic-owner",
            "--rights",
            "Authored synthetic fixtures only.",
            "--media-type",
            media,
            "--adapter",
            adapter,
        ]
        if version:
            arguments += ["--manifest-version", version]
        imported = reviewed_apply(arguments)
        assert not reviewed_apply(arguments)["applied"]
        vault = open_vault(LocalBindings.load(configuration), "synthetic-vault")
        for source in imported["inputs"]["normalized_sources"]:
            label = None
            if (
                name == "archive"
                and source["metadata"].get("message_id") == "message-prompt"
            ):
                label = "assistant"
            if name == "bookmarks":
                label = (
                    "inert"
                    if b"inert-bookmarklet" in vault.get(source["source"]["revision"])
                    else "bookmark"
                )
            if name == "page":
                label = "page"
            if label:
                evidence = source["evidence"][0]
                if name == "bookmarks":
                    evidence = {
                        "source": source["source"],
                        "locator": "artifact",
                        "content_sha256": source["source"]["revision"][7:],
                    }
                inputs.append((label, evidence))
    grants = workspace / "source-grants.json"
    write_json(grants, {"source_grants": [e["source"] for _, e in inputs]})
    source_session = workspace / "pipeline-source-session.json"
    scope(configuration, source_session, source_grants=grants)
    context = QueryContext.load(configuration, source_session)
    descriptor = {
        "id": "authored-extraction",
        "version": "1.0.0",
        "model": "authored-fixture-no-model",
        "prompt_revision": digest_bytes(b"synthetic-extraction-prompt/v1"),
        "schema_revision": "mindgarden.extraction-output/v1",
    }
    request = {
        "schema": "mindgarden.extraction-request/v1",
        "id": "pipeline-curation",
        "garden": "synthetic-garden",
        "created_at": TIME,
        "domains": ["knowledge-systems"],
        "topics": ["prompt-bank"],
        "producer": descriptor,
        "sources": [e for _, e in inputs],
        "limits": {"max_input_bytes": 65536, "max_output_bytes": 32768},
    }
    responses = read_object(FIXTURES / "extraction/responses.json")
    labels = {canonical_json(e): label for label, e in inputs}
    recording = {"producer": descriptor, "outputs": {}}

    class AuthoredProducer:
        execution = "offline"
        descriptor = deepcopy(request["producer"])

        def extract(self, evidence):
            output = deepcopy(responses[labels[canonical_json(evidence["evidence"])]])
            recording["outputs"][evidence["input_sha256"]] = output
            return output

    producer = AuthoredProducer()
    partial = produce_batch(context, request, producer, max_new_units=1)
    resumed = produce_batch(context, request, producer, previous=partial)
    assert resumed["new_calls"] == 3
    assert produce_batch(context, request, producer, previous=resumed)["new_calls"] == 0
    request_path = workspace / "extraction-request.json"
    write_json(request_path, request)
    recording_path = workspace / "recorded-proposals.json"
    write_json(recording_path, recording)
    arguments = [
        "extraction",
        "--local-config",
        str(configuration),
        "--scope",
        str(source_session),
        "--input",
        str(request_path),
        "--recorded-output",
        str(recording_path),
        "--output-directory",
        str(workspace / "unreviewed-proposals"),
    ]
    preview = cli_json(arguments)
    cli_json([*arguments, "--apply", "--plan-digest", preview["plan_sha256"]])
    proposal = deepcopy(preview["batch"]["proposal"])
    assert proposal["review_authority"] is None
    review = {
        "state": "approved",
        "reviewers": ["synthetic-reviewer"],
        "reviewed_at": TIME,
        "rationale": "Authored synthetic approval to keep attributed unverified proposals; not factual verification.",
    }
    proposal["review_authority"] = {"kind": "human", "id": "synthetic-reviewer"}
    for candidate in proposal["candidates"]:
        output = candidate["output"]
        assert output["review"]["state"] == "unreviewed"
        output.update(review=review, status="active")
        for item in output["claims"] + output["synapses"]:
            item["review"] = review
    reviewed_path = workspace / "reviewed-proposals.json"
    write_json(reviewed_path, proposal)
    curation = cli_json(
        [
            "gardenize",
            "--local-config",
            str(configuration),
            "--plan",
            str(reviewed_path),
        ]
    )
    cli_json(
        [
            "gardenize",
            "--local-config",
            str(configuration),
            "--apply",
            str(reviewed_path),
            "--plan-digest",
            curation["plan_sha256"],
        ]
    )
    selected = next(
        c["output"]
        for c in proposal["candidates"]
        if c["output"]["title"] == "Exact evidence may support explicit uncertainty."
    )
    original_id = selected["id"]
    original = read_object(garden / ".garden/knowledge" / (original_id + ".json"))
    project = workspace / "project-garden"
    project.mkdir(mode=0o700)
    initialization = [
        "init",
        "--repository-root",
        str(project),
        "--visibility",
        "private",
        "--kind",
        "repository",
        "--garden-id",
        "project-garden",
        "--title",
        "Synthetic project garden",
        "--owner",
        "synthetic-owner",
        "--canonical-uri",
        "urn:mindgarden:garden:project-garden",
        "--domain",
        "knowledge-systems",
        "--topic",
        "prompt-bank",
    ]
    initialized = cli_json(initialization)
    cli([*initialization, "--apply", "--plan-digest", initialized["plan_sha256"]])

    bindings = read_object(configuration)
    bindings["gardens"].append(
        {"id": "project-garden", "root": str(project), "scope": local_scope()}
    )
    write_json(configuration, bindings)
    transition = {
        "schema": "mindgarden.routing-transition/v1",
        "id": "pipeline-move",
        "created_at": TIME,
        "operation": "move",
        "from": [
            {
                "garden": "synthetic-garden",
                "id": original_id,
                "revision": "sha256:" + original["content"]["sha256"],
            }
        ],
        "to": {
            "garden": "project-garden",
            "id": "moved-extracted-prompt",
            "revision": None,
        },
        "authority": {"kind": "human", "id": "synthetic-reviewer"},
        "review": review,
        "rationale": "Explicit private move retaining attached graph and original evidence.",
    }
    transition_path = workspace / "reviewed-move.json"
    write_json(transition_path, transition)
    reviewed_apply(
        [
            "route",
            "--local-config",
            str(configuration),
            "--transition",
            str(transition_path),
        ]
    )
    session = workspace / "pipeline-read-session.json"
    scope(configuration, session)
    catalog = cli_json(
        [
            "federation",
            "local-discover",
            "--local-config",
            str(configuration),
            "--scope",
            str(session),
        ]
    )
    assert len(catalog["gardens"]) == 2 and catalog["publication"] == "never-exportable"
    selection = [
        {"garden": entry["garden"], "revision": entry["revision"]}
        for entry in catalog["gardens"]
    ]
    query_path = workspace / "selected-query.json"

    def query(document, config=configuration):
        write_json(
            query_path,
            {
                "schema": "mindgarden.local-federation-query/v1",
                "gardens": selection,
                **document,
            },
        )
        return cli(
            [
                "federation",
                "local-query",
                "--local-config",
                str(config),
                "--scope",
                str(session),
                "--input",
                str(query_path),
            ]
        ).encode()

    search = json.loads(
        query(
            {"operation": "search", "query": "exact evidence uncertainty", "limit": 100}
        )
    )
    entry = next(
        result
        for result in search["results"]
        if result["reference"]["id"] == "moved-extracted-prompt"
    )
    assert not any(
        result["reference"]["id"] == original_id for result in search["results"]
    )
    citation = entry["sources"][0]
    assert citation == next(e for label, e in inputs if label == "assistant")
    profile = {
        "schema": "mindgarden.context-profile/v1",
        "id": "pipeline-pack",
        "garden": "project-garden",
        "title": "Synthetic reviewed pipeline context",
        "description": "Exact-source selected moved proposal.",
        "query": "evidence",
        "include": [entry["reference"]],
        "exclude": [],
        "kinds": [],
        "max_items": 1,
        "max_bytes": 8192,
        "max_candidates": 16,
    }
    pack_request = {"operation": "context", "profile": profile, "format": "json"}
    pack = query(pack_request)
    assert len(pack) <= 8192 and json.loads(pack)["included"][0]["sources"] == [
        citation
    ]
    graph_request = {
        "operation": "graph",
        "start": "project-garden/moved-extracted-prompt",
        "depth": 1,
        "limit": 100,
    }
    graph = query(graph_request)
    index = cli_json(
        [
            "index",
            "--repository-root",
            str(garden),
            "--local-config",
            str(configuration),
            "--scope",
            str(session),
        ]
    )
    vault = open_vault(LocalBindings.load(configuration), "synthetic-vault")
    original_bundle = vault.export_bundle()
    backup = workspace / "pipeline-vault-backup.zip"
    reviewed_apply(
        [
            "vault",
            "export",
            "--local-config",
            str(configuration),
            "--vault-id",
            "synthetic-vault",
            "--output",
            str(backup),
        ]
    )
    assert backup.read_bytes() == original_bundle
    reviewed_apply(
        [
            "vault",
            "relocate",
            "--local-config",
            str(configuration),
            "--vault-id",
            "synthetic-vault",
            "--destination",
            str(workspace / "pipeline-relocated-vault"),
        ]
    )
    assert (
        query(pack_request) == pack
        and query(graph_request) == graph
        and vault.export_bundle() == original_bundle
    )
    restored = workspace / "pipeline-restored-vault"
    reviewed_apply(
        [
            "vault",
            "restore",
            "--local-config",
            str(configuration),
            "--vault-id",
            "synthetic-vault",
            "--input",
            str(backup),
            "--destination",
            str(restored),
        ]
    )
    clean = workspace / "pipeline-clean"
    clean.mkdir(mode=0o700)
    clean_bindings = read_object(configuration)
    for binding in clean_bindings["gardens"]:
        root = clean / binding["id"]
        root.mkdir(mode=0o700)
        shutil.copytree(Path(binding["root"]) / ".garden", root / ".garden")
        for generated in read_object(root / ".garden/garden.json")["roots"][
            "generated"
        ]:
            path = safe_path(root / ".garden", generated)
            if path.exists():
                shutil.rmtree(
                    path
                )  # only disposable projections in this new synthetic copy
        binding["root"] = str(root)
    clean_bindings["vaults"][0]["root"] = str(restored)
    clean_config = workspace / "pipeline-clean-bindings.json"
    write_json(clean_config, clean_bindings)
    assert (
        query(pack_request, clean_config) == pack
        and query(graph_request, clean_config) == graph
    )
    clean_index = cli_json(
        [
            "index",
            "--repository-root",
            str(clean / "synthetic-garden"),
            "--local-config",
            str(clean_config),
            "--scope",
            str(session),
            "--write",
        ]
    )
    assert clean_index == index
    source = citation["source"]
    evidence = cli_json(
        [
            "evidence",
            "--local-config",
            str(clean_config),
            "--scope",
            str(session),
            "--garden-id",
            source["garden"],
            "--source-id",
            source["id"],
            "--revision",
            source["revision"],
            "--locator",
            citation["locator"],
            "--content-sha256",
            citation["content_sha256"],
        ]
    )
    assert evidence["text"] == "Cite exact evidence; preserve uncertainty."
    assert (
        garden / ".garden/knowledge" / (original_id + ".json")
    ).read_bytes() == canonical_json(original)
    assert (
        open_vault(LocalBindings.load(clean_config), "synthetic-vault").audit()[
            "status"
        ]
        == "verified"
    )
    for binding in clean_bindings["gardens"]:
        for record in (Path(binding["root"]) / ".garden").rglob("*.json"):
            assert str(workspace).encode() not in record.read_bytes()
    return {
        "schema": "mindgarden.pipeline-completion-proof/v1",
        "status": "passed",
        "engine_version": mindgarden.__version__,
        "baseline_proof_sha256": digest_bytes(canonical_json(baseline)),
        "archive_spec_version": "2.0.2",
        "producer": descriptor,
        "producer_units": len(inputs),
        "proposal_count": len(proposal["candidates"]),
        "resume": {
            "initial_new_calls": partial["new_calls"],
            "resumed_new_calls": resumed["new_calls"],
            "completed_unit_replay": 0,
        },
        "unresolved_proposals": "ambiguity-and-unknown-relations-retained",
        "review": "explicit-authored-human",
        "retrieved": entry["reference"],
        "source_reference": citation,
        "original_selector": evidence["origin"]["original_selector"],
        "attribution": entry["qualifications"]["attribution"],
        "context_sha256": digest_bytes(pack),
        "index_sha256": digest_bytes(canonical_json(index)),
        "graph_sha256": digest_bytes(graph),
        "context_bytes": len(pack),
        "context_max_bytes": 8192,
        "vault_backup_sha256": digest_bytes(original_bundle),
        "originals": "retained",
        "canonical_home": "single-moved-home",
        "local_catalog": "metadata-only-never-exportable",
        "recovery": "relocation-restore-clean-rebuild-exact",
        "network": "blocked-in-process",
        "google": "unused",
        "model": "unused",
    }


def run_demo(workspace):
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
        patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")),
        patch(
            "subprocess.run",
            side_effect=AssertionError("External process/model attempted"),
        ),
    ):
        return workflow(workspace.absolute())


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    if arguments.require_source and not engine.is_relative_to(ROOT / "src"):
        parser.error("Exact source engine required")
    if arguments.require_installed and (
        engine.is_relative_to(ROOT / "src")
        or not engine.is_relative_to(Path(sys.prefix).resolve())
    ):
        parser.error("Isolated installed engine required")
    report = run_demo(arguments.workspace)
    if report != read_object(FIXTURES / "extraction/pipeline-proof.json"):
        raise AssertionError("Combined synthetic pipeline proof differs")
    if arguments.report:
        with arguments.report.open("xb") as output:
            output.write(canonical_json(report))
    print(canonical_json(report).decode(), end="")


if __name__ == "__main__":
    main()
