"""Private scoped asset inventory and reviewed non-destructive triage plans."""

from copy import deepcopy

from ..domain.assets import asset_review, asset_review_heads
from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object
from ..domain.garden import inspect_garden
from ..domain.scope import inherit_scope, local_scope
from ..domain.validation import ContractError
from .bindings import LocalBindings, garden_fingerprint
from .changes import ChangePlan
from .query import QueryContext
from .records import artifact_reference, provenance_record
from .storage import content_resolver

RETAIN = {"policy": "retain-originals", "legal_hold": False, "delete_authority": "none"}


def build_asset_manifest(context: QueryContext) -> dict:
    context.require("assets")
    if context.session.get("request_scope", {}).get("visibility") == "public":
        raise ContractError("PUBLICATION_DENIED: asset inventories are private owner outputs")
    snapshots = context.snapshots()
    records = [record for snapshot in snapshots.values() for record in snapshot.records.values()]
    heads = asset_review_heads(records)
    assets, scopes = {}, []
    for garden, snapshot in sorted(snapshots.items()):
        for record_id, record in sorted(snapshot.records.items()):
            if record["schema"] != "mindgarden.source/v1" or record["kind"] != "captured": continue
            if not context.allowed(garden, record): continue
            artifact = record["artifact"]; content_id = "sha256:" + artifact["sha256"]
            scope = context.scope_for(garden, record); scopes.append(scope)
            item = assets.setdefault(content_id, {"content_id": content_id, "sha256": artifact["sha256"],
                "size_bytes": artifact["size_bytes"], "media_types": [], "origins": [], "rights": [], "sources": [],
                "provenance": [], "scope": scope, "state": "unreviewed", "review": None,
                "retention": dict(RETAIN), "copy_policy": "reference-only",
                "encryption": {"required": False, "verified": False}, "interpretation": "untrusted-source"})
            item["scope"] = inherit_scope([item["scope"], scope])
            for field, value in (("media_types", record["media_type"]), ("origins", record["origin"]), ("rights", record["rights"]),
                                 ("sources", artifact_reference(garden, record_id, artifact["sha256"]))):
                if value not in item[field]: item[field].append(value)
            for reference in record["provenance"]:
                if reference not in item["provenance"]: item["provenance"].append(reference)
    for content_id, item in assets.items():
        for field in ("media_types", "origins", "rights", "sources", "provenance"):
            item[field].sort(key=canonical_json)
        head = heads.get(content_id)
        if head:
            event = asset_review(head)
            item.update(state=event["state"], review={"event": artifact_reference(head["garden"], head["id"], digest_bytes(canonical_json(head))),
                                                      "authority": event["authority"], "review": event["review"]},
                        retention=event["retention"], copy_policy=event["copy_policy"])
    maximum = min(context.session["budgets"]["max_results"], context.session["budgets"]["max_candidates"])
    selected = [assets[key] for key in sorted(assets)[:maximum]]
    output_scope = context.output_scope(scopes)
    output_scope = inherit_scope([output_scope, local_scope(output_scope["visibility"], persistence=output_scope["persistence"],
                                                           execution=output_scope["execution"], publication="never-exportable")])
    payload = {"schema": "mindgarden.asset-manifest/v1", "publication": "never-exportable", "scope": output_scope,
               "selection": "explicit-assets-projection-and-source-review-grants", "assets": selected,
               "source_revisions": [{"garden": garden, "revision": revision} for garden, revision in sorted(context.last_view_revisions.items())]}
    payload["manifest_sha256"] = digest_bytes(canonical_json(payload))
    if ContractRegistry().errors(payload, "asset-manifest"):
        raise ContractError("ASSET_MANIFEST_INVALID: authorized inventory violates its contract")
    return context.finalize(payload)


