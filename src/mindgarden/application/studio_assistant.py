"""Prepare one explicitly reviewed local turn and rehearse it with an offline provider."""

from collections.abc import Iterator
from dataclasses import dataclass
import json
import re
from secrets import compare_digest
from typing import Protocol

from ..domain.contracts import canonical_json, digest_bytes, strict_json
from ..domain.validation import ContractError
from .local_federation import ordinary_output_scope, require_private
from .query import QueryContext
from .retrieval import build_index, rank, record_key, render_context


REQUIRED_PROJECTIONS = frozenset({"context", "evidence"})
MAX_QUESTION_LENGTH = 256
MAX_CONTEXT_BYTES = 8192
MAX_OUTPUT_BYTES = 16384
MAX_STREAM_EVENTS = 48
STREAM_ERROR_RESERVE = 256
FOCUS_REFERENCE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*")
APPROVAL_DIGEST = re.compile(r"[a-f0-9]{64}")


@dataclass(frozen=True)
class AssistantInput:
    question: str
    lens: str
    focus: str | None
    records: list[dict]


@dataclass(frozen=True)
class PreparedTurn:
    input: AssistantInput
    preview: dict
    capabilities: frozenset[str]
    approved: bool


class AssistantProvider(Protocol):
    """A local adapter receives only approved data and yields text or citation events."""

    name: str
    capabilities: frozenset[str]

    def events(self, approved: AssistantInput) -> Iterator[dict]: ...


class FixtureAssistant:
    """Reproduce approved notes and their qualifications without a model or tools."""

    name = "fixture"
    capabilities = frozenset({"preview", "stream", "cancel"})

    def events(self, approved: AssistantInput) -> Iterator[dict]:
        if not approved.records:
            yield {"type": "text", "text": "No reviewed evidence matched this question in the selected view."}
            return
        yield {"type": "text", "text": "Offline fixture. This reply quotes the approved reviewed notes.\n"}
        for record in approved.records:
            text = "\n" + record["title"] + "\n" + record["content"]
            if record["caveats"]:
                text += "\nCaveats\n" + "\n".join(record["caveats"])
            if record["uncertainty"]:
                text += "\nOpen questions\n" + "\n".join(record["uncertainty"])
            yield {"type": "text", "text": text + "\n"}
            for citation in record["sources"]:
                yield {"type": "citation", "reference": record["reference"], "citation": citation}


def parse_turn(value: dict, *, run: bool) -> tuple[str, str, str | None]:
    invalid = "ASSISTANT_INVALID: supply a bounded question and supported lens/focus"
    expected = {"question", "lens", "focus"} | ({"preview_sha256"} if run else set())
    if value.keys() != expected:
        raise ContractError(invalid)
    lens, question, focus = value["lens"], value["question"], value["focus"]
    if (
        lens not in ("garden", "finance")
        or not isinstance(question, str)
        or not question.strip()
        or len(question) > MAX_QUESTION_LENGTH
        or not question.isprintable()
        or focus is not None and (not isinstance(focus, str) or len(focus) > 256 or not FOCUS_REFERENCE.fullmatch(focus))
    ):
        raise ContractError(invalid)
    if run and (not isinstance(value["preview_sha256"], str) or not APPROVAL_DIGEST.fullmatch(value["preview_sha256"])):
        raise ContractError(invalid)
    return lens, question, focus


def output_limit(context: QueryContext) -> int:
    budgets = context.session["budgets"]
    return min(MAX_OUTPUT_BYTES, budgets["max_context_bytes"], budgets.get("max_output_bytes", MAX_OUTPUT_BYTES))


def _context_for_turn(context: QueryContext, index: dict, lens: str, question: str, focus: str | None) -> bytes:
    records = index["records"]
    if lens == "finance":
        records = [record for record in records
                   if "financial-records" in record["domains"] or "spending" in record["topics"]]
    if focus is not None:
        selected = [record for record in records if record_key(record["reference"]) == focus]
        if not selected:
            raise ContractError("ASSISTANT_FOCUS: requested focus is unavailable in this view")
    else:
        selected = [result["record"] for result in rank({"records": records}, question)[:3]]
    if not selected:
        return b""
    profile = {
        "schema": "mindgarden.context-profile/v1",
        "id": "studio-assistant",
        "garden": selected[0]["garden"],
        "title": "Studio turn context",
        "description": "Bounded reviewed evidence for an explicitly approved local turn.",
        "query": question,
        "include": [record["reference"] for record in selected],
        "exclude": [],
        "kinds": [],
        "max_items": len(selected),
        "max_bytes": min(MAX_CONTEXT_BYTES, output_limit(context)),
        "max_candidates": len(selected),
    }
    return render_context(context, profile, "json", selected_records=[record_key(item["reference"]) for item in selected])


