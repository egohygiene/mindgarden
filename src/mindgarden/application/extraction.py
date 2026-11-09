"""Bounded optional extraction into existing, explicitly unreviewed curation plans."""

from copy import deepcopy

from ..adapters.extraction_producer import (
    ExtractionProducer,
    RecordedExtractionProducer,
)
from ..adapters.generated_files import apply_generated, inventory
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from ..domain.scope import local_scope
from ..domain.validation import ContractError
from .federation import export_destination
from .query import QueryContext
from .source_evidence import resolve_source_evidence

REVIEW = {
    "state": "unreviewed",
    "reviewers": [],
    "reviewed_at": None,
    "rationale": None,
}
RELATIONS = {
    "related",
    "supports",
    "contradicts",
    "supersedes",
    "derived-from",
    "part-of",
    "depends-on",
    "references",
}


def validate_output(value, selected_text, maximum):
    try:
        size = len(canonical_json(value))
    except (TypeError, ValueError, RecursionError) as error:
        raise ContractError(
            "EXTRACTION_OUTPUT: producer output must be bounded JSON"
        ) from error
    if size > maximum or ContractRegistry().errors(value, "extraction-output"):
        raise ContractError("EXTRACTION_OUTPUT: invalid or oversized producer output")
    entities = {e["id"]: e for e in value["entities"]}
    assertions = {a["id"]: a for a in value["assertions"]}
    if len(entities) != len(value["entities"]) or len(assertions) != len(
        value["assertions"]
    ):
        raise ContractError("EXTRACTION_OUTPUT: duplicate local proposal identity")
    if value["status"] in {"failed", "unsupported"} and (entities or assertions):
        raise ContractError(
            "EXTRACTION_OUTPUT: unsuccessful results cannot masquerade as candidates"
        )
    for item in [*entities.values(), *assertions.values()]:
        if item["quote"] not in selected_text:
            raise ContractError(
                "EXTRACTION_OUTPUT: supporting quote differs from exact selected evidence"
            )
    for assertion in assertions.values():
        if (
            assertion["subject"] not in entities
            or assertion["object"] not in entities
            or any(
                target not in assertions or target == assertion["id"]
                for target in assertion["contradicts"]
            )
        ):
            raise ContractError(
                "EXTRACTION_OUTPUT: proposal endpoint or contradiction does not resolve"
            )
    return deepcopy(value)


