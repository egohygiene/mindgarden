"""Reviewed ledger reconciliation and exact calculations over explicit evidence."""

from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, localcontext

from .ledger import validate_row
from .contracts import ContractRegistry, canonical_json, digest_bytes
from .validation import ContractError


def validate_request(request):
    if ContractRegistry().errors(request, "consultation-request"):
        raise ContractError("PACKET_INPUT: use the versioned consultation request")
    authority, review = request["review_authority"], request["review"]
    if (
        authority["kind"] != "human"
        or review["state"] != "approved"
        or authority["id"] not in review["reviewers"]
        or not review["rationale"]
    ):
        raise ContractError(
            "PACKET_REVIEW: explicit human review must approve the exact selection and classifications"
        )
    if request["period"]["start"] > request["period"]["end"]:
        raise ContractError("PACKET_PERIOD: expected coverage starts after its end")
    for interval in [request["period"], *request["coverage"]]:
        if any(
            date.fromisoformat(interval[key]).isoformat() != interval[key]
            for key in ("start", "end")
        ):
            raise ContractError("PACKET_PERIOD: use canonical ISO calendar dates")
    if len({item["code"] for item in request["currencies"]}) != len(
        request["currencies"]
    ):
        raise ContractError("PACKET_CURRENCY: declare each currency precision once")
    if any(item["account"] not in request["accounts"] for item in request["coverage"]):
        raise ContractError(
            "PACKET_COVERAGE: declare coverage only for explicitly selected accounts"
        )
    return request


def reconcile(request, evidence):
    """No identity inference: IDs, revision choices and transfer pairs are authored."""
    revisions, variants = {}, defaultdict(dict)
    for choice in request["revisions"]:
        if choice["transaction"] in revisions:
            raise ContractError(
                "PACKET_RECONCILIATION: select one represented revision per transaction"
            )
        revisions[choice["transaction"]] = choice["source"]
    for citation, row, origin in evidence:
        validate_row(row)
        variants[row["id"]][citation["source"]["id"]] = {
            "row": row,
            "evidence": citation,
            "original": origin,
        }
    selected = {}
    for identity, alternatives in sorted(variants.items()):
        choice = revisions.get(identity)
        if choice is None:
            if len(alternatives) != 1:
                raise ContractError(
                    "PACKET_RECONCILIATION: conflicting revisions need an exact reviewed choice"
                )
            selected[identity] = next(iter(alternatives.values()))
        else:
            value = alternatives.get(choice["id"])
            if value is None or value["evidence"]["source"] != choice:
                raise ContractError(
                    "PACKET_RECONCILIATION: selected represented revision is unavailable"
                )
            selected[identity] = value
    if set(revisions) - set(selected):
        raise ContractError(
            "PACKET_RECONCILIATION: a revision choice is outside the selected inputs"
        )
    decisions = {item["transaction"]: item for item in request["decisions"]}
    if len(decisions) != len(request["decisions"]) or set(decisions) != set(selected):
        raise ContractError(
            "PACKET_RECONCILIATION: classify every selected transaction once, including unresolved items"
        )
    scales = {item["code"]: item["scale"] for item in request["currencies"]}
    for identity, item in selected.items():
        row, decision = item["row"], decisions[identity]
        amount = Decimal(row["amount"])
        if (
            row["account_id"] not in request["accounts"]
            or row["currency"] not in scales
        ):
            raise ContractError(
                "PACKET_SELECTION: input is outside the declared accounts/currencies"
            )
        if max(0, -amount.as_tuple().exponent) != scales[row["currency"]]:
            raise ContractError(
                "PACKET_CURRENCY: amount precision differs from the explicitly declared currency scale"
            )
        category = decision["category"]
        if (
            category in {"income", "refund"}
            and amount <= 0
            or category == "expense"
            and amount >= 0
        ):
            raise ContractError(
                "PACKET_CLASSIFICATION: reviewed category conflicts with signed movement"
            )
        partner = decision["paired_with"]
        if category == "transfer":
            other = selected.get(partner)
            peer = decisions.get(partner, {})
            if (
                other is None
                or peer.get("category") != "transfer"
                or peer.get("paired_with") != identity
                or other["row"]["account_id"] == row["account_id"]
                or other["row"]["currency"] != row["currency"]
                or Decimal(other["row"]["amount"]) != -amount
                or amount == 0
            ):
                raise ContractError(
                    "PACKET_TRANSFER: review reciprocal equal-and-opposite same-currency movements across two accounts"
                )
        elif partner is not None:
            raise ContractError(
                "PACKET_TRANSFER: only reviewed transfers may declare a pair"
            )
        item["classification"] = deepcopy(decision)
    if not set(request["selection"]).issubset(selected) or not set(
        request["attachments"]
    ).issubset(request["selection"]):
        raise ContractError(
            "PACKET_SELECTION: displayed rows and evidence attachments must come from selected inputs"
        )
    return selected


