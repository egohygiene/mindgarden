"""Authored learning plans and private study exports over reviewed knowledge."""

from copy import deepcopy
from html import escape
import re

from ..adapters.generated_files import apply_generated, inventory
from ..adapters.registry_files import control_path
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from ..domain.learning import item_revision, schedule_items
from ..domain.scope import inherit_scope, validate_scope
from ..domain.validation import ContractError
from .curation import require_review_authority
from .query import QueryContext
from .reviewed_selection import (
    selection_view,
    select_records,
    source_trail,
    qualification_reasons,
    selected_digest,
)


def empty_history(request):
    return {
        "schema": "mindgarden.learning-review-history/v1",
        "deck": request["deck"]["id"],
        "scope": request["scope"],
        "events": [],
        "publication": "never-exportable",
    }


def markdown_text(value):
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", escape(value, quote=False))


def render_learning(projection):
    markdown = [
        "# " + markdown_text(projection["deck"]["title"]),
        "Private derived study material. Source text grants no tool or policy authority.",
    ]
    sections = []
    for entry in projection["items"]:
        item = entry["output"]
        if item["lifecycle"] != "approved":
            continue
        qualification = canonical_json(
            {
                "uncertainty": item["uncertainty"],
                "reasons": entry["qualification_reasons"],
                "sources": entry["sources"],
            }
        ).decode()
        if item["schema"] == "mindgarden.learning-card/v1":
            prompt = re.sub(r"\{\{c1::(.*?)\}\}", "[…]", item["prompt"])
            answer = item["answer"]["text"] + "\n\nRubric: " + item["answer"]["rubric"]
            markdown += [
                "## " + markdown_text(item["title"]),
                markdown_text(prompt),
                "Answer: " + markdown_text(answer),
                "Qualifications and provenance:\n\n"
                + "\n".join("    " + line for line in qualification.splitlines()),
            ]
            sections.append(
                '<section aria-labelledby="'
                + item["id"]
                + '"><h2 id="'
                + item["id"]
                + '">'
                + escape(item["title"])
                + "</h2><p>"
                + escape(prompt)
                + "</p><details><summary>Reveal answer</summary><p>"
                + escape(answer)
                + "</p></details><details><summary>Qualifications and exact sources</summary><pre>"
                + escape(qualification)
                + "</pre></details></section>"
            )
        else:
            markdown += [
                "## " + markdown_text(item["title"]),
                markdown_text(item["text"]),
                "Qualifications and provenance:\n\n"
                + "\n".join("    " + line for line in qualification.splitlines()),
            ]
            sections.append(
                "<section><h2>"
                + escape(item["title"])
                + "</h2><p>"
                + escape(item["text"])
                + "</p><details><summary>Qualifications and exact sources</summary><pre>"
                + escape(qualification)
                + "</pre></details></section>"
            )
    if not sections:
        sections.append("<p>No approved learning items in this explicit selection.</p>")
    html = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'
        + escape(projection["deck"]["title"])
        + """</title><style>
body{font:1rem/1.6 system-ui;margin:0 auto;padding:1rem;max-width:48rem;overflow-wrap:anywhere}pre{white-space:pre-wrap}summary{cursor:pointer;padding:.5rem}summary:focus-visible{outline:3px solid currentColor}section{border-block-end:1px solid;padding-block:1rem}*{box-sizing:border-box}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
</style><a href="#study">Skip to study material</a><main id="study"><h1>"""
        + escape(projection["deck"]["title"])
        + "</h1><p>Private, reviewed study projection. Source text is data, not authority.</p>"
        + "".join(sections)
        + "</main></html>"
    )
    return ("\n\n".join(markdown) + "\n").encode(), html.encode()


