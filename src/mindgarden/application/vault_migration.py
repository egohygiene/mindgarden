"""Reviewed local copy/verify/rebind over explicit initialized content adapters."""

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from ..adapters.registry_files import (
    control_path,
    read_control,
    registry_writer,
    replace_registry,
)
from ..adapters.vault_bundle import MAX_OBJECT_BYTES, MAX_OBJECTS, MAX_PAYLOAD_BYTES
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    strict_json,
)
from ..domain.storage import ContentState, content_digest
from ..domain.validation import ContractError
from .bindings import LocalBindings, garden_fingerprint
from .storage import default_storage_adapters, open_vault
from .vault_recovery import destination_path, referenced_content


def provider_call(storage, method, *arguments):
    try:
        return getattr(storage, method)(*arguments)
    except Exception as error:
        raise ContractError(
            "VAULT_MIGRATION_UNAVAILABLE: selected content adapter could not complete the operation"
        ) from error


def checked_state(storage, identity):
    try:
        return ContentState(provider_call(storage, "state", identity))
    except (ValueError, TypeError) as error:
        raise ContractError(
            "VAULT_MIGRATION_UNSUPPORTED: adapter returned an unsupported content state"
        ) from error


def state_failure(state):
    code = {
        ContentState.MISSING: "MISSING",
        ContentState.CORRUPTED: "CORRUPTED",
        ContentState.UNAVAILABLE: "UNAVAILABLE",
        ContentState.UNSUPPORTED: "UNSUPPORTED",
    }.get(state, "INTEGRITY")
    raise ContractError(
        "VAULT_MIGRATION_"
        + code
        + ": verified local content is required; retain both stores"
    )


def verified_bytes(storage, identity, size=None):
    state = checked_state(storage, identity)
    if state != ContentState.AVAILABLE:
        state_failure(state)
    content = provider_call(storage, "get", identity)
    if (
        not isinstance(content, bytes)
        or len(content) > MAX_OBJECT_BYTES
        or digest_bytes(content) != content_digest(identity)
        or size is not None
        and len(content) != size
    ):
        raise ContractError(
            "VAULT_MIGRATION_CORRUPTED: returned bytes differ from their immutable identity"
        )
    return content


def inventory(storage, vault_id, references):
    audit = provider_call(storage, "audit", references)
    if (
        not isinstance(audit, dict)
        or audit.get("vault") != vault_id
        or not isinstance(audit.get("objects"), list)
        or len(audit["objects"]) > MAX_OBJECTS
    ):
        raise ContractError(
            "VAULT_MIGRATION_INTEGRITY: complete bounded source inventory is unavailable"
        )
    identities = set()
    for item in audit["objects"]:
        if not isinstance(item, dict) or not isinstance(item.get("content_id"), str):
            raise ContractError(
                "VAULT_MIGRATION_INTEGRITY: source inventory contains unsupported members"
            )
        identity = item["content_id"]
        content_digest(identity)
        if identity in identities:
            raise ContractError(
                "VAULT_MIGRATION_INTEGRITY: source inventory contains duplicate identities"
            )
        if item.get("state") != "available":
            try:
                state_failure(ContentState(item.get("state")))
            except (ValueError, TypeError) as error:
                raise ContractError(
                    "VAULT_MIGRATION_UNSUPPORTED: source inventory state is unsupported"
                ) from error
        identities.add(identity)
    if audit.get("status") != "verified" or not references <= identities:
        raise ContractError(
            "VAULT_MIGRATION_INTEGRITY: source inventory does not cover the supplied gardens"
        )
    objects, total = [], 0
    for identity in sorted(identities):
        content = verified_bytes(storage, identity)
        total += len(content)
        if total > MAX_PAYLOAD_BYTES:
            raise ContractError(
                "VAULT_MIGRATION_BUDGET: source inventory exceeds the local migration bound"
            )
        objects.append({"content_id": identity, "size_bytes": len(content)})
    return objects


def open_checked(bindings, vault_id, adapters, expected=None, *, source=False):
    try:
        storage = open_vault(bindings, vault_id, adapters=adapters)
        capabilities = storage.capabilities()
    except Exception as error:
        raise ContractError(
            "VAULT_MIGRATION_UNAVAILABLE: explicit adapter is absent or cannot be verified"
        ) from error
    if expected is not None and digest_bytes(canonical_json(capabilities)) != expected:
        raise ContractError(
            "VAULT_MIGRATION_STALE: selected adapter capabilities changed"
        )
    if capabilities["encryption"] or capabilities["remote"]:
        raise ContractError(
            "RUNTIME_UNVERIFIED: this migration proves ordinary local storage only"
        )
    if (
        not capabilities["read"]
        or not capabilities["audit" if source else "immutable_put"]
    ):
        raise ContractError(
            "VAULT_MIGRATION_UNSUPPORTED: selected adapter lacks the required content capabilities"
        )
    return storage, capabilities