def mapped_candidates(record, request):
    """No alias merging or vocabulary creation. Unknown mappings remain in the batch."""
    output = record["output"]
    if output is None:
        return []
    key = record["key"][:16]
    entities = {e["id"]: e for e in output["entities"]}
    ids = {
        e["id"]: "extract-" + key + "-e-" + digest_bytes(e["id"].encode())[:12]
        for e in entities.values()
    }
    assertion_ids = {
        a["id"]: "extract-" + key + "-a-" + digest_bytes(a["id"].encode())[:12]
        for a in output["assertions"]
    }
    eligible = {
        a["id"]
        for a in output["assertions"]
        if a["predicate"] in RELATIONS
        and all(
            entities[a[side]]["resolution"] == "new" for side in ("subject", "object")
        )
    }
    source = record["evidence"]
    author = {
        "kind": "agent",
        "id": request["producer"]["id"],
        "version": request["producer"]["version"],
    }
    origin = record["origin"]
    attribution = (
        "assistant-suggestion"
        if origin["speaker"] == "assistant"
        else "user-report"
        if origin["speaker"] == "user"
        else "third-party"
    )
    pins = canonical_json(request["producer"]).decode().strip()

    def candidate(
        identity,
        title,
        kind,
        body,
        *,
        caveats=(),
        uncertainty=(),
        claims=(),
        synapses=(),
        contradictions=(),
        aliases=(),
    ):
        return {
            "id": identity,
            "action": "keep",
            "sources": [source],
            "merge_inputs": [],
            "rationale": "Optional producer proposal; explicit review remains required. "
            + pins,
            "output": {
                "id": identity,
                "title": title,
                "kind": kind,
                "body": body,
                "authors": [author],
                "review": deepcopy(REVIEW),
                "status": "proposed",
                "confidence": "unknown",
                "epistemic_state": "unverified",
                "attribution": attribution,
                "domains": list(request["domains"]),
                "topics": list(request["topics"]),
                "caveats": [
                    "Producer structure and quotations do not verify its interpretation.",
                    "Source identity: " + origin["source_identity"],
                    "Observed speaker/time: "
                    + str(origin["speaker"])
                    + "/"
                    + str(origin["timestamp"]),
                    *caveats,
                ],
                "uncertainty": list(uncertainty),
                "contradictions": list(contradictions),
                "claims": list(claims),
                "synapses": list(synapses),
                "aliases": list(aliases),
            },
        }

    def reference(identity):
        return {"garden": request["garden"], "id": identity, "revision": None}

    candidates = []
    for entity in entities.values():
        if entity["resolution"] != "new":
            continue
        candidates.append(
            candidate(
                ids[entity["id"]],
                entity["label"],
                "concept",
                entity["label"] + "\n" + entity["rationale"] + "\n",
                uncertainty=[
                    "Entity identity and aliases remain unverified; no cross-source merge occurred."
                ],
                aliases=entity["aliases"],
            )
        )
    for assertion in output["assertions"]:
        if assertion["id"] not in eligible:
            continue
        identity = assertion_ids[assertion["id"]]
        contradiction_targets = [
            reference(assertion_ids[value])
            for value in assertion["contradicts"]
            if value in eligible
        ]
        statement = assertion["statement"]
        qualified = (
            f"Proposed {assertion['stance']} ({assertion['polarity']}): {statement}\n"
        )
        qualifications = [
            "Context: " + assertion["context"],
            "Temporal qualification: " + str(assertion["temporal"]),
            "Polarity/stance: " + assertion["polarity"] + "/" + assertion["stance"],
        ]
        claim = {
            "id": identity + "-claim",
            "statement": qualified.strip(),
            "epistemic_state": "open-question"
            if assertion["stance"] == "question"
            else "unverified",
            "confidence": "unknown",
            "review": deepcopy(REVIEW),
            "evidence": [
                {
                    "target": source,
                    "relationship": "uncertain",
                    "rationale": "Exact source supports an attributed proposal, not verification.",
                }
            ],
        }
        synapses = [
            {
                "id": identity + "-object",
                "type": assertion["predicate"],
                "target": reference(ids[assertion["object"]]),
                "directed": True,
                "review": deepcopy(REVIEW),
                "rationale": "Proposed object relationship; " + assertion["context"],
            },
            {
                "id": identity + "-subject",
                "type": "references",
                "target": reference(ids[assertion["subject"]]),
                "directed": True,
                "review": deepcopy(REVIEW),
                "rationale": "Explicit proposed subject mapping.",
            },
        ]
        for index, target in enumerate(contradiction_targets):
            synapses.append(
                {
                    "id": identity + "-conflict-" + str(index),
                    "type": "contradicts",
                    "target": target,
                    "directed": True,
                    "review": deepcopy(REVIEW),
                    "rationale": "Producer-reported disagreement retained for review.",
                }
            )
        candidates.append(
            candidate(
                identity,
                statement[:160],
                "insight",
                qualified,
                caveats=qualifications,
                uncertainty=assertion["uncertainty"],
                claims=[claim],
                synapses=synapses,
                contradictions=contradiction_targets,
            )
        )
    return candidates


