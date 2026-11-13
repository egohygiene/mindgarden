# Reviewed CSV ledger mappings

`mapped-ledger-csv` normalizes explicitly supplied UTF-8 CSV through the existing
source/vault boundary. It emits the existing `ledger-row/v1`; the packet service
still owns source grants, reviewed revisions/classifications, exact-decimal
calculations and selected output. There is no bank connection or model call.

## Explicit configuration

The [mapping schema](../contracts/v1/ledger-csv-mapping.schema.json) declares:

- An exact ordered header with distinct names; unexpected columns fail.
- Transaction ID, date and description columns.
- Account/currency columns or explicit literal values.
- Signed decimals, or separate nonnegative debit/credit columns with exactly one
  populated per row.
- `YYYY-MM-DD` or zero-padded `MM/DD/YYYY`, plus an explicit posted/transaction
  calendar-date meaning. No timezone, exchange rate or date order is inferred.
- Version and explicit human review of the normalization semantics.

See synthetic [signed layout A](../tests/fixtures/consultation/mappings/layout-a.json)
and [debit/credit layout B](../tests/fixtures/consultation/mappings/layout-b.json).
Only declared transformations run; mappings cannot contain executable code.
Currency signs, thousands separators, formulas, scientific notation, missing
transaction IDs and other formats remain unsupported rather than guessed.

```sh
mindgarden ingest --repository-root /private/garden \
  --local-config /private/bindings.json --vault-id source-vault \
  --input /private/supplied-export.csv --source-id chosen-export \
  --title "Explicitly selected export" --origin urn:private:selected-export \
  --captured 2026-11-13T00:00:00Z --owner local-owner \
  --rights "User-supplied records" --media-type text/csv \
  --adapter mapped-ledger-csv --manifest-version mapping-v1 \
  --ledger-mapping /private/reviewed-mapping.json
```

Review the preview. Repeat the same inputs with `--apply --plan-digest SHA256`.
`mapping-v1` names this normalization input profile, not a bank/archive
specification. Strict `ledger-csv` / `1.0.0` remains the default for its declared
input; unsupported or unconfigured mapped input fails closed. V0 rejects the new
option rather than silently ignoring it.

## Identity, evidence and review

Original CSV bytes are immutable vault objects. Each row keeps its exact UTF-8
byte span, physical CSV record, header and mapping revision. BOM, CRLF, quoted
multiline text and Unicode do not turn character offsets into byte offsets.
The canonical reviewed mapping is preserved in normalization provenance; local
mapping filenames/paths do not enter portable records.

Transaction IDs remain `(account, transaction ID)`. Normalized-source identity
also binds the canonical mapping revision, separately from row content identity.
A changed interpretation cannot relabel an existing source whose bytes normalize
identically. Vault content still deduplicates. Repeated/overlapping exports under
the same mapping reuse unchanged evidence; competing interpretations require
the packet's explicit reviewed revision selection.

The preview binds the supplied mapping-file digest. Changed config, source,
target or scope invalidates apply before originals are written. Mapping review
does not approve knowledge, categories, transfers or publication. The packet
still needs its separate human review and source grants.

## Synthetic checkpoint and limits

Two layouts plus overlap reproduce eight selected transactions and exact 2259.76
movement, preserving original spans/configuration. The packet rebuilds
byte-identically after export/restore/rebinding to a clean vault, with the old
vault and mapping filenames moved aside and retained.

This is bounded format support, not arbitrary bank/PDF interpretation, complete
accounting, live-data validation or an approved private pilot. Broader correction/
freshness, accounting, balances/assets and optional UI/PDF outputs remain parent
scope. [The sprint ledger](freshness-mapping-sprint.md) records exact branches,
tests, CI, dependencies and remaining work.