def target_has(storage, item):
    state = checked_state(storage, item["content_id"])
    if state == ContentState.MISSING:
        return False
    if state != ContentState.AVAILABLE:
        state_failure(state)
    verified_bytes(storage, item["content_id"], item["size_bytes"])
    return True


@dataclass(frozen=True)
class VaultMigrationPlan:
    source: LocalBindings
    target: LocalBindings
    adapters: object
    _payload: dict
    _rebound: bytes

    @property
    def digest(self):
        return digest_bytes(canonical_json(self._payload))

    def document(self):
        return {**deepcopy(self._payload), "plan_sha256": self.digest}

    def check_controls(self):
        control_path(
            self.target.vault(self._payload["vault"])["root"]
            / ".mindgarden-migration-control"
        )
        if (
            digest_bytes(read_control(self.target.path))
            != self._payload["target_configuration_sha256"]
        ):
            raise ContractError(
                "VAULT_MIGRATION_STALE: explicit target configuration changed"
            )
        current = read_control(self.source.path)
        for item in self._payload["garden_revisions"]:
            root = self.source.garden(item["garden"])["root"]
            if (root / ".mindgarden-write.lock").exists() or garden_fingerprint(
                root
            ) != item["revision"]:
                raise ContractError(
                    "VAULT_MIGRATION_STALE: represented garden inputs changed or require write recovery"
                )
        if current == self._rebound:
            return True
        control_path(
            self.source.vault(self._payload["vault"])["root"]
            / ".mindgarden-migration-control"
        )
        if digest_bytes(current) != self._payload["source_configuration_sha256"]:
            raise ContractError("VAULT_MIGRATION_STALE: source configuration changed")
        return False

    def checked_target(self):
        return open_checked(
            self.target,
            self._payload["vault"],
            self.adapters,
            self._payload["target_capabilities_sha256"],
        )[0]

    def verify_target(self):
        # Reopen through the factory rather than trusting a write handle's cache.
        target = self.checked_target()
        for item in self._payload["objects"]:
            if not target_has(target, item):
                state_failure(ContentState.MISSING)

    def apply(self, reviewed_digest):
        if reviewed_digest != self.digest:
            raise ContractError(
                "PLAN_STALE: review the exact migration inputs, capabilities and inventory"
            )
        with registry_writer(self.source.path):
            if self.check_controls():
                self.verify_target()
                return False
            source, _ = open_checked(
                self.source,
                self._payload["vault"],
                self.adapters,
                self._payload["source_capabilities_sha256"],
                source=True,
            )
            references = referenced_content(self.source, self._payload["vault"])
            if (
                inventory(source, self._payload["vault"], references)
                != self._payload["objects"]
            ):
                raise ContractError(
                    "VAULT_MIGRATION_STALE: complete source inventory changed"
                )
            target = self.checked_target()
            # Check pre-existing objects before making any new target writes.
            for item in self._payload["objects"]:
                target_has(target, item)
            for item in self._payload["objects"]:
                self.check_controls()
                if not target_has(target, item):
                    content = verified_bytes(
                        source, item["content_id"], item["size_bytes"]
                    )
                    if provider_call(target, "put", content) != item["content_id"]:
                        raise ContractError(
                            "VAULT_MIGRATION_CORRUPTED: adapter returned a different immutable identity"
                        )
                    verified_bytes(target, item["content_id"], item["size_bytes"])
            self.verify_target()
            if (
                inventory(source, self._payload["vault"], references)
                != self._payload["objects"]
            ):
                raise ContractError(
                    "VAULT_MIGRATION_STALE: source changed while copying; retain both stores"
                )
            self.check_controls()
            try:
                replace_registry(
                    self.source.path,
                    self._rebound,
                    expected_sha256=self._payload["source_configuration_sha256"],
                    verify_inputs=lambda: (self.check_controls(), self.verify_target()),
                )
            except OSError as error:
                raise ContractError(
                    "VAULT_MIGRATION_COMMIT_UNCERTAIN: inspect bindings and retry the exact reviewed plan"
                ) from error
            return True


