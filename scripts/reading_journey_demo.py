#!/usr/bin/env python3
"""Synthetic archive, reviewed context, private routing and clean vault recovery."""

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
from mindgarden.application.curation import build_curation_plan
from mindgarden.application.federation import build_catalog
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.public_bundle_context import public_bundle_context
from mindgarden.application.site import build_site
from mindgarden.application.storage import open_vault
from mindgarden.domain.contracts import (
    canonical_json,
    digest_bytes,
    read_object,
    safe_path,
)
from mindgarden.domain.scope import local_scope
from mindgarden.domain.site import QUARTZ_COMMIT, QUARTZ_REPOSITORY
from mindgarden.domain.validation import ContractError

sys.path.insert(0, str(ROOT / "scripts"))
from private_garden_demo import TIME, cli, cli_json, reviewed_apply, write_json


def initialize(root, identity, kind):
    root.mkdir(mode=0o700)
    args = [
        "init",
        "--repository-root",
        str(root),
        "--visibility",
        "private",
        "--kind",
        kind,
        "--garden-id",
        identity,
        "--title",
        "Synthetic journey garden",
        "--owner",
        "synthetic-owner",
        "--canonical-uri",
        "urn:mindgarden:garden:" + identity,
        "--domain",
        "knowledge-systems",
        "--topic",
        "prompt-bank",
    ]
    plan = cli_json(args)
    cli(args + ["--apply", "--plan-digest", plan["plan_sha256"]])


def private_outputs(configuration, session, garden):
    shared = [
        "--repository-root",
        str(garden),
        "--local-config",
        str(configuration),
        "--scope",
        str(session),
    ]
    index = cli_json(["index", *shared, "--write"])
    cli_json(["index", *shared, "--check"])
    graph = cli_json(["graph", *shared])
    context = cli(
        ["context", *shared, "--pack", "default", "--format", "json"]
    ).encode()
    return canonical_json(index), canonical_json(graph), context


def public_slice(root):
    # Data recipes only. In installed verification mode no source engine path is added.
    sys.path.insert(0, str(ROOT))
    from tests.federation_fixture import create_fixture

    fixture = create_fixture(root)
    bundle = fixture["bundle"]
    plan = bundle.plan(fixture["context"], fixture["export"])
    bundle.apply(fixture["context"], fixture["export"], plan["plan_sha256"])
    directory = fixture["export"] / bundle.output_root
    revision = bundle.descriptor["revision"]
    catalog = build_catalog(
        {
            "schema": "mindgarden.federation-catalog-request/v1",
            "bundles": [{"directory": str(directory), "expected_revision": revision}],
        }
    )
    request = {
        "schema": "mindgarden.federation-context-request/v1",
        "id": "synthetic-public-context",
        "catalog": catalog,
        "bundles": [
            {
                "garden": bundle.garden,
                "directory": str(directory),
                "expected_revision": revision,
            }
        ],
        "query": "evidence",
        "max_items": 3,
        "max_bytes": 8192,
    }
    packet = public_bundle_context(fixture["context"], request)
    assert json.loads(packet)["included"]
    profile = deepcopy(fixture["profile"])
    profile.update(kind="site", id="synthetic-reading-site", output_root="garden")
    profile["x-site"] = {
        "schema": "mindgarden.site-adapter/v1",
        "renderer": "quartz-v5",
        "repository": QUARTZ_REPOSITORY,
        "commit": QUARTZ_COMMIT,
        "node_major": 24,
        "title": "Synthetic reading garden",
        "description": "Reviewed synthetic evidence.",
    }
    site = build_site(fixture["context"], profile)
    assert b"Exact evidence" in site.files["notes/reviewed-prompt/index.md"]
    prompt = next(
        item["record"]
        for item in json.loads(packet)["included"]
        if item["record"]["reference"]["id"] == "reviewed-prompt"
    )
    assert prompt["sources"] == fixture["evidence"]
    assert prompt["canonical_url"] in [
        route["url"] for route in site.manifest["routes"]
    ]
    return {
        "descriptor_revision": revision,
        "context_sha256": digest_bytes(packet),
        "context_bytes": len(packet),
        "site_revision": site.manifest["revision"],
        "canonical_reference": prompt["reference"],
        "source_reference": prompt["sources"][0],
        "rendering": "static-projection-only; actual browser proof is separately recorded",
    }


