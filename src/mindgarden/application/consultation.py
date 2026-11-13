"""Live-authorized private packet planning through existing source grants."""

from copy import deepcopy
import json

from ..adapters.generated_files import apply_generated, complete_generated, inventory
from ..adapters.registry_files import control_path
from ..domain.consultation import build_packet, markdown, validate_request
from ..domain.contracts import canonical_json, digest_bytes, read_object, strict_json
from ..domain.scope import local_scope
from ..domain.validation import ContractError
from .federation import export_destination
from .query import QueryContext
from .source_evidence import resolve_source_evidence_batch


def plan_packet(context, request):
    request = deepcopy(validate_request(request))
    context.require("context")
    if request["scope"] != local_scope(publication="never-exportable"):
        raise ContractError(
            "PACKET_SCOPE: first packet checkpoint requires the ordinary private personal boundary"
        )
    if len(request["sources"]) > min(
        request["limits"]["max_rows"], context.session["budgets"]["max_candidates"]
    ):
        raise ContractError(
            "PACKET_BUDGET: selected source rows exceed the explicit candidate budget"
        )
    seen, evidence, scopes = set(), [], []
    for citation in request["sources"]:
        key = canonical_json(citation)
        if key in seen or citation["locator"] != "artifact":
            raise ContractError(
                "PACKET_SOURCE: select each complete normalized row once"
            )
        seen.add(key)
    verified = resolve_source_evidence_batch(context, request["sources"])
    for citation, value in zip(request["sources"], verified):
        try:
            row = strict_json(value["text"])
        except ContractError as error:
            raise ContractError(
                "PACKET_SOURCE: exact selected input is not a normalized ledger row"
            ) from error
        evidence.append((deepcopy(citation), row, value["origin"]))
        scopes.append(value["scope"])
    scope = context.output_scope(scopes)
    if scope != request["scope"]:
        raise ContractError(
            "PACKET_SCOPE: output must retain all contributor restrictions"
        )
    packet, selected = build_packet(request, evidence, scope)
    files = {"packet.json": canonical_json(packet), "packet.md": markdown(packet)}
    for identity in sorted(request["attachments"]):
        files["evidence-" + identity + ".json"] = canonical_json(
            selected[identity]["row"]
        )
    # Request/review and numeric calculation provenance travel with the private
    # bundle; these are data, not credentials or a source of session authority.
    files["reviewed-request.json"] = canonical_json(request)
    maximum = min(
        request["limits"]["max_bytes"], context.session["budgets"]["max_context_bytes"]
    )
    preview = {
        "schema": "mindgarden.consultation-plan/v1",
        "id": request["id"],
        "scope": scope,
        "packet": packet,
        "calculation_sha256": digest_bytes(files["packet.json"]),
        "authority_sha256": context.scope_digest(),
        "files": inventory(files),
    }
    preview["plan_sha256"] = digest_bytes(canonical_json(preview))
    complete = complete_generated(files, preview["plan_sha256"])
    if sum(map(len, complete.values())) > maximum:
        raise ContractError(
            "PACKET_BUDGET: complete packet, ownership, review and evidence exceed the byte budget"
        )
    context.ensure_bundle(complete)
    return context.finalize(preview), files


def run_packet(arguments):
    context = QueryContext.load(arguments.local_config, arguments.scope)
    destination = arguments.output_directory.absolute()
    destination = export_destination(context, destination.parent, destination.name)
    control_path(destination / ".mindgarden-generated.json")

    def current():
        return plan_packet(context, read_object(arguments.input))

    preview, files = current()

    def verify():
        if current() != (preview, files):
            raise ContractError(
                "PACKET_STALE: source, review, selection or live authority changed"
            )

    if arguments.check and not destination.is_dir():
        raise ContractError(
            "PACKET_MISSING: no immutable packet exists at the selected location"
        )
    if arguments.apply or arguments.check:
        changed = apply_generated(
            destination,
            files,
            preview["plan_sha256"] if arguments.check else arguments.plan_digest,
            preview["plan_sha256"],
            check_live=context.check_live,
            validate_output=context.ensure_bundle,
            verify_inputs=verify,
        )
        result = {
            "status": "created" if changed else "verified-no-op",
            "plan_sha256": preview["plan_sha256"],
        }
    else:
        result = preview
    context.ensure_output(canonical_json(result))
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0
