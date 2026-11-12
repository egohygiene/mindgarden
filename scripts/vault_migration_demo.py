#!/usr/bin/env python3
"""Prove private adapter migration, interruption/retry, removal and clean restore."""

from argparse import ArgumentParser
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

from mindgarden.adapters.filesystem import FilesystemVault
from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index, render_context, search_payload
from mindgarden.application.vault_migration import build_vault_migration_plan
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.validation import ContractError

sys.path.insert(0, str(ROOT))
from tests.migration_fixture import create_fixture
from tests.support_v1 import write_json


def projections(fixture, adapters=None, configuration=None):
    context = QueryContext.load(
        configuration or fixture["configuration"],
        fixture["session_path"],
        storage_adapters=adapters,
    )
    profile = json.loads(
        (fixture["workspace"] / ".garden/context-packs/default.json").read_bytes()
    )
    return (
        canonical_json(build_index(context)),
        render_context(context, profile, "json"),
        search_payload(context, "prompt"),
    )


def workflow(root):
    fault = {"calls": 0, "armed": True}
    fixture = create_fixture(root, adapter="synthetic-local", fault=fault)
    adapters = fixture["adapters"]
    before = projections(fixture)
    source_bundle = fixture["vault"].export_bundle()
    garden = garden_fingerprint(fixture["workspace"])
    bindings_before = fixture["configuration"].read_bytes()
    plan = build_vault_migration_plan(
        fixture["bindings"],
        fixture["target_configuration"],
        "synthetic-vault",
        adapters=adapters,
    )
    try:
        plan.apply(plan.digest)
    except ContractError as error:
        assert str(error).startswith("VAULT_MIGRATION_UNAVAILABLE:")
    else:
        raise AssertionError("Synthetic failure was not exercised")
    assert fixture["configuration"].read_bytes() == bindings_before
    assert len(fixture["target"].audit()["objects"]) == 1
    resumed = build_vault_migration_plan(
        LocalBindings.load(fixture["configuration"]),
        fixture["target_configuration"],
        "synthetic-vault",
        adapters=adapters,
    )
    assert resumed.digest == plan.digest
    fault["armed"] = False
    assert resumed.apply(plan.digest)
    assert not resumed.apply(plan.digest)
    assert projections(fixture, adapters) == before
    assert fixture["target"].export_bundle() == source_bundle
    assert fixture["vault"].export_bundle() == source_bundle
    assert garden_fingerprint(fixture["workspace"]) == garden
    original_configuration = root / "original-target.json"
    original = {**fixture["original_configuration"], "gardens": []}
    write_json(original_configuration, original)
    original_configuration.chmod(0o600)
    reverse = build_vault_migration_plan(
        LocalBindings.load(fixture["configuration"]),
        original_configuration,
        "synthetic-vault",
        adapters=adapters,
    )
    assert reverse.apply(reverse.digest)
    adapters.remove("synthetic-local")
    assert not reverse.apply(reverse.digest)
    assert projections(fixture) == before
    restored = FilesystemVault(root / "clean-restored-vault", "synthetic-vault")
    assert restored.restore_bundle(source_bundle, digest_bytes(source_bundle))
    restored_configuration = {
        **fixture["original_configuration"],
        "vaults": [
            {
                "id": "synthetic-vault",
                "adapter": "filesystem",
                "root": str(restored.root),
            }
        ],
    }
    restored_path = root / "restored-bindings.json"
    write_json(restored_path, restored_configuration)
    restored_path.chmod(0o600)
    assert projections(fixture, configuration=restored_path) == before
    assert restored.export_bundle() == source_bundle
    citation = before[2]["results"][0]["sources"][0]
    return {
        "schema": "mindgarden.vault-migration-proof/v1",
        "status": "passed",
        "adapter": "synthetic-local-filesystem-port",
        "source_retained": True,
        "vault_identity": "synthetic-vault",
        "copied_objects": len(plan.document()["objects"]),
        "partial_failure": "bindings-unchanged",
        "retry": "same-reviewed-digest",
        "verification": "independent-reopen-and-core-checksums",
        "adapter_removed_after_return": True,
        "index_sha256": digest_bytes(before[0]),
        "context_sha256": digest_bytes(before[1]),
        "source_reference": citation,
        "clean_restore": "exact-projections-and-backup",
        "original_backup_sha256": digest_bytes(source_bundle),
        "network": "blocked-in-process",
        "google": "unused",
        "model": "unused",
        "full_parent_acceptance": False,
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args()
    module = Path(mindgarden.__file__).resolve()
    if arguments.require_source and not module.is_relative_to(ROOT / "src"):
        parser.error("Source engine required")
    if arguments.require_installed and not module.is_relative_to(
        Path(sys.prefix).resolve()
    ):
        parser.error("Isolated installed engine required")
    if arguments.workspace.exists():
        parser.error("Select a new synthetic workspace; existing content is preserved")
    with (
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
        patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")),
        patch(
            "subprocess.Popen", side_effect=AssertionError("External process attempted")
        ),
    ):
        report = workflow(arguments.workspace.absolute())
    content = canonical_json(report)
    if arguments.report is not None:
        arguments.report.write_bytes(content)
    print(content.decode(), end="")


if __name__ == "__main__":
    main()