def produce_batch(
    context: QueryContext,
    request: dict,
    producer: ExtractionProducer,
    *,
    previous=None,
    max_new_units=None,
    on_checkpoint=None,
):
    context.require("source-evidence")
    if (
        ContractRegistry().errors(request, "extraction-request")
        or context.session.get("request_scope")
        != local_scope(publication="never-exportable")
        or producer.execution != "offline"
        or producer.descriptor != request["producer"]
    ):
        raise ContractError(
            "EXTRACTION_REQUEST: bounded private offline inputs and exact producer pins are required"
        )
    if (
        request["garden"] not in context.bindings.gardens
        or context.bindings.gardens[request["garden"]]["scope"]["visibility"]
        != "personal"
    ):
        raise ContractError(
            "EXTRACTION_TARGET: proposals require an authorized private fallback garden"
        )
    if max_new_units is not None and (
        type(max_new_units) is not int or not 1 <= max_new_units <= 16
    ):
        raise ContractError(
            "EXTRACTION_BUDGET: new-unit limit must be between one and sixteen"
        )
    config_digest = digest_bytes(
        canonical_json({"producer": request["producer"], "limits": request["limits"]})
    )
    request_digest = digest_bytes(canonical_json(request))
    previous_records = {}
    if previous is not None:
        if (
            not isinstance(previous, dict)
            or previous.get("schema") != "mindgarden.extraction-batch/v1"
            or previous.get("config_sha256") != config_digest
            or previous.get("request_sha256") != request_digest
            or not isinstance(previous.get("records"), list)
            or len(previous["records"]) > 16
        ):
            raise ContractError(
                "EXTRACTION_RESUME: checkpoint does not represent the exact request/configuration"
            )
        for record in previous["records"]:
            if not isinstance(record, dict) or record.get("key") in previous_records:
                raise ContractError(
                    "EXTRACTION_RESUME: malformed or duplicate checkpoint record"
                )
            previous_records[record["key"]] = record
    selected = []
    for source in request["sources"]:
        evidence = resolve_source_evidence(
            context, source["source"], source["locator"], source["content_sha256"]
        )
        origin = evidence["origin"]
        item = {
            "evidence": source,
            "text": evidence["text"],
            "origin": {
                "source_identity": evidence["source_identity"],
                "speaker": origin.get("speaker"),
                "timestamp": origin.get("timestamp"),
                "source_message_id": origin.get("source_message_id"),
                "branch_id": origin.get("branch_id"),
                "summary_derived": origin.get("summary_derived"),
            },
        }
        item["input_sha256"] = digest_bytes(canonical_json(item))
        item["key"] = digest_bytes(
            canonical_json({"input": item["input_sha256"], "config": config_digest})
        )
        selected.append(item)
    if (
        sum(len(item["text"].encode()) for item in selected)
        > request["limits"]["max_input_bytes"]
    ):
        raise ContractError(
            "EXTRACTION_BUDGET: selected text exceeds the explicit batch input limit"
        )
    if set(previous_records) - {item["key"] for item in selected}:
        raise ContractError("EXTRACTION_RESUME: checkpoint contains unselected inputs")
    records, new_calls = [], 0

    def checkpoint():
        return {
            "schema": "mindgarden.extraction-batch/v1",
            "request_sha256": request_digest,
            "config_sha256": config_digest,
            "scope": local_scope(publication="never-exportable"),
            "authority_sha256": context.scope_digest(),
            "producer": deepcopy(request["producer"]),
            "records": deepcopy(records),
        }

    for item in selected:
        context.check_live()
        output, status, diagnostic = None, "deferred", "batch-interrupted"
        earlier = previous_records.get(item["key"])
        if earlier is not None and earlier.get("status") in {
            "success",
            "success-empty",
            "unsupported",
            "partial",
        }:
            if (
                earlier.get("evidence") != item["evidence"]
                or earlier.get("input_sha256") != item["input_sha256"]
                or earlier.get("origin") != item["origin"]
            ):
                raise ContractError(
                    "EXTRACTION_RESUME: exact evidence metadata differs"
                )
            output = validate_output(
                earlier.get("output"),
                item["text"],
                request["limits"]["max_output_bytes"],
            )
            status = output["status"]
            if (
                status == "success"
                and not output["entities"]
                and not output["assertions"]
            ):
                status = "success-empty"
            diagnostic = None
        elif max_new_units is None or new_calls < max_new_units:
            new_calls += 1
            try:
                output = validate_output(
                    producer.extract(deepcopy(item)),
                    item["text"],
                    request["limits"]["max_output_bytes"],
                )
                status = output["status"]
                if (
                    status == "success"
                    and not output["entities"]
                    and not output["assertions"]
                ):
                    status = "success-empty"
                diagnostic = None
            except ContractError:
                status, diagnostic, output = "invalid", "invalid-output", None
            except Exception:
                status, diagnostic, output = "failed", "provider-failure", None
        record = {
            key: deepcopy(item[key])
            for key in ("key", "input_sha256", "evidence", "origin")
        }
        record.update(status=status, diagnostic=diagnostic, output=output)
        records.append(record)
        context.check_live()
        if on_checkpoint is not None:
            on_checkpoint(context.finalize(checkpoint()))
    result = checkpoint()
    candidates = [
        candidate
        for record in records
        for candidate in mapped_candidates(record, request)
    ]
    result["proposal"] = (
        {
            "schema": "mindgarden.curation-plan/v1",
            "id": request["id"],
            "garden": request["garden"],
            "created_at": request["created_at"],
            "producer": {
                "kind": "agent",
                "id": request["producer"]["id"],
                "version": request["producer"]["version"],
            },
            "review_authority": None,
            "candidates": candidates,
        }
        if candidates
        else None
    )
    if result["proposal"] is not None and ContractRegistry().errors(
        result["proposal"], "curation-plan"
    ):
        raise ContractError(
            "EXTRACTION_MAPPING: proposals do not conform to the existing curation contract"
        )
    result["status"] = (
        "complete"
        if all(
            r["status"] in {"success", "success-empty", "unsupported"} for r in records
        )
        else "partial"
    )
    result["new_calls"] = new_calls
    result["plan_sha256"] = digest_bytes(
        canonical_json({k: v for k, v in result.items() if k != "new_calls"})
    )
    return context.finalize(result)


