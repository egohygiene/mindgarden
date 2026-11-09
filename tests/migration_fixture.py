"""Authored migration fixture and replaceable filesystem-backed content port."""

from pathlib import Path

from mindgarden.adapters.filesystem import FilesystemVault
from mindgarden.application.bindings import LocalBindings
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.storage import default_storage_adapters
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.scope import local_scope
from tests.support_v1 import (
    TIME,
    add_knowledge,
    create_garden,
    write_json,
    write_session,
)

FIXTURES = Path(__file__).parent / "fixtures/assets"


class SyntheticLocalPort:
    """Explicit extension over real files; not a new hosted provider implementation."""

    def __init__(self, binding, vault_id, fault=None):
        self.storage = FilesystemVault(binding["root"], vault_id)
        self.fault = fault

    def capabilities(self):
        return {
            **self.storage.capabilities(),
            "adapter": "synthetic-local",
            "relocate": False,
        }

    def state(self, identity):
        return self.storage.state(identity)

    def get(self, identity):
        return self.storage.get(identity)

    def put(self, content):
        if self.fault is not None:
            self.fault["calls"] += 1
            if self.fault.get("armed") and self.fault["calls"] == 2:
                raise RuntimeError(
                    "Synthetic provider failure; private detail must not be echoed"
                )
        return self.storage.put(content)

    def audit(self, expected=None):
        return self.storage.audit(expected)

    def export_bundle(self):
        return self.storage.export_bundle()

    def restore_bundle(self, content, digest):
        return self.storage.restore_bundle(content, digest)


def create_fixture(root, *, adapter="filesystem", fault=None):
    root.mkdir(mode=0o700, parents=True)
    workspace = root / "garden"
    create_garden(workspace)
    configuration = root / "bindings.json"
    target_configuration = root / "target-bindings.json"
    vault = FilesystemVault(root / "source-vault", "synthetic-vault")
    target = FilesystemVault(root / "target-vault", "synthetic-vault")
    original = {
        "schema": "mindgarden.local-bindings/v1",
        "gardens": [
            {"id": "synthetic-garden", "root": str(workspace), "scope": local_scope()}
        ],
        "vaults": [
            {"id": "synthetic-vault", "adapter": "filesystem", "root": str(vault.root)}
        ],
        "revoked_sessions": [],
    }
    write_json(configuration, original)
    configuration.chmod(0o600)
    write_json(
        target_configuration,
        {
            "schema": "mindgarden.local-bindings/v1",
            "gardens": [],
            "vaults": [
                {"id": "synthetic-vault", "adapter": adapter, "root": str(target.root)}
            ],
            "revoked_sessions": [],
        },
    )
    target_configuration.chmod(0o600)
    for store, path in ((vault, configuration), (target, target_configuration)):
        plan = store.plan_init(digest_bytes(path.read_bytes()))
        store.initialize(plan, plan["plan_sha256"])
    bindings = LocalBindings.load(configuration)
    source = root / "captured.txt"
    source.write_bytes((FIXTURES / "migration-source.txt").read_bytes())
    plan = build_ingestion_plan(
        bindings,
        "synthetic-garden",
        "synthetic-vault",
        source,
        {
            "source_id": "migration-source",
            "title": "Synthetic migration prompt",
            "origin": "urn:synthetic:migration",
            "owner": "synthetic-owner",
            "rights": "Synthetic fixture only.",
            "captured_at": TIME,
            "media_type": "text/plain",
        },
    )
    apply_ingestion(plan, plan.digest, bindings, "synthetic-vault")
    evidence = plan.inputs["normalized_sources"][0]["evidence"]
    add_knowledge(workspace, sources=evidence)
    vault.put(b"An unreferenced synthetic original must also be retained.\n")
    session_path = root / "session.json"
    write_session(session_path, configuration)
    adapters = default_storage_adapters()
    adapters.register(
        "synthetic-local",
        lambda binding, identity: SyntheticLocalPort(binding, identity, fault),
    )
    return {
        "root": root,
        "workspace": workspace,
        "configuration": configuration,
        "target_configuration": target_configuration,
        "vault": vault,
        "target": target,
        "bindings": bindings,
        "session_path": session_path,
        "evidence": evidence,
        "adapters": adapters,
        "original_configuration": original,
    }
