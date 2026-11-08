"""Private, expiring, create-or-verify compaction proofs; never canonical knowledge."""

from datetime import datetime, timedelta, timezone

from ..adapters.generated_files import apply_generated, inventory
from ..adapters.registry_files import control_path
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from ..domain.scope import local_scope
from ..domain.validation import ContractError
from .compaction import preview_compaction
from .query import QueryContext


def plan_compaction_bundle(
    context, plan, created_at, *, curation=None, source_only=False
):
    context.require("context")
    if plan.get("scope") != local_scope(publication="never-exportable"):
        raise ContractError(
            "COMPACTION_PRIVATE: persisted proofs require a private local ceiling"
        )
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if created.tzinfo is None:
            raise ValueError()
        created = created.astimezone(timezone.utc)
    except (TypeError, AttributeError, ValueError) as error:
        raise ContractError(
            "COMPACTION_TIME: supply an explicit creation time with offset"
        ) from error
    report = preview_compaction(
        context, plan, curation=curation, source_only=source_only
    )
    expires = min(
        created + timedelta(seconds=plan["retention"]["model_context"]["ttl_seconds"]),
        datetime.fromisoformat(context.session["expires_at"].replace("Z", "+00:00")),
    )
    if created > context.clock() or context.clock() >= expires:
        raise ContractError(
            "COMPACTION_EXPIRED: proof is expired or not yet active; review a new bundle"
        )
    report["retention"]["enforcement"] = "private-bundle-live-authority-and-expiry"
    bundle = {
        "schema": "mindgarden.compaction-bundle/v1",
        "classification": "machine-local-control",
        "publication": "never-exportable",
        "scope": plan["scope"],
        "authority_sha256": context.scope_digest(),
        "source_plan_sha256": report["plan_sha256"],
        "input_mode": "source-grant" if source_only else "reviewed-evidence",
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "expires_at": expires.isoformat().replace("+00:00", "Z"),
        "manifest_sha256": digest_bytes(canonical_json(report["manifest"])),
        "report_sha256": digest_bytes(canonical_json(report)),
    }
    if ContractRegistry().errors(bundle, "compaction-bundle"):
        raise ContractError(
            "COMPACTION_BUNDLE: supported bounded proof metadata required"
        )
    files = {
        "plan.json": canonical_json(plan),
        "report.json": canonical_json(report),
        "manifest.json": canonical_json(report["manifest"]),
        "bundle.json": canonical_json(bundle),
    }
    if curation is not None:
        files["curation.json"] = canonical_json(curation)
    preview = {"bundle": bundle, "report": report, "files": inventory(files)}
    preview["plan_sha256"] = digest_bytes(canonical_json(preview))
    return context.finalize(preview), files


def run_compaction_bundle(arguments):
    context = QueryContext.load(arguments.local_config, arguments.scope)
    directory = arguments.output_directory.absolute()
    control_path(directory / ".mindgarden-generated.json")

    def current():
        plan = read_object(arguments.input)
        curation = (
            read_object(arguments.curation_plan) if arguments.curation_plan else None
        )
        return plan_compaction_bundle(
            context,
            plan,
            arguments.created_at,
            curation=curation,
            source_only=arguments.source_only,
        )

    preview, files = current()

    def verify():
        if current() != (preview, files):
            raise ContractError(
                "COMPACTION_STALE: inputs or authority changed; review a new plan"
            )

    if arguments.check and not directory.is_dir():
        raise ContractError("COMPACTION_MISSING: immutable proof bundle is unavailable")
    if arguments.apply or arguments.check:
        changed = apply_generated(
            directory,
            files,
            preview["plan_sha256"] if arguments.check else arguments.plan_digest,
            preview["plan_sha256"],
            check_live=context.check_live,
            verify_inputs=verify,
        )
        result = {
            "status": "created" if changed else "verified-no-op",
            "plan_sha256": preview["plan_sha256"],
            "expires_at": preview["bundle"]["expires_at"],
        }
    else:
        result = preview
    context.ensure_output(canonical_json(result))
    print(canonical_json(result).decode(), end="")
    return 0