def run_extraction(arguments):
    context = QueryContext.load(arguments.local_config, arguments.scope)
    request = read_object(arguments.input)
    recording = read_object(arguments.recorded_output)
    if set(recording) != {"producer", "outputs"}:
        raise ContractError(
            "EXTRACTION_RECORDING: supply the explicit recorded producer/output map"
        )
    previous = read_object(arguments.resume) if arguments.resume else None
    producer = RecordedExtractionProducer(recording["producer"], recording["outputs"])
    result = produce_batch(
        context,
        request,
        producer,
        previous=previous,
        max_new_units=arguments.max_new_units,
    )
    files = {
        "batch.json": canonical_json(result),
        "request.json": canonical_json(request),
    }
    if result["proposal"] is not None:
        files["curation.json"] = canonical_json(result["proposal"])
    preview = {"batch": result, "files": inventory(files)}
    digest = digest_bytes(canonical_json(preview))
    if arguments.output_directory:
        directory = export_destination(
            context,
            arguments.output_directory.absolute().parent,
            arguments.output_directory.name,
        )

        def verify():
            if (
                read_object(arguments.input) != request
                or read_object(arguments.recorded_output) != recording
            ):
                raise ContractError(
                    "EXTRACTION_STALE: request or authored outputs changed"
                )
            if arguments.resume and read_object(arguments.resume) != previous:
                raise ContractError("EXTRACTION_STALE: resume checkpoint changed")

        if arguments.apply:
            apply_generated(
                directory,
                files,
                arguments.plan_digest,
                digest,
                check_live=context.check_live,
                verify_inputs=verify,
            )
    elif arguments.apply:
        raise ContractError(
            "EXTRACTION_DESTINATION: explicit private output directory is required"
        )
    payload = {**preview, "plan_sha256": digest}
    context.ensure_output(canonical_json(payload))
    print(canonical_json(payload).decode(), end="")
    return 0
