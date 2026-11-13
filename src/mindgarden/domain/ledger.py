"""Portable ledger-row identity and validation, independent of CSV or storage."""

from datetime import date
import re

from .contracts import canonical_json, digest_bytes
from .validation import ContractError

FIELDS = ("transaction_id", "account_id", "date", "amount", "currency", "description")
AMOUNT = re.compile(r"-?(?:0|[1-9][0-9]{0,15})(?:\.[0-9]{1,6})?\Z")


def transaction_key(account, transaction):
    return "transaction-" + digest_bytes(canonical_json([account, transaction]))[:32]


def validate_row(row):
    if (
        not isinstance(row, dict)
        or set(row) != {"schema", "id", *FIELDS}
        or row["schema"] != "mindgarden.ledger-row/v1"
        or any(not isinstance(row[key], str) for key in row)
        or not all(0 < len(row[key]) <= 128 for key in ("account_id", "transaction_id"))
        or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", row["account_id"])
        or len(row["description"]) > 4096
        or not AMOUNT.fullmatch(row["amount"])
        or not re.fullmatch(r"[A-Z]{3}", row["currency"])
        or row["id"] != transaction_key(row["account_id"], row["transaction_id"])
    ):
        raise ContractError(
            "LEDGER_FORMAT: use the declared ledger CSV fields and exact decimal strings"
        )
    try:
        if date.fromisoformat(row["date"]).isoformat() != row["date"]:
            raise ValueError()
    except ValueError as error:
        raise ContractError("LEDGER_DATE: supply an ISO calendar date") from error
    return row
