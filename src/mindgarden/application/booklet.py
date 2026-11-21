"""Printable, explicitly reviewed editions of Willow Garden's fictional ledger."""

from pathlib import Path
import re
from secrets import compare_digest
import sys
from textwrap import wrap

from ..domain.contracts import canonical_json, digest_bytes, strict_json
from ..domain.validation import ContractError
from .consultation import plan_packet


BOOKLET_MONTH = "2026-01"
BOOKLET_PERIOD = {"start": "2026-01-01", "end": "2026-01-31"}
RENDERER = "mindgarden.monthly-booklet-pdf/v1"
REQUEST_SHA256 = "f76f7ffa54d863292a5acfad3d45d2f6ab9a87c90e1416c97a36f4f979fd4a15"
REQUEST_LIMIT = 32 * 1024
LINES_PER_PAGE = 42
SECTION_HEADINGS = {
    "MOVEMENT BY CURRENCY",
    "COVERAGE AND GAPS",
    "LIMITATIONS",
    "SELECTED TRANSACTIONS AND CITATIONS",
    "EVIDENCE APPENDIX",
}


def read_booklet_request() -> dict:
    """Load the exact authored request from the checked-in or installed example."""
    roots = (
        Path(__file__).resolve().parents[3] / "examples/mock-garden",
        Path(sys.prefix) / "share/mindgarden/examples/mock-garden",
    )
    for root in roots:
        path = root / "booklet-request.json"
        try:
            with path.open("rb") as source:
                raw = source.read(REQUEST_LIMIT + 1)
        except FileNotFoundError:
            continue
        except OSError as error:
            raise ContractError(
                "BOOKLET_UNAVAILABLE: the fictional request could not be read"
            ) from error
        if len(raw) <= REQUEST_LIMIT and digest_bytes(raw) == REQUEST_SHA256:
            return strict_json(raw)
        break
    raise ContractError(
        "BOOKLET_UNAVAILABLE: install the exact reviewed Willow booklet fixture"
    )


def report_lines(report: dict):
    yield f"Willow finance booklet | {report['month']}"
    yield "Fictional ledger - private example"
    yield ""
    period = report["period"]
    yield f"Calendar dates: {period['start']} through {period['end']} ({report['timezone']})"
    yield "Amounts below reflect the selected movements. Currency totals stay separate."
    yield ""
    yield "MOVEMENT BY CURRENCY"
    for row in report["totals"]:
        yield f"{row['currency']}"
        yield f"  Income {row['income']}   Expense outflow {row['expense']}   Refunds {row['refund']}"
        yield f"  Transfer net {row['transfer']}   Uncategorized {row['uncategorized']}"
        yield f"  Net movement {row['net_movement']}"
    yield ""
    yield "COVERAGE AND GAPS"
    for item in report["coverage"]:
        account = item["account"]
        first, last = item["observed_first"], item["observed_last"]
        window = f"{first} through {last}" if first else "no supplied transactions"
        yield f"{account}: {window}"
        for interval in item["missing_declared_intervals"]:
            yield f"  Declared coverage gap: {interval['start']} through {interval['end']}"
    yield ""
    yield f"Unresolved classifications: {len(report['unresolved_transactions'])}"
    for question in report["questions"]:
        yield "- " + question
    yield ""
    yield "LIMITATIONS"
    yield from report["limitations"]
    yield ""
    yield "SELECTED TRANSACTIONS AND CITATIONS"
    for item in report["transactions"]:
        yield (
            f"[{item['citation']}] {item['date']} | {item['account']} | "
            f"{item['currency']} {item['amount']} | {item['classification']}"
        )
    yield ""
    yield "EVIDENCE APPENDIX"
    for number, citation in enumerate(report["evidence"], 1):
        source = citation["source"]
        yield f"[E{number:02}] {source['garden']}/{source['id']}"
        yield f"  Revision {source['revision']}"
        yield f"  Locator {citation['locator']}"
        yield f"  SHA-256 {citation['content_sha256']}"


def pdf_text(line: str) -> bytes:
    literal = "".join(
        character if character.isprintable() else " " for character in line
    )
    return (
        literal.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("cp1252", errors="replace")
    )


