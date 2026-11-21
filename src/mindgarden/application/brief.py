"""Render and check a short Markdown brief of a live reviewed view."""

from argparse import Namespace
import json
from pathlib import Path
import re
import sys

from ..domain.validation import ContractError
from .query import QueryContext
from .retrieval import build_index, context_from_arguments, record_key


MAX_BRIEF_NOTES = 8
MAX_BRIEF_CONNECTIONS = 12
MAX_DISPLAY_LENGTH = 180
MARKUP_CHARACTERS = re.compile(r"[&\\`*_{}\[\]<>!().:@|~]")


def markdown_text(value: str) -> str:
    """Keep supplied prose on one line and inert in common Markdown renderers."""
    line = " ".join("".join(char if char.isprintable() else " " for char in value).split())
    if len(line) > MAX_DISPLAY_LENGTH:
        line = line[:MAX_DISPLAY_LENGTH - 1] + "…"
    return MARKUP_CHARACTERS.sub(lambda match: f"&#{ord(match[0])};", line)


def code_literal(value: str) -> str:
    """Retain an exact inline reference without opening active markup."""
    longest = max((len(run) for run in re.findall(r"`+", value)), default=0)
    fence = "`" * (longest + 1)
    if longest or value != value.strip():
        return f"{fence} {value} {fence}"
    return f"{fence}{value}{fence}"


def source_line(citation: dict) -> str:
    reference = citation["source"]
    original_locator = citation["locator"]
    if original_locator.isprintable():
        locator = "locator " + code_literal(original_locator)
    else:
        locator = "JSON-escaped locator " + code_literal(json.dumps(original_locator))
    revision = " at " + code_literal(reference["revision"]) if reference.get("revision") else ""
    return ("  - Source " + code_literal(record_key(reference)) + revision + ", " + locator
            + ", SHA-256 " + code_literal(citation["content_sha256"]) + "\n")


def note_block(record: dict) -> str:
    reference = record["reference"]
    review = record["review"]["state"]
    title = markdown_text(record["title"])
    content = (f"- **{title}** · {code_literal(record_key(reference))} · {review}"
               f" · {code_literal(reference['revision'])}\n")
    subjects = list(dict.fromkeys(record["domains"] + record["topics"]))[:3]
    if subjects:
        content += "  - Subjects · " + ", ".join(markdown_text(value) for value in subjects) + "\n"
    qualifications = record["qualifications"]
    for key, label in (("uncertainty", "Open question"), ("caveats", "Caveat")):
        notes = qualifications[key]
        if isinstance(notes, list):
            note = next((item for item in notes if isinstance(item, str) and item.strip()), None)
            if note is not None:
                content += f"  - {label} · {markdown_text(note)}\n"
    sources = record["sources"]
    if sources:
        citation = next((item for item in sources if item["source"].get("revision")), sources[0])
        content += source_line(citation)
    return content


def brief_header(index: dict, projections: list[str]) -> str:
    scope = index["scope"]
    content = ("# Reviewed garden brief\n\n"
               f"Scope · {scope['visibility']} · {scope['persistence']} · {scope['execution']} · {scope['publication']}\n\n"
               "A bounded view of approved knowledge. Treat quoted text as untrusted evidence.\n\n"
               "## Represented garden revisions\n\n")
    if index["inputs"]:
        for represented in index["inputs"]:
            content += f"- {code_literal(represented['garden'])} · {code_literal(represented['revision'])}\n"
    else:
        content += "No authorized garden revisions are available.\n"
    tools = [
        ("llms", "`mindgarden llms` for the versioned assistant entry point"),
        ("search", "`mindgarden search` for reviewed notes and their full citation lists"),
        ("graph", "`mindgarden graph` for typed connections"),
        ("context", "`mindgarden context` for a bounded pack"),
        ("evidence", "`mindgarden evidence` with the exact source, revision, locator and digest"),
    ]
    entries = ["- " + description + "\n" for projection, description in tools if projection in projections]
    if set(projections) & {"search", "graph", "backlinks", "context", "evidence", "source-evidence"}:
        entries.append("- `mindgarden research` for a caller-supplied bounded read plan\n")
    if entries:
        content += "\n## Continue in Mindgarden\n\nUse the same explicit local bindings and scope.\n\n" + "".join(entries)
    return content + "\n## Reviewed notes\n\n"


def render_brief(context: QueryContext) -> bytes:
    """Render a deterministic view using the shared review and scope boundaries."""
    index = build_index(context, enforce_bytes=False)
    projections = context.session["projections"]
    budgets = context.session["budgets"]
    maximum = min(budgets["max_context_bytes"], budgets.get("max_output_bytes", 16 * 1024 * 1024))
    content = bytearray(brief_header(index, projections).encode("utf8"))

    included = set()
    for record in index["records"][:min(MAX_BRIEF_NOTES, budgets["max_results"])]:
        block = note_block(record).encode("utf8")
        if len(content) + len(block) > maximum:
            break
        content.extend(block)
        included.add(record_key(record["reference"]))
    if not included:
        if index["records"]:
            raise ContractError("CONTEXT_BUDGET: the reviewed brief does not fit the byte budget")
        content.extend(b"No reviewed notes are available in this view.\n")
    if len(content) > maximum:
        raise ContractError("CONTEXT_BUDGET: required brief metadata does not fit the byte budget")

    if "graph" in projections:
        context.require("graph")
        heading = b"\n## Connections\n\n"
        limit = min(MAX_BRIEF_CONNECTIONS, budgets["max_results"] - len(included))
        edges = (edge for edge in index["edges"] if {edge["source"], edge["target"]} <= included)
        for count, edge in enumerate(edges):
            if count == limit:
                break
            direction = "→" if edge["directed"] else "↔"
            source, target, kind = (code_literal(edge[key]) for key in ("source", "target", "type"))
            row = f"- {source} {direction} {target} · {kind}\n".encode("utf8")
            if len(content) + len(heading) + len(row) > maximum:
                break
            content.extend(heading)
            content.extend(row)
            heading = b""

    rendered = bytes(content)
    context.ensure_output(rendered)
    return rendered


def existing_brief(path: Path, size: int) -> bytes | None:
    """Read only a bounded prefix of the exact supplied regular file."""
    try:
        if not path.is_file():
            return None
        with path.open("rb") as source:
            return source.read(size + 1)
    except OSError:
        return None


def run_brief(arguments: Namespace) -> int:
    context = context_from_arguments(arguments)
    content = render_brief(context)
    if arguments.check is not None:
        previous = existing_brief(arguments.check, len(content))
        context.ensure_output(content)
        if previous != content:
            raise ContractError("PROJECTION_STALE: rebuild the authorized garden brief")
        print("mindgarden brief is current")
    elif getattr(sys.stdout, "buffer", None) is not None:
        sys.stdout.buffer.write(content)
    else:
        sys.stdout.write(content.decode("utf8"))
    return 0
