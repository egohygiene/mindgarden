"""Strict supplied CSV normalization; no bank-format inference or acquisition."""

import csv
import io

from ..domain.contracts import canonical_json
from ..domain.ledger import FIELDS, transaction_key, validate_row
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError


class LedgerCSVAdapter:
    adapter_id = "ledger-csv"
    version = "1.0.0"
    supported_inputs = frozenset({("text/csv", "1.0.0")})
    limits = {"capture_bytes": 2_000_000, "units": 1000, "unit_bytes": 8192}

    def normalize(self, captured, metadata):
        try:
            text = captured.decode("utf8")
            physical = io.StringIO(text, newline="").readlines()
            offsets = [0]
            for line in physical:
                offsets.append(offsets[-1] + len(line.encode("utf8")))
            reader = csv.reader(io.StringIO(text, newline=""), strict=True)
            header = next(reader)
            if not header:
                raise ValueError()
            header[0] = header[0].removeprefix("\ufeff")
            if tuple(header) != FIELDS:
                raise ValueError()
            units, seen = [], set()
            end_line = reader.line_num
            for record_number, cells in enumerate(reader, 2):
                start_line, end_line = end_line, reader.line_num
                if len(cells) != len(FIELDS) or len(units) >= 1000:
                    raise ValueError()
                row = dict(zip(FIELDS, cells))
                row.update(
                    schema="mindgarden.ledger-row/v1",
                    id=transaction_key(row["account_id"], row["transaction_id"]),
                )
                validate_row(row)
                if row["id"] in seen:
                    raise ContractError(
                        "LEDGER_DUPLICATE: resolve repeated transaction identities within an export"
                    )
                seen.add(row["id"])
                units.append(
                    NormalizedUnit(
                        "ledger:" + row["id"],
                        canonical_json(row),
                        "application/json",
                        metadata={
                            "csv_record": record_number,
                            "original_utf8_span": {
                                "start": offsets[start_line],
                                "end": offsets[end_line],
                            },
                            "header": list(FIELDS),
                        },
                    )
                )
            if not units:
                raise ValueError()
            return NormalizedBundle(
                tuple(units),
                (
                    {
                        "name": "declared-ledger-csv",
                        "version": self.version,
                        "parameters": {
                            "encoding": "UTF-8",
                            "header": list(FIELDS),
                            "date": "ISO-calendar-date",
                            "amount": "signed-decimal-string",
                        },
                    },
                ),
            )
        except (UnicodeError, csv.Error, ValueError, StopIteration, KeyError) as error:
            raise ContractError(
                "LEDGER_FORMAT: supply nonempty UTF-8 CSV with the declared six-column header"
            ) from error