def print_pdf(report: dict) -> bytes:
    """Render bounded Letter pages with built-in fonts and selectable figures."""
    lines = [
        line
        for text in report_lines(report)
        for line in (wrap(text, width=82, replace_whitespace=True) or [""])
    ]
    pages = [
        lines[start : start + LINES_PER_PAGE]
        for start in range(0, len(lines), LINES_PER_PAGE)
    ]
    children = b" ".join(
        f"{5 + number * 2} 0 R".encode("ascii") for number in range(len(pages))
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [ "
        + children
        + b" ] /Count "
        + str(len(pages)).encode("ascii")
        + b" >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    for number, page in enumerate(pages, 1):
        stream_id = len(objects) + 2
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            + f"/Contents {stream_id} 0 R >>".encode("ascii")
        )
        content = bytearray(
            b"0.89 0.93 0.90 rg 48 716 516 32 re f\n"
            b"0.71 0.78 0.73 RG 0.5 w 48 64 m 564 64 l S\n"
            b"0.14 0.20 0.18 rg\n"
        )
        items = [(727, "F2", 12, f"Willow Garden / {report['month']}")]
        for index, line in enumerate(page):
            if number == 1 and index == 0:
                items.append((698, "F2", 16, line))
            else:
                items.append(
                    (
                        698 - index * 14,
                        "F2" if line in SECTION_HEADINGS else "F1",
                        10,
                        line,
                    )
                )
        items.append(
            (50, "F1", 9, f"Private fictional booklet | Page {number} of {len(pages)}")
        )
        for offset, font, size, line in items:
            content.extend(
                f"BT /{font} {size} Tf 1 0 0 1 56 {offset} Tm (".encode("ascii")
            )
            content.extend(pdf_text(line))
            content.extend(b") Tj ET\n")
        objects.append(
            f"<< /Length {len(content)} >>\nstream\n".encode("ascii")
            + content
            + b"endstream"
        )
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for identity, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{identity} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    start = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets:
        output.extend(f"{offset:010} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return bytes(output)


def prepare_booklet(context, month: str) -> tuple[dict, dict[str, bytes]]:
    context.require("context")
    context.require("source-evidence")
    if month != BOOKLET_MONTH:
        raise ContractError(
            "BOOKLET_UNAVAILABLE: Willow has reviewed inputs only for 2026-01"
        )
    request = read_booklet_request()
    if request.get("period") != BOOKLET_PERIOD:
        raise ContractError(
            "BOOKLET_UNAVAILABLE: the requested month lacks an exact review"
        )
    plan, files = plan_packet(context, request)
    packet = plan["packet"]
    dependencies = strict_json(files["packet-dependencies.json"])
    citations = {
        canonical_json(item): f"E{number:02}"
        for number, item in enumerate(packet["evidence"], 1)
    }
    transactions = [
        {
            "id": item["row"]["id"],
            "date": item["row"]["date"],
            "account": item["row"]["account_id"],
            "currency": item["row"]["currency"],
            "amount": item["row"]["amount"],
            "classification": item["classification"]["category"],
            "paired_with": item["classification"]["paired_with"],
            "citation": citations[canonical_json(item["evidence"])],
        }
        for item in packet["transactions"]
    ]
    represented = {item["source"]["garden"] for item in packet["evidence"]}
    preview = {
        "schema": "mindgarden.monthly-booklet-preview/v1",
        "status": "current",
        "month": month,
        "timezone": "UTC",
        "renderer": RENDERER,
        "fictional": True,
        "period": packet["period"],
        "accounts": request["accounts"],
        "scope": packet["scope"],
        "review": packet["review"],
        "review_authority": packet["review_authority"],
        "totals": packet["totals"],
        "coverage": packet["coverage"],
        "declared_coverage": packet["declared_coverage"],
        "limitations": packet["limitations"],
        "unresolved_transactions": packet["unresolved_transactions"],
        "questions": packet["questions"],
        "evidence": packet["evidence"],
        "transactions": sorted(transactions, key=lambda row: (row["date"], row["id"])),
        "represented_inputs": [
            item
            for item in context.session["readable"]
            if item["garden"] in represented
        ],
        "represented_revision_choices": packet["represented_revision_choices"],
        "packet_plan_sha256": plan["plan_sha256"],
        "inputs_sha256": dependencies["inputs_sha256"],
        "calculation": packet["calculation"],
    }
    pdf = print_pdf(preview)
    preview["pdf_sha256"] = digest_bytes(pdf)
    preview["plan_sha256"] = digest_bytes(canonical_json(preview))
    manifest = canonical_json(
        {**preview, "schema": "mindgarden.monthly-booklet-evidence/v1"}
    )
    artifacts = {"pdf": pdf, "evidence": manifest}
    if (
        sum(map(len, artifacts.values()))
        > context.session["budgets"]["max_context_bytes"]
    ):
        raise ContractError(
            "QUERY_BUDGET: the complete booklet exceeds the session byte budget"
        )
    context.ensure_bundle(artifacts)
    return context.finalize(preview), artifacts


def booklet_preview(context, month: str) -> dict:
    """Preview the exact scope, selected evidence and bytes under current authority."""
    return prepare_booklet(context, month)[0]


def booklet_artifact(
    context, month: str, plan_sha256: str, format: str
) -> tuple[str, bytes]:
    """Recompute before handing approved bytes to the explicit local caller."""
    mime_types = {
        "pdf": "application/pdf",
        "evidence": "application/json; charset=utf-8",
    }
    if not isinstance(format, str) or format not in mime_types:
        raise ContractError("BOOKLET_FORMAT: choose pdf or evidence")
    if not isinstance(plan_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", plan_sha256
    ):
        raise ContractError(
            "BOOKLET_REVIEW: select the current preview and review it again"
        )
    preview, artifacts = prepare_booklet(context, month)
    if not compare_digest(preview["plan_sha256"], plan_sha256):
        raise ContractError(
            "BOOKLET_REVIEW: select the current preview and review it again"
        )
    content = artifacts[format]
    context.ensure_output(content)
    return mime_types[format], content