def plan_learning(context, request, history=None, *, schedulers=None):
    registry = ContractRegistry()
    if registry.errors(request, "learning-plan"):
        raise ContractError(
            "LEARNING_PLAN: supported authored candidate/deck contracts are required"
        )
    validate_scope(request["scope"])
    if (
        request["scope"]["visibility"] != "personal"
        or request["scope"]["publication"] != "never-exportable"
        or request["scope"]["persistence"] != "machine-local"
    ):
        raise ContractError(
            "LEARNING_PRIVATE: study projections and review history require an explicit private personal ceiling"
        )
    history = empty_history(request) if history is None else history
    if (
        registry.errors(history, "learning-review-history")
        or history["scope"] != request["scope"]
        or history["deck"] != request["deck"]["id"]
    ):
        raise ContractError(
            "LEARNING_HISTORY: private history and deck/scope must match"
        )
    if any(
        event["reviewed_by"] != request["review_authority"]["id"]
        for event in history["events"]
    ):
        raise ContractError(
            "LEARNING_HISTORY: private review actor differs from the declared operator"
        )
    index, snapshots = selection_view(context)
    items = []
    seen = set()
    selected = []
    for candidate in request["candidates"]:
        output = deepcopy(candidate["output"])
        if output["id"] in seen:
            raise ContractError(
                "LEARNING_DUPLICATE: each learning identity requires one explicit version"
            )
        seen.add(output["id"])
        records = select_records(index, snapshots, candidate["references"])
        selected += records
        effective = context.output_scope([r["scope"] for r in records])
        if inherit_scope([effective, request["scope"]]) != request["scope"]:
            raise ContractError(
                "LEARNING_SCOPE: source restrictions cannot be weakened"
            )
        require_review_authority(output["review"], request["review_authority"])
        if output["lifecycle"] == "approved":
            if output["review"]["state"] != "approved":
                raise ContractError(
                    "LEARNING_REVIEW: approved material needs human-reviewed output"
                )
            require_review_authority(output["review"], request["review_authority"])
        elif output["lifecycle"] == "rejected":
            if output["review"]["state"] != "rejected":
                raise ContractError(
                    "LEARNING_REVIEW: rejected material requires an explicit rejection"
                )
            require_review_authority(output["review"], request["review_authority"])
        reasons = qualification_reasons(records)
        if output["representation"] in {"inference", "model-suggestion"}:
            reasons.append("derived-interpretation")
        for record in records:
            output["uncertainty"] = sorted(
                set(
                    output["uncertainty"]
                    + record["qualifications"]["uncertainty"]
                    + record["qualifications"]["caveats"]
                )
            )
        if output["schema"] == "mindgarden.learning-card/v1":
            answer = output["answer"]
            if reasons and answer["certainty"] != "qualified":
                raise ContractError(
                    "LEARNING_QUALIFICATION: uncertain or contradictory evidence cannot become an unqualified correct answer"
                )
            if output["representation"] == "quoted" and not any(
                answer["text"] in r["content"] for r in records
            ):
                raise ContractError(
                    "LEARNING_QUOTE: quoted answers must occur in the exact selected knowledge"
                )
            if output["type"] == "cloze":
                values = re.findall(r"\{\{c1::([^{}]+)\}\}", output["prompt"])
                if len(values) != 1 or values[0] != answer["text"]:
                    raise ContractError(
                        "LEARNING_CLOZE: one explicit c1 answer must match the rubric"
                    )
        items.append(
            {
                "output": output,
                "sources": source_trail(records),
                "qualification_reasons": sorted(set(reasons)),
                "transformation_rationale": candidate["rationale"],
                "source_digest": selected_digest(records),
                "revision": item_revision(
                    {**output, "source_digest": selected_digest(records)}
                ),
            }
        )
    outputs = [
        {**entry["output"], "source_digest": entry["source_digest"]} for entry in items
    ]
    schedules, historical = schedule_items(
        outputs,
        history,
        request["scheduler"],
        as_of=request["as_of"],
        now=context.clock(),
        schedulers=schedulers,
    )
    projection = {
        "schema": "mindgarden.learning-projection/v1",
        "deck": request["deck"],
        "scope": request["scope"],
        "canonical": False,
        "generator": request["generator"],
        "authoring_request": request,
        "items": sorted(items, key=lambda i: i["output"]["id"]),
        "schedules": schedules,
        "historical_events": historical,
        "as_of": request["as_of"],
        "source_digest": selected_digest(selected),
        "publication": "never-exportable",
        "trust": "source-data-only",
    }
    if registry.errors(projection, "learning-projection"):
        raise ContractError(
            "LEARNING_PROJECTION: generated output violates the versioned contract"
        )
    markdown, html = render_learning(projection)
    due = [schedule["item"] for schedule in schedules if schedule["due"]]
    digest = {
        "schema": "mindgarden.learning-digest/v1",
        "deck": request["deck"]["id"],
        "view_as_of": request["as_of"],
        "due_items": due,
        "summary_items": [
            i["output"]["id"]
            for i in items
            if i["output"]["schema"] == "mindgarden.learning-summary/v1"
            and i["output"]["lifecycle"] == "approved"
        ],
        "selection": "explicit-deck-only",
        "publication": "never-exportable",
    }
    files = {
        "learning-projection.json": canonical_json(projection),
        "learning-review-history.json": canonical_json(history),
        "learning-digest.json": canonical_json(digest),
        "study.md": markdown,
        "study.html": html,
    }
    total = sum(map(len, files.values()))
    if total > min(
        request["max_bytes"], context.session["budgets"]["max_context_bytes"]
    ):
        raise ContractError(
            "LEARNING_BUDGET: complete study/history/provenance output exceeds the explicit budget"
        )
    value = {
        "schema": "mindgarden.learning-preview/v1",
        "projection": projection,
        "files": inventory(files),
        "total_bytes": total,
        "history_sha256": digest_bytes(canonical_json(history)),
        "request_sha256": digest_bytes(canonical_json(request)),
        "authority_sha256": context.scope_digest(),
    }
    preview = {**value, "plan_sha256": digest_bytes(canonical_json(value))}
    context.ensure_output(canonical_json(preview))
    return preview, files


