"""Local storage application services over explicit consumer bindings."""

from __future__ import annotations

from argparse import Namespace
import json

from ..adapters.filesystem import FilesystemVault
from ..domain.contracts import digest_bytes
from ..domain.validation import ContractError
from .bindings import LocalBindings


def open_vault(bindings: LocalBindings, vault_id: str) -> FilesystemVault:
    binding = bindings.vault(vault_id)
    if binding["adapter"] != "filesystem":
        raise ContractError("STORAGE_UNSUPPORTED: storage adapter is not installed")
    return FilesystemVault(binding["root"], vault_id)


def content_resolver(bindings: LocalBindings):
    def resolve(artifact: dict) -> bytes:
        reference = artifact["vault"]
        if reference["content_id"] != "sha256:" + artifact["sha256"]:
            raise ContractError("CONTENT_ID: content identity and artifact checksum disagree")
        content = open_vault(bindings, reference["id"]).get(reference["content_id"])
        if len(content) != artifact["size_bytes"]:
            raise ContractError("CONTENT_SIZE: stored content length differs")
        return content
    return resolve


def run_vault(arguments: Namespace) -> int:
    bindings = LocalBindings.load(arguments.local_config)
    vault = open_vault(bindings, arguments.vault_id)
    if arguments.operation == "init":
        plan = vault.plan_init(digest_bytes(arguments.local_config.read_bytes()))
        if arguments.apply:
            if not arguments.plan_digest:
                raise ContractError("PLAN_DIGEST: --plan-digest is required with --apply")
            applied = vault.initialize(plan, arguments.plan_digest)
            plan = {**plan, "applied": applied}
        result = plan
    elif arguments.operation == "audit":
        from .vault_recovery import referenced_content

        result = vault.audit(referenced_content(bindings, arguments.vault_id))
    elif arguments.operation == "capabilities":
        result = vault.capabilities()
    elif arguments.operation == "resolve":
        result = {"schema": "mindgarden.content-status/v1", "content_id": arguments.content_id,
                  "state": vault.state(arguments.content_id).value}
    elif arguments.operation in {"export", "restore", "relocate"}:
        from .vault_recovery import build_vault_recovery_plan

        destination = arguments.output if arguments.operation == "export" else arguments.destination
        plan = build_vault_recovery_plan(bindings, arguments.vault_id, arguments.operation, destination,
                                         input_path=getattr(arguments, "input", None))
        result = plan.document()
        if arguments.apply:
            if not arguments.plan_digest:
                raise ContractError("PLAN_DIGEST: --plan-digest is required with --apply")
            result["applied"] = plan.apply(arguments.plan_digest)
    else:
        raise ContractError("STORAGE_UNSUPPORTED: unsupported storage operation")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 3 if result.get("status") == "invalid" or result.get("state", "available") != "available" else 0