def build_asset_review_plan(bindings: LocalBindings, garden_id: str, request: dict, *, input_path=None) -> ChangePlan:
    if ContractRegistry().errors(request, "asset-review-request"):
        raise ContractError("ASSET_REVIEW_INVALID: supply an explicit human reviewed asset request")
    if request["authority"]["id"] not in request["review"]["reviewers"]:
        raise ContractError("ASSET_REVIEW_INVALID: human authority must be a named reviewer")
    if request["state"] == "restricted":
        raise ContractError("RUNTIME_UNVERIFIED: restricted triage requires unavailable confidential storage/runtime")
    if request["copy_policy"] != "reference-only":
        raise ContractError("ASSET_COPY_UNAVAILABLE: approved copy requires a separate publication/rights contract")
    binding = bindings.garden(garden_id)
    if binding["scope"]["visibility"] == "public" or binding["scope"]["persistence"] == "encrypted-vault":
        raise ContractError("RUNTIME_UNVERIFIED: this triage checkpoint requires an ordinary private garden")
    resolver = content_resolver(bindings)
    snapshot = inspect_garden(binding["root"], content_resolver=resolver).require_valid()
    reference = request["source"]; source = snapshot.records.get(reference["id"])
    if (reference["garden"] != garden_id or source is None or source["schema"] != "mindgarden.source/v1"
            or source["kind"] != "captured" or reference["revision"] != "sha256:" + source["artifact"]["sha256"]):
        raise ContractError("ASSET_SOURCE_STALE: triage requires exact captured-source evidence")
    scope = inherit_scope([binding["scope"], source.get("scope", binding["scope"])])
    if scope["visibility"] == "restricted" or scope["persistence"] == "encrypted-vault":
        raise ContractError("RUNTIME_UNVERIFIED: source triage scope requires unavailable assurance")
    event = {**deepcopy(request), "schema": "mindgarden.asset-review/v1", "content_id": "sha256:" + source["artifact"]["sha256"]}
    record_id = "asset-review-" + digest_bytes(canonical_json(event))[:32]
    inputs = [{"artifact": reference, "sha256": source["artifact"]["sha256"], "role": "source"}]
    if request["previous"] is not None:
        inputs.append({"artifact": request["previous"], "sha256": request["previous"]["revision"][7:], "role": "previous-version"})
    record = provenance_record(garden_id, record_id, source["id"], source["artifact"]["sha256"], inputs=inputs,
        transformations=[{"name": "non-destructive-asset-review", "version": "1.0.0", "parameters": {"request_sha256": digest_bytes(canonical_json(request))}}],
        created_at=request["review"]["reviewed_at"], rights=source["rights"], origin=source["origin"], scope=scope)
    record["x-asset-review"] = event; asset_review(record)
    heads = asset_review_heads(snapshot.records.values()); head = heads.get(event["content_id"])
    expected = artifact_reference(garden_id, head["id"], digest_bytes(canonical_json(head))) if head else None
    if record_id not in snapshot.records and request["previous"] != expected:
        raise ContractError("ASSET_REVIEW_STALE: explicitly supersede the exact current review event")
    checks = [(bindings.path, digest_bytes(bindings.path.read_bytes()))]
    if input_path is not None: checks.append((input_path.absolute(), digest_bytes(input_path.read_bytes())))
    return ChangePlan("asset-review", garden_id, binding["root"],
        {"garden_revision": garden_fingerprint(binding["root"]), "request": deepcopy(request), "scope": scope},
        {"provenance/" + record_id + ".json": canonical_json(record)}, source_checks=checks)


def apply_asset_review(plan: ChangePlan, reviewed_digest: str, bindings: LocalBindings) -> bool:
    def no_blob(_content): raise ContractError("ASSET_REVIEW_INVALID: metadata review cannot write source bytes")
    return plan.apply(reviewed_digest, validate=lambda stage: inspect_garden(plan.root, garden_root=stage,
        content_resolver=content_resolver(bindings)).require_valid(), put_blob=no_blob)


def run_asset(arguments):
    context = None
    if arguments.operation == "inventory":
        context = QueryContext.load(arguments.local_config, arguments.scope)
        result = build_asset_manifest(context)
    else:
        bindings = LocalBindings.load(arguments.local_config)
        request = read_object(arguments.input)
        plan = build_asset_review_plan(bindings, arguments.garden_id, request, input_path=arguments.input)
        result = plan.document()
        if arguments.apply:
            if not arguments.plan_digest: raise ContractError("PLAN_DIGEST: --plan-digest is required with --apply")
            result["applied"] = apply_asset_review(plan, arguments.plan_digest, bindings)
    content = canonical_json(result)
    if context is not None: context.ensure_output(content)
    print(content.decode(), end="")
    return 0
