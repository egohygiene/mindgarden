"""Non-destructive preflight for an explicitly selected private local workspace."""

import os
from pathlib import Path

from ..adapters.drive_credentials import cached_access_token
from ..adapters.registry_files import control_path
from ..domain.contracts import ContractRegistry, canonical_json, read_object, safe_path
from ..domain.drive_capture import validate_binding
from ..domain.validation import ContractError
from .bindings import LocalBindings
from .local_federation import ordinary_output_scope, require_private, verified_metadata
from .query import QueryContext, authority_bytes
from .storage import open_vault


def private_control(path):
    path = control_path(Path(path))
    if (
        not path.is_file()
        or path.stat().st_uid != os.getuid()
        or path.stat().st_mode & 0o077
    ):
        raise ContractError(
            "PILOT_LOCATION: use owned private control files outside Git"
        )
    return path


def private_root(root):
    if (
        os.name != "posix"
        or not root.is_dir()
        or root.stat().st_uid != os.getuid()
        or root.stat().st_mode & 0o077
        or any(path.is_symlink() for path in (root, *root.parents))
        or any(
            (parent / ".git").exists() or (parent / ".git").is_symlink()
            for parent in (root, *root.parents)
        )
    ):
        raise ContractError(
            "PILOT_LOCATION: this pilot requires owned private untracked POSIX roots"
        )


def preflight(
    local_config,
    session_path,
    garden_id,
    vault_id,
    classification,
    *,
    drive_binding=None,
):
    """Inspect metadata/configuration only; no original, provider or model reads."""
    config = private_control(local_config)
    session = private_control(session_path)
    originals = {config: authority_bytes(config), session: authority_bytes(session)}
    if classification != "personal":
        raise ContractError(
            "PILOT_CLASSIFICATION: restricted/unknown processing needs actual external assurance"
        )
    context = QueryContext.load(config, session, garden_ids={garden_id})
    require_private(context)
    binding = context.bindings.garden(garden_id)
    if binding["scope"]["visibility"] != classification:
        raise ContractError(
            "PILOT_CLASSIFICATION: declared and existing garden policy disagree"
        )
    views = verified_metadata(context)
    ordinary_output_scope(
        context, [binding["scope"], *views[garden_id]["scopes"].values()]
    )
    private_root(binding["root"])
    bindings = LocalBindings.load(config, garden_ids={garden_id}, vault_ids={vault_id})
    vault_binding = bindings.vault(vault_id)
    private_root(vault_binding["root"])
    vault = open_vault(bindings, vault_id)
    capabilities = vault.capabilities()
    if capabilities["adapter"] != "filesystem" or capabilities["remote"]:
        raise ContractError(
            "PILOT_UNAVAILABLE: first pilot requires the local filesystem baseline"
        )
    manifest = read_object(safe_path(vault_binding["root"], "vault.json"))
    if (
        ContractRegistry().errors(manifest, "vault")
        or manifest["id"] != vault_id
        or manifest["adapter"] != "filesystem"
        or manifest["format_version"] != "1.0.0"
    ):
        raise ContractError(
            "PILOT_UNAVAILABLE: initialized vault metadata is unavailable"
        )
    checks = [
        {"check": name, "status": "passed"}
        for name in (
            "private-control-paths",
            "exact-live-session",
            "personal-offline-policy",
            "private-untracked-roots",
            "filesystem-vault-metadata",
        )
    ]
    if drive_binding is not None:
        path = private_control(drive_binding)
        originals[path] = authority_bytes(path)
        validate_binding(read_object(path))
        checks.append(
            {"check": "reviewed-controlled-import-selection", "status": "passed"}
        )
        try:
            cached_access_token()
        except ContractError:
            checks.append({"check": "cached-drive-credential", "status": "unavailable"})
        else:
            checks.append(
                {
                    "check": "cached-drive-credential",
                    "status": "present-not-live-verified",
                }
            )
    context.check_live()
    if any(authority_bytes(path) != content for path, content in originals.items()):
        raise ContractError(
            "PILOT_UNAVAILABLE: private configuration changed during preflight"
        )
    result = {
        "schema": "mindgarden.local-pilot-preflight/v1",
        "status": "blocked"
        if any(c["status"] == "unavailable" for c in checks)
        else "ready-to-attempt",
        "classification": classification,
        "checks": checks,
        "original_reads": 0,
        "network_calls": 0,
        "model_calls": 0,
        "writes": 0,
        "limitations": [
            "Readiness is not live account authentication, source integrity audit or approval of unseen content.",
            "Folder selection and classification must be supplied by the operator; no account scan or downgrade.",
            "Real restricted processing and external/hosted assistant access require their actual policy/runtime authority.",
            "No private pilot, financial completeness, legal interpretation or confidential-runtime assurance is certified.",
            "This first pilot excludes Git-tracked roots and unverified platform/private-Git storage.",
        ],
    }
    context.ensure_output(canonical_json(result))
    return result


def run_pilot(arguments):
    result = preflight(
        arguments.local_config,
        arguments.scope,
        arguments.garden_id,
        arguments.vault_id,
        arguments.classification,
        drive_binding=arguments.drive_binding,
    )
    print(canonical_json(result).decode(), end="")
    return 3 if result["status"] == "blocked" else 0