def workflow(workspace):
    workspace = workspace.absolute()
    if any(path.is_symlink() for path in (workspace, *workspace.parents)) or (
        workspace.exists() and any(workspace.iterdir())
    ):
        raise ValueError("Synthetic journey requires a new or empty ordinary workspace")
    workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
    workspace.chmod(0o700)
    garden, project = workspace / "garden", workspace / "project"
    initialize(garden, "synthetic-garden", "personal")
    initialize(project, "project-garden", "repository")
    configuration = workspace / "bindings.json"
    source_root = workspace / "source-vault"
    document = {
        "schema": "mindgarden.local-bindings/v1",
        "gardens": [
            {"id": identity, "root": str(root), "scope": local_scope()}
            for identity, root in (
                ("synthetic-garden", garden),
                ("project-garden", project),
            )
        ],
        "vaults": [
            {"id": "synthetic-vault", "adapter": "filesystem", "root": str(source_root)}
        ],
        "revoked_sessions": [],
    }
    write_json(configuration, document)
    reviewed_apply(
        [
            "vault",
            "init",
            "--local-config",
            str(configuration),
            "--vault-id",
            "synthetic-vault",
        ]
    )
    bindings = LocalBindings.load(configuration)
    original_vault = open_vault(bindings, "synthetic-vault")
    sys.path.insert(0, str(ROOT))
    from tests.archive_fixture import package_bytes
    from tests.journey_fixture import curation_members, mixed_proposal

    members = curation_members()
    original = package_bytes(members)
    archive = workspace / "synthetic-archive.zip"
    archive.write_bytes(original)
    archive.chmod(0o600)
    metadata = {
        "source_id": "synthetic-archive",
        "title": "Synthetic conversation archive",
        "owner": "synthetic-owner",
        "origin": "urn:synthetic:conversation",
        "captured_at": TIME,
        "rights": "Authored synthetic fixtures only.",
        "media_type": "application/zip",
        "attachment_selection": {"mode": "selected", "asset_ids": ["asset-diagram"]},
    }

    def import_plan():
        return build_ingestion_plan(
            bindings,
            "synthetic-garden",
            "synthetic-vault",
            archive,
            metadata,
            adapter_id="conversation-archive",
            manifest_version="2.0.2",
        )

    imported = import_plan()
    archive.write_bytes(original + b"changed")
    try:
        apply_ingestion(imported, imported.digest, bindings, "synthetic-vault")
    except ContractError as error:
        assert str(error).startswith("PLAN_STALE:")
    else:
        raise AssertionError("Changed input did not invalidate the reviewed import")
    assert original_vault.audit()["objects"] == []
    archive.write_bytes(original)
    assert apply_ingestion(imported, imported.digest, bindings, "synthetic-vault")
    again = import_plan()
    assert not apply_ingestion(again, again.digest, bindings, "synthetic-vault")
    manifest = json.loads(members["ARCHIVE-MANIFEST.json"])
    manifest["archive_revision"] = 2
    members["ARCHIVE-MANIFEST.json"] = canonical_json(manifest)
    overlapping = package_bytes(members)
    archive.write_bytes(overlapping)
    overlap_plan = import_plan()
    assert [item["source"] for item in overlap_plan.inputs["normalized_sources"]] == [
        item["source"] for item in imported.inputs["normalized_sources"]
    ]
    assert apply_ingestion(
        overlap_plan, overlap_plan.digest, bindings, "synthetic-vault"
    )

    proposal = mixed_proposal(imported)
    diagram = next(
        c["output"]
        for c in proposal["candidates"]
        if c.get("output", {}).get("id") == "diagram-proposal"
    )
    prompt = next(
        c["output"]
        for c in proposal["candidates"]
        if c.get("output", {}).get("id") == "reviewed-prompt"
    )
    diagram_ref = {
        "garden": "synthetic-garden",
        "id": diagram["id"],
        "revision": "sha256:" + digest_bytes(diagram["body"].encode()),
    }
    prompt["synapses"] = [
        {
            "id": "incoming-diagram-reference",
            "type": "references",
            "target": diagram_ref,
            "directed": True,
            "review": prompt["review"],
            "rationale": "Reviewed reference to the assistant's architecture proposal.",
        }
    ]
    proposal_path = workspace / "curation.json"
    write_json(proposal_path, proposal)
    candidate = build_curation_plan(bindings, proposal_path)
    assert "reviewed-prompt" in json.dumps(candidate.inputs)
    preview = cli_json(
        [
            "gardenize",
            "--local-config",
            str(configuration),
            "--plan",
            str(proposal_path),
        ]
    )
    assert cli_json(
        [
            "gardenize",
            "--local-config",
            str(configuration),
            "--apply",
            str(proposal_path),
            "--plan-digest",
            preview["plan_sha256"],
        ]
    )["applied"]
    move = {
        "schema": "mindgarden.routing-transition/v1",
        "id": "diagram-private-home",
        "operation": "move",
        "created_at": TIME,
        "from": [diagram_ref],
        "to": {
            "garden": "project-garden",
            "id": "architecture-diagram",
            "revision": None,
        },
        "review": diagram["review"],
        "authority": proposal["review_authority"],
        "rationale": "Reviewed diagram home; prompt remains personal.",
    }
    move_path = workspace / "move.json"
    write_json(move_path, move)
    moved = reviewed_apply(
        ["route", "--local-config", str(configuration), "--transition", str(move_path)]
    )
    (incoming,) = moved["decisions"][0]["incoming_references"]
    repair = {
        "schema": "mindgarden.reference-repair/v1",
        "id": "diagram-reference-review",
        "created_at": TIME,
        "review": prompt["review"],
        "authority": proposal["review_authority"],
        "repairs": [
            {
                "edge": incoming["reference"],
                "source": incoming["source"],
                "historical_target": incoming["historical_target"],
                "canonical_target": incoming["proposed_canonical_target"],
                "replacement_id": "current-diagram-reference",
                "rationale": "Independent human review follows this exact private canonical successor.",
            }
        ],
    }
    repair_path = workspace / "repair.json"
    write_json(repair_path, repair)
    reviewed_apply(
        [
            "route",
            "--local-config",
            str(configuration),
            "--reference-repair",
            str(repair_path),
        ]
    )
    pack_path = garden / ".garden/context-packs/default.json"
    profile = read_object(pack_path)
    profile.update(query="evidence", max_bytes=8192)
    write_json(pack_path, profile)
    session = workspace / "session.json"
    cli(
        [
            "scope",
            "--local-config",
            str(configuration),
            "--session-id",
            "synthetic-reading-session",
            "--readable-garden",
            "synthetic-garden",
            "--readable-garden",
            "project-garden",
            "--writable-garden",
            "synthetic-garden",
            "--allowed-visibility",
            "personal",
            "--expires-at",
            "2099-01-01T00:00:00Z",
            "--output",
            str(session),
        ]
    )
    shared = [
        "--repository-root",
        str(garden),
        "--local-config",
        str(configuration),
        "--scope",
        str(session),
    ]
    results = cli_json(["search", *shared, "--query", "evidence"])
    entry = next(
        item
        for item in results["results"]
        if item["reference"]["id"] == "reviewed-prompt"
    )
    expected_text = "Cite exact evidence; preserve uncertainty."
    citation = next(
        item
        for item in entry["sources"]
        if item["content_sha256"] == digest_bytes(expected_text.encode())
    )
    evidence_args = [
        "evidence",
        "--scope",
        str(session),
        "--garden-id",
        citation["source"]["garden"],
        "--source-id",
        citation["source"]["id"],
        "--revision",
        citation["source"]["revision"],
        "--locator",
        citation["locator"],
        "--content-sha256",
        citation["content_sha256"],
    ]
    evidence = cli_json([*evidence_args, "--local-config", str(configuration)])
    assert (
        evidence["text"] == expected_text
        and evidence["source_review"]["state"] == "unreviewed"
    )
    assert evidence["origin"]["speaker"] == "assistant"
    assert evidence["origin"]["original_selector"]["json_pointer"] == "/messages/1"
    before = private_outputs(configuration, session, garden)
    markdown = cli(["context", *shared, "--pack", "default", "--format", "markdown"])
    assert len(markdown.encode()) <= 8192 and "ACCOUNT-EXAMPLE" not in markdown
    context = json.loads(before[2])
    assert any(item["reference"] == entry["reference"] for item in context["included"])
    assert len(before[2]) <= 8192 and b"ACCOUNT-EXAMPLE" not in before[2]
    assert b"open-question" not in before[2]
    assert any(
        edge["target"] == "project-garden/architecture-diagram"
        for edge in json.loads(before[1])["edges"]
    )
    for root in (garden, project):
        assert (
            cli_json(
                [
                    "validate",
                    "--repository-root",
                    str(root),
                    "--local-config",
                    str(configuration),
                    "--format",
                    "json",
                ]
            )["status"]
            == "valid"
        )
    backup_bytes = original_vault.export_bundle()
    all_blobs = [
        original_vault.get(item["content_id"])
        for item in original_vault.audit()["objects"]
    ]
    assert original in all_blobs and overlapping in all_blobs
    assert (
        members["assets/diagram.png"] in all_blobs
        and members["assets/scratch.png"] not in all_blobs
    )
    target_root = workspace / "migrated-vault"
    target_document = deepcopy(document)
    target_document["gardens"] = []
    target_document["vaults"][0]["root"] = str(target_root)
    target_config = workspace / "target-bindings.json"
    write_json(target_config, target_document)
    reviewed_apply(
        [
            "vault",
            "init",
            "--local-config",
            str(target_config),
            "--vault-id",
            "synthetic-vault",
        ]
    )
    reviewed_apply(
        [
            "vault",
            "migrate",
            "--local-config",
            str(configuration),
            "--vault-id",
            "synthetic-vault",
            "--target-local-config",
            str(target_config),
        ]
    )
    assert private_outputs(configuration, session, garden) == before
    assert original_vault.export_bundle() == backup_bytes
    assert (
        open_vault(LocalBindings.load(configuration), "synthetic-vault").export_bundle()
        == backup_bytes
    )
    migrated_vault = open_vault(LocalBindings.load(configuration), "synthetic-vault")
    relocated = workspace / "relocated-vault"
    reviewed_apply(
        [
            "vault",
            "relocate",
            "--local-config",
            str(configuration),
            "--vault-id",
            "synthetic-vault",
            "--destination",
            str(relocated),
        ]
    )
    assert private_outputs(configuration, session, garden) == before
    assert migrated_vault.export_bundle() == backup_bytes
    backup = workspace / "backup.zip"
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
    restored = workspace / "restored-vault"
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
    clean = workspace / "clean"
    clean.mkdir(mode=0o700)
    clean_document = read_object(configuration)
    for binding in clean_document["gardens"]:
        source = Path(binding["root"])
        destination = clean / binding["id"]
        destination.mkdir(mode=0o700)
        shutil.copytree(source / ".garden", destination / ".garden")
        for generated in read_object(destination / ".garden/garden.json")["roots"][
            "generated"
        ]:
            path = safe_path(destination / ".garden", generated)
            if path.exists():
                shutil.rmtree(path)
        binding["root"] = str(destination)
        for path in (destination / ".garden").rglob("*.json"):
            assert str(workspace).encode() not in path.read_bytes()
    clean_document["vaults"][0]["root"] = str(restored)
    clean_config = clean / "bindings.json"
    write_json(clean_config, clean_document)
    assert private_outputs(clean_config, session, clean / "synthetic-garden") == before
    clean_shared = [
        "--repository-root",
        str(clean / "synthetic-garden"),
        "--local-config",
        str(clean_config),
        "--scope",
        str(session),
    ]
    assert (
        cli(["context", *clean_shared, "--pack", "default", "--format", "markdown"])
        == markdown
    )
    assert cli_json([*evidence_args, "--local-config", str(clean_config)]) == evidence
    public = public_slice(workspace / "public-slice")
    return {
        "schema": "mindgarden.reading-journey-proof/v1",
        "status": "passed-bounded-synthetic-journey",
        "engine_version": mindgarden.__version__,
        "archive_version": "2.0.2-source-profile",
        "reviewed_prompt": entry["reference"],
        "knowledge_review": entry["review"]["state"],
        "attribution": entry["qualifications"]["attribution"],
        "epistemic_state": entry["qualifications"]["epistemic_state"],
        "source_reference": citation,
        "original_selector": evidence["origin"]["original_selector"],
        "source_review": "unreviewed",
        "selected_asset": "asset-diagram",
        "excluded_asset": "asset-scratch",
        "original_archive_sha256": digest_bytes(original),
        "overlapping_archive_sha256": digest_bytes(overlapping),
        "vault_objects": len(all_blobs),
        "vault_backup_sha256": digest_bytes(backup_bytes),
        "index_sha256": digest_bytes(before[0]),
        "graph_sha256": digest_bytes(before[1]),
        "context_sha256": digest_bytes(before[2]),
        "context_bytes": len(before[2]),
        "context_max_bytes": 8192,
        "context_markdown_sha256": digest_bytes(markdown.encode()),
        "context_markdown_bytes": len(markdown.encode()),
        "private_diagram_home": incoming["proposed_canonical_target"],
        "public_reference_slice": public,
        "checks": [
            "private-cli-init-validation",
            "stale-import-rejected-before-writes",
            "repeat-and-overlap-deduplication",
            "selected-binary-caption-and-retained-scratch-original",
            "authored-human-review-and-attribution",
            "reviewed-private-move-and-independent-reference-repair",
            "exact-search-evidence-and-bounded-context",
            "initialized-vault-migration-with-original-retained",
            "filesystem-relocation-with-old-location-retained",
            "export-restore-clean-rebuild-exact",
            "supplied-public-bundle-context-and-static-reading-projection",
            "no-physical-paths-in-records",
        ],
        "network": "blocked-in-process",
        "models": "unused",
        "google": "unused",
        "real_private_pilot": "unclaimed",
        "empathy_publication": "unclaimed",
        "full_parent_acceptance": False,
    }


def run_demo(workspace):
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
        patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")),
        patch(
            "subprocess.run",
            side_effect=AssertionError("External provider or model process attempted"),
        ),
    ):
        return workflow(workspace)


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
        parser.error("Require the engine from this source checkout")
    if args.require_installed and (
        engine.is_relative_to(ROOT / "src")
        or not engine.is_relative_to(Path(sys.prefix).resolve())
    ):
        parser.error("Require an installed engine in a clean interpreter")
    report = run_demo(args.workspace)
    if args.check_golden:
        assert report == read_object(
            ROOT / "tests/fixtures/conversation-archives/reading-journey-proof.json"
        )
    output = canonical_json(report)
    if args.report:
        with args.report.open("xb") as stream:
            stream.write(output)
    sys.stdout.write(output.decode())


if __name__ == "__main__":
    main()