def prepare_turn(context: QueryContext, provider: AssistantProvider, request: dict, *, run=False) -> PreparedTurn:
    lens, question, focus = parse_turn(request, run=run)
    capabilities = frozenset(provider.capabilities)
    if "preview" not in capabilities:
        raise ContractError("ASSISTANT_UNAVAILABLE: the local fixture cannot prepare a turn")
    require_private(context)
    for projection in sorted(REQUIRED_PROJECTIONS):
        context.require(projection)
    index = build_index(context, projection="context")
    content = _context_for_turn(context, index, lens, question, focus)
    pack = strict_json(content) if content else {"included": [], "scope": ordinary_output_scope(context, [])}
    known = {record_key(record["reference"]): record["title"] for record in index["records"]}
    records = []
    for item in pack["included"]:
        record = {key: item[key] for key in ("reference", "review", "scope", "sources", "content")}
        record["title"] = known[record_key(item["reference"])]
        for key in ("caveats", "uncertainty"):
            record[key] = item["qualifications"][key]
        records.append(record)
    preview = {
        "provider": provider.name,
        "lens": lens,
        "focus": focus,
        "context_bytes": len(canonical_json(records)),
        "scope": pack["scope"],
        "records": records,
    }
    digest = digest_bytes(canonical_json({
        "preview": preview,
        "question": question,
        "provider_capabilities": sorted(capabilities),
        "scope_sha256": context.scope_digest(),
        "authorized_inputs": index["inputs"],
        "context_sha256": digest_bytes(content),
    }))
    if run and not compare_digest(request["preview_sha256"], digest):
        raise ContractError("ASSISTANT_APPROVAL: preview no longer matches this exact turn")
    preview["preview_sha256"] = digest
    response = canonical_json(preview)
    if len(response) > output_limit(context):
        raise ContractError("QUERY_BUDGET: complete assistant preview exceeds its byte budget")
    context.ensure_output(response)
    return PreparedTurn(AssistantInput(question, lens, focus, records), preview, capabilities, run)


def ndjson(event: dict) -> bytes:
    return (json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf8")


def turn_lines(context: QueryContext, provider: AssistantProvider, prepared: PreparedTurn) -> tuple[bytes, ...]:
    """Preflight the deterministic fixture before sending any turn bytes."""
    if (not prepared.approved or provider.name != prepared.preview["provider"]
            or provider.capabilities != prepared.capabilities):
        raise ContractError("ASSISTANT_APPROVAL: prepare and approve the exact current provider input")
    if not {"stream", "cancel"} <= prepared.capabilities:
        raise ContractError("ASSISTANT_UNAVAILABLE: the local fixture cannot stream an approved turn")
    lines = [ndjson({"type": "start", "provider": provider.name})]
    done = ndjson({"type": "done"})
    budget = output_limit(context) - len(done) - STREAM_ERROR_RESERVE
    size = len(lines[0])
    allowed = {
        canonical_json({"type": "citation", "reference": item["reference"], "citation": citation})
        for item in prepared.input.records for citation in item["sources"]
    }
    context.check_live()
    for event in provider.events(prepared.input):
        context.check_live()
        if not isinstance(event, dict):
            raise ContractError("ASSISTANT_UNAVAILABLE: the fixture produced an unsupported event")
        kind = event.get("type")
        plain_text = kind == "text" and event.keys() == {"type", "text"} and isinstance(event["text"], str)
        citation = kind == "citation" and canonical_json(event) in allowed
        if not plain_text and not citation:
            raise ContractError("ASSISTANT_UNAVAILABLE: the fixture produced an unsupported event")
        line = ndjson(event)
        size += len(line)
        if len(lines) >= MAX_STREAM_EVENTS - 1 or size > budget:
            raise ContractError("QUERY_BUDGET: assistant reply exceeds its event or total byte budget")
        lines.append(line)
    if size > budget:
        raise ContractError("QUERY_BUDGET: assistant reply exceeds its total byte budget")
    lines.append(done)
    context.ensure_output(b"".join(lines))
    return tuple(lines)