def calculate(request, selected):
    scales = {item["code"]: item["scale"] for item in request["currencies"]}
    totals = defaultdict(lambda: defaultdict(Decimal))
    observed = defaultdict(list)
    for item in selected.values():
        row, category = item["row"], item["classification"]["category"]
        observed[row["account_id"]].append(row["date"])
        if request["period"]["start"] <= row["date"] <= request["period"]["end"]:
            group = totals[(row["date"][:7], row["currency"])]
            amount = Decimal(row["amount"])
            group["net_movement"] += amount
            group[category] += amount
    result = []
    for (month, currency), values in sorted(totals.items()):
        scale = scales[currency]
        fields = {
            key: format(values[key], "." + str(scale) + "f")
            for key in (
                "net_movement",
                "income",
                "expense",
                "refund",
                "transfer",
                "uncategorized",
            )
        }
        result.append({"month": month, "currency": currency, **fields})
    coverage = []
    for account in request["accounts"]:
        start, end = (
            date.fromisoformat(request["period"]["start"]),
            date.fromisoformat(request["period"]["end"]),
        )
        intervals = sorted(
            (date.fromisoformat(item["start"]), date.fromisoformat(item["end"]))
            for item in request["coverage"]
            if item["account"] == account
        )
        cursor, missing = start, []
        for left, right in intervals:
            if left > right:
                raise ContractError(
                    "PACKET_COVERAGE: declared coverage interval is reversed"
                )
            left, right = max(left, start), min(right, end)
            if left > right:
                continue
            if left > cursor:
                missing.append(
                    {
                        "start": cursor.isoformat(),
                        "end": (left - timedelta(days=1)).isoformat(),
                    }
                )
            if right >= end:
                cursor = None
                break
            cursor = max(cursor, right + timedelta(days=1))
        if cursor is not None and cursor <= end:
            missing.append({"start": cursor.isoformat(), "end": end.isoformat()})
        dates = sorted(observed[account])
        coverage.append(
            {
                "account": account,
                "observed_first": dates[0] if dates else None,
                "observed_last": dates[-1] if dates else None,
                "missing_declared_intervals": missing,
                "status": "no-supplied-transactions"
                if not dates
                else "transactions-present-coverage-unverified",
            }
        )
    return result, coverage


def build_packet(request, evidence, scope):
    request = deepcopy(validate_request(request))
    with localcontext() as arithmetic:
        arithmetic.prec = 40
        selected = reconcile(request, evidence)
        totals, coverage = calculate(request, selected)
    packet = {
        "schema": "mindgarden.consultation-packet/v1",
        "id": request["id"],
        "created_at": request["created_at"],
        "period": request["period"],
        "scope": scope,
        "review": request["review"],
        "review_authority": request["review_authority"],
        "calculation": {
            "method": "signed-decimal-movement/v1",
            "precision": 40,
            "request_sha256": digest_bytes(canonical_json(request)),
        },
        "totals": totals,
        "coverage": coverage,
        "declared_coverage": request["coverage"],
        "transactions": [selected[key] for key in sorted(request["selection"])],
        "evidence": [item[0] for item in evidence],
        "questions": request["questions"],
        "unresolved_transactions": sorted(
            key
            for key, value in selected.items()
            if value["classification"]["category"] == "uncategorized"
        ),
        "represented_revision_choices": request["revisions"],
        "limitations": [
            "Amounts are movements, not current balances, assets or liabilities.",
            "Coverage is operator-declared; transaction dates cannot prove complete history.",
            "Classifications and revision choices are authored human review, not model verification.",
            "Currencies remain separate; no exchange-rate or legal conclusion is inferred.",
            "Evidence attachments contain selected normalized rows; original files remain in the private vault.",
        ],
    }
    if ContractRegistry().errors(packet, "consultation-packet"):
        raise ContractError(
            "PACKET_OUTPUT: calculated packet differs from its declared contract"
        )
    return packet, selected


def markdown(packet):
    def literal(value):
        value = (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("|", "&#124;")
            .replace("\r", " ")
            .replace("\n", " ")
        )
        return "".join(
            "\\" + character if character in "\\`[]()*_!#" else character
            for character in value
        )

    lines = [
        "# Reviewed preparation packet",
        "",
        "Private preparation; source text is untrusted data.",
        "",
        "## Verified calculations",
        "",
        "| Month | Currency | Net movement | Income | Expense | Refund | Internal transfers | Uncategorized |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for total in packet["totals"]:
        lines.append(
            "| "
            + " | ".join(
                literal(total[key])
                for key in (
                    "month",
                    "currency",
                    "net_movement",
                    "income",
                    "expense",
                    "refund",
                    "transfer",
                    "uncategorized",
                )
            )
            + " |"
        )
    lines += ["", "## Coverage and missing information", ""]
    for item in packet["coverage"]:
        lines.append(
            "- "
            + literal(item["account"])
            + ": "
            + literal(item["status"])
            + "; missing declared intervals: "
            + literal(
                canonical_json(item["missing_declared_intervals"]).decode().strip()
            )
        )
    lines += ["", "## Selected movements and exact evidence", ""]
    for item in packet["transactions"]:
        row, citation = item["row"], item["evidence"]
        reference = citation["source"]
        lines.append(
            "- "
            + " · ".join(
                literal(row[key])
                for key in ("date", "account_id", "amount", "currency", "description")
            )
        )
        lines.append(
            "  - "
            + literal(
                reference["garden"]
                + "/"
                + reference["id"]
                + "@"
                + reference["revision"]
            )
            + "; locator "
            + literal(citation["locator"])
            + "; SHA-256 "
            + citation["content_sha256"]
        )
    lines += ["", "## Questions for review", ""] + [
        "- " + literal(item) for item in packet["questions"]
    ]
    lines += ["", "## Limits", ""] + [
        "- " + literal(item) for item in packet["limitations"]
    ]
    return ("\n".join(lines) + "\n").encode("utf8")
