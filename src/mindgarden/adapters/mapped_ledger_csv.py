"""Reviewed, closed CSV mappings over the existing portable ledger-row contract."""

from copy import deepcopy
import csv
from datetime import datetime
import io

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes
from ..domain.ledger import AMOUNT, transaction_key, validate_row
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError


def validate_mapping(mapping):
    if ContractRegistry().errors(mapping, "ledger-csv-mapping"):
        raise ContractError(
            "LEDGER_MAPPING: supply the supported explicit mapping contract"
        )
    review = mapping["review"]
    if (
        review["state"] != "approved"
        or mapping["review_authority"]["id"] not in review["reviewers"]
        or not review["reviewed_at"]
        or not review["rationale"]
    ):
        raise ContractError(
            "LEDGER_MAPPING_REVIEW: explicit human review must approve normalization semantics"
        )
    header = mapping["header"]
    columns = [
        mapping["fields"][field] for field in ("transaction_id", "date", "description")
    ]
    columns += [
        value["column"]
        for value in mapping["fields"].values()
        if isinstance(value, dict) and "column" in value
    ]
    columns += [value for field, value in mapping["amount"].items() if field != "mode"]
    if not set(columns) <= set(header):
        raise ContractError(
            "LEDGER_MAPPING: every selected column must belong to the declared exact header"
        )
    return mapping


def amount_value(row, mapping):
    if mapping["mode"] == "signed":
        return row[mapping["column"]]
    debit, credit = row[mapping["debit_column"]], row[mapping["credit_column"]]
    if bool(debit) == bool(credit):
        raise ContractError(
            "LEDGER_MAPPING_AMOUNT: exactly one nonnegative debit or credit value is required"
        )
    value = debit or credit
    if not AMOUNT.fullmatch(value) or value.startswith("-"):
        raise ContractError(
            "LEDGER_MAPPING_AMOUNT: debit/credit cells require exact nonnegative decimal strings"
        )
    return "-" + value if debit else value


class MappedLedgerCSVAdapter:
    adapter_id = "mapped-ledger-csv"
    version = "1.0.0"
    # A distinct declared normalization profile preserves legacy CSV selection.
    supported_inputs = frozenset({("text/csv", "mapping-v1")})
    limits = {"capture_bytes": 2_000_000, "units": 1000, "unit_bytes": 8192}

    def normalize(self, captured, metadata):
        mapping = deepcopy(validate_mapping(metadata.get("ledger_mapping")))
        revision = "sha256:" + digest_bytes(canonical_json(mapping))
        try:
            text = captured.decode("utf8")
            offsets = [0]
            for line in io.StringIO(text, newline="").readlines():
                offsets.append(offsets[-1] + len(line.encode("utf8")))
            reader = csv.reader(io.StringIO(text, newline=""), strict=True)
            header = next(reader)
            if not header:
                raise ValueError()
            header[0] = header[0].removeprefix("\ufeff")
            if header != mapping["header"]:
                raise ContractError(
                    "LEDGER_MAPPING_HEADER: captured header differs from the reviewed layout"
                )
            units, seen = [], set()
            previous_line = reader.line_num
            for number, cells in enumerate(reader, 2):
                start_line, previous_line = previous_line, reader.line_num
                if len(cells) != len(header) or len(units) >= 1000:
                    raise ValueError()
                supplied = dict(zip(header, cells))
                fields = mapping["fields"]
                row = {
                    key: supplied[fields[key]]
                    for key in ("transaction_id", "date", "description")
                }
                for key in ("account_id", "currency"):
                    selector = fields[key]
                    row[key] = (
                        selector["value"]
                        if "value" in selector
                        else supplied[selector["column"]]
                    )
                if mapping["date_format"] == "MM/DD/YYYY":
                    parsed = datetime.strptime(row["date"], "%m/%d/%Y")
                    if parsed.strftime("%m/%d/%Y") != row["date"]:
                        raise ValueError()
                    row["date"] = parsed.date().isoformat()
                row.update(
                    schema="mindgarden.ledger-row/v1",
                    id=transaction_key(row["account_id"], row["transaction_id"]),
                    amount=amount_value(supplied, mapping["amount"]),
                )
                validate_row(row)
                if row["id"] in seen:
                    raise ContractError(
                        "LEDGER_DUPLICATE: resolve repeated transaction identities within an export"
                    )
                seen.add(row["id"])
                units.append(
                    NormalizedUnit(
                        "ledger:" + row["id"] + ":mapping:" + revision[7:],
                        canonical_json(row),
                        "application/json",
                        metadata={
                            "csv_record": number,
                            "original_utf8_span": {
                                "start": offsets[start_line],
                                "end": offsets[previous_line],
                            },
                            "header": header,
                            "mapping_revision": revision,
                            "date_semantics": mapping["date_semantics"],
                        },
                    )
                )
            if not units:
                raise ValueError()
            return NormalizedBundle(
                tuple(units),
                (
                    {
                        "name": "reviewed-ledger-csv-mapping",
                        "version": self.version,
                        "parameters": {
                            "mapping_revision": revision,
                            "mapping": mapping,
                            "encoding": "UTF-8",
                        },
                    },
                ),
                metadata={"mapping_revision": revision, "mapping": mapping},
            )
        except (UnicodeError, csv.Error, ValueError, StopIteration, KeyError) as error:
            raise ContractError(
                "LEDGER_MAPPING_FORMAT: captured rows do not match the reviewed date/column/decimal contract"
            ) from error