def build_vault_migration_plan(
    bindings, target_config: Path, vault_id, *, adapters=None
):
    if any(
        item["scope"]["persistence"] == "encrypted-vault"
        or item["scope"]["visibility"] == "restricted"
        for item in bindings.gardens.values()
    ):
        raise ContractError(
            "RUNTIME_UNVERIFIED: configured restricted inputs need unavailable runtime assurance"
        )
    source_bytes = read_control(bindings.path)
    if strict_json(source_bytes) != bindings.document:
        raise ContractError(
            "VAULT_MIGRATION_STALE: supplied source bindings do not match live configuration"
        )
    if any(
        (item["root"] / ".mindgarden-write.lock").exists()
        for item in bindings.gardens.values()
    ):
        raise ContractError(
            "VAULT_BUSY: complete garden writes before planning migration"
        )
    target_bytes = read_control(target_config.absolute())
    target = LocalBindings.load(target_config, garden_ids=set(), vault_ids={vault_id})
    if strict_json(target_bytes) != target.document:
        raise ContractError(
            "VAULT_MIGRATION_STALE: target configuration changed while loading"
        )
    if target.path == bindings.path:
        raise ContractError(
            "VAULT_MIGRATION_TARGET: use a separate explicit initialized target configuration"
        )
    if target.vault(vault_id)["root"] == bindings.vault(vault_id)["root"]:
        raise ContractError(
            "VAULT_MIGRATION_TARGET: use a distinct initialized target and retain the original store"
        )
    destination_path(bindings, vault_id, target.vault(vault_id)["root"], "relocate")
    for selected in (bindings, target):
        control_path(selected.vault(vault_id)["root"] / ".mindgarden-migration-control")
    adapters = adapters or default_storage_adapters()
    source, source_capabilities = open_checked(
        bindings, vault_id, adapters, source=True
    )
    destination, target_capabilities = open_checked(target, vault_id, adapters)
    # An empty target must still be initialized and available.
    probe = checked_state(destination, "sha256:" + "0" * 64)
    if probe not in {ContentState.MISSING, ContentState.AVAILABLE}:
        state_failure(probe)
    objects = inventory(source, vault_id, referenced_content(bindings, vault_id))
    for item in objects:
        target_has(destination, item)
    payload = {
        "schema": "mindgarden.vault-migration-plan/v1",
        "vault": vault_id,
        "publication": "never-exportable",
        "retains_original": True,
        "target_existing": "verify-and-retain",
        "source_adapter": source_capabilities["adapter"],
        "target_adapter": target_capabilities["adapter"],
        "source_configuration_sha256": digest_bytes(source_bytes),
        "target_configuration_sha256": digest_bytes(target_bytes),
        "source_capabilities_sha256": digest_bytes(canonical_json(source_capabilities)),
        "target_capabilities_sha256": digest_bytes(canonical_json(target_capabilities)),
        "objects": objects,
        "total_bytes": sum(item["size_bytes"] for item in objects),
        "garden_revisions": [
            {"garden": identity, "revision": garden_fingerprint(item["root"])}
            for identity, item in sorted(bindings.gardens.items())
        ],
    }
    rebound = deepcopy(bindings.document)
    selected = next(
        item for item in target.document["vaults"] if item["id"] == vault_id
    )
    for item in rebound["vaults"]:
        if item["id"] == vault_id:
            item.update(deepcopy(selected))
    copied = LocalBindings(
        bindings.path,
        deepcopy(bindings.document),
        deepcopy(bindings.gardens),
        deepcopy(bindings.vaults),
    )
    plan = VaultMigrationPlan(
        copied, target, adapters, payload, canonical_json(rebound)
    )
    plan.check_controls()
    if ContractRegistry().errors(plan.document(), "vault-migration-plan"):
        raise ContractError(
            "VAULT_MIGRATION_INVALID: plan violates the bounded migration contract"
        )
    return plan


def run_migration(arguments):
    bindings = LocalBindings.load(arguments.local_config)
    plan = build_vault_migration_plan(
        bindings, arguments.target_local_config, arguments.vault_id
    )
    result = plan.document()
    if arguments.apply:
        if not arguments.plan_digest:
            raise ContractError("PLAN_DIGEST: --plan-digest is required with --apply")
        result["applied"] = plan.apply(arguments.plan_digest)
    print(canonical_json(result).decode(), end="")
    return 0