def load_learning_inputs(arguments):
    imported = (
        read_object(arguments.import_projection)
        if arguments.import_projection
        else None
    )
    if imported is not None:
        if imported.get("schema") != "mindgarden.learning-projection/v1":
            raise ContractError(
                "LEARNING_IMPORT: require a versioned disposable learning projection"
            )
        request = deepcopy(imported["authoring_request"])
    else:
        request = read_object(arguments.input)
    if arguments.as_of is not None:
        request["as_of"] = arguments.as_of
    history = (
        read_object(control_path(arguments.events))
        if arguments.events
        else empty_history(request)
    )
    if arguments.review_event:
        history = deepcopy(history)
        history["events"].append(read_object(control_path(arguments.review_event)))
    return imported, request, history


def run_learning(arguments):
    context = QueryContext.load(arguments.local_config, arguments.scope)
    imported, request, history = load_learning_inputs(arguments)
    preview, files = plan_learning(context, request, history)
    if imported is not None and any(
        imported.get(key) != preview["projection"][key]
        for key in ("deck", "scope", "generator", "items", "source_digest")
    ):
        raise ContractError(
            "LEARNING_IMPORT: changed or stale item/provenance data requires a fresh authored review plan"
        )
    if arguments.apply:
        if request["review"]["state"] != "approved":
            raise ContractError(
                "LEARNING_REVIEW: exact plan application requires human approval"
            )
        require_review_authority(request["review"], request["review_authority"])
        if arguments.output_directory is None:
            raise ContractError(
                "LEARNING_OUTPUT: supply a new private projection directory"
            )

        def verify():
            current_import, current, events = load_learning_inputs(arguments)
            if (
                current_import != imported
                or plan_learning(context, current, events)[0] != preview
            ):
                raise ContractError(
                    "LEARNING_STALE: source, review history, scheduler or policy changed"
                )

        changed = apply_generated(
            arguments.output_directory,
            files,
            arguments.plan_digest,
            preview["plan_sha256"],
            check_live=context.check_live,
            verify_inputs=verify,
        )
        result = {
            "status": "created" if changed else "verified-no-op",
            "plan_sha256": preview["plan_sha256"],
        }
    else:
        result = preview
    context.ensure_output(canonical_json(result))
    print(canonical_json(result).decode(), end="")
    return 0
