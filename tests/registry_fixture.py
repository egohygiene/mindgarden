"""Synthetic public/personal roots and a private-to-public reference for #30."""

from copy import deepcopy
import json
from pathlib import Path

from mindgarden.adapters.registry_files import create_control
from mindgarden.application.registry import apply_registry_plan, build_registry_plan
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.scope import local_scope
from tests.federation_fixture import create_fixture as create_public_fixture
from tests.support_v1 import FIXTURES, add_knowledge, create_garden, reference, write_json


def create_roots(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    public = create_public_fixture(root / "public", "repository-garden")
    personal_root = root / "personal"
    garden = create_garden(personal_root, "personal-garden")
    note = add_knowledge(personal_root, "personal-prompt", body="personal-content-canary: Keep exact evidence in personal notes.\n")
    edge = json.loads((FIXTURES / "synapse.json").read_text())
    edge.update(id="personal-public-reference", garden="personal-garden", type="related", directed=True,
                source=reference("personal-garden", note["id"]), target=reference("repository-garden", "reviewed-prompt"),
                visibility="private", status="active", review=deepcopy(note["review"]), evidence=public["evidence"])
    write_json(garden / "synapses/personal-public-reference.json", edge)
    vault = root / "source-vault"
    vault.mkdir()
    (vault / "original.txt").write_bytes((Path(__file__).parent / "fixtures/registry/source.txt").read_bytes())
    return {"public": public, "personal_root": personal_root, "vault_root": vault,
            "vaults": [{"id": "synthetic-source-vault", "root": str(vault), "adapter": "filesystem"}],
            "bindings": [{"id": "repository-garden", "root": str(public["workspace"]), "scope": local_scope("public", publication="publishable")},
                         {"id": "personal-garden", "root": str(personal_root), "scope": local_scope()}]}


def mutate(registry: Path, operation: str, request: dict) -> dict:
    plan = build_registry_plan(registry, operation, request)
    apply_registry_plan(registry, plan.document(), plan.document()["plan_sha256"])
    return plan.document()


def register_roots(registry: Path, fixture: dict) -> None:
    create_control(registry, canonical_json({"schema": "mindgarden.local-bindings/v1", "gardens": [],
                                            "vaults": fixture["vaults"], "revoked_sessions": []}))
    mutate(registry, "init", {})
    for binding in fixture["bindings"]:
        mutate(registry, "register", {"root": binding["root"], "scope": binding["scope"],
                                     "expected_garden": binding["id"], "expected_owners": []})
    mutate(registry, "set-view", {"id": "private-view-canary", "gardens": [binding["id"] for binding in fixture["bindings"]]})
