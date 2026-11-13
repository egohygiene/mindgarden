# Reviewed local preparation packets

This is the first bounded #90 checkpoint under the selected
[local workflow](local-consultation-workflow.md). It is a private, deterministic
calculation and evidence-export service, not a bank connector, legal decision
engine or completed real-data pilot.

## Input and source identity

`ledger-csv` version 1.0.0 consumes an explicitly declared UTF-8 CSV with the six
columns in the [synthetic fixture](../tests/fixtures/consultation/README.md).
An optional initial UTF-8 BOM and normal CSV quoting/newlines are supported.
Amounts remain signed decimal strings; transaction IDs and account aliases are
supplied, never inferred from similar dates or amounts. The adapter preserves
the original CSV in the existing vault and emits exact normalized row sources.
Original UTF-8 byte spans and CSV record numbers remain in adapter metadata.

Use the ordinary source plan/apply command, with your explicit private bindings:

```sh
mindgarden ingest --repository-root /private/garden --local-config /private/bindings.json \
  --vault-id private-sources --input /private/declared-ledger.csv \
  --source-id selected-export --title "Selected declared export" \
  --origin urn:example:selected-export --captured 2026-11-13T00:00:00Z \
  --owner local-owner --rights "Explicitly supplied local material" \
  --media-type text/csv --adapter ledger-csv --manifest-version 1.0.0
```

Inspect the result and repeat with `--apply --plan-digest SHA256`. Changing the
file, adapter, metadata or target invalidates that digest. Unchanged overlapping
rows reuse normalized evidence; original exports and observation lineage remain.
This format does not claim arbitrary bank CSV, debit/credit-column, localized
amount/date or multi-sheet spreadsheet compatibility.

## Review and exact calculations

The versioned [request contract](../contracts/v1/consultation-request.schema.json)
selects exact normalized evidence, expected accounts/period, currency precision,
coverage declarations, classifications, represented-revision choices, selected
display rows, evidence attachments and questions. A
[concrete synthetic request](../tests/fixtures/contracts/v1/valid/consultation-request.json)
shows its structure; its fixture references are not authority to read real data.

Use an ordinary personal/offline/never-exportable session with exact source
grants as defined by [the source evidence boundary](extraction-producers.md).
Unreviewed source grants permit evidence inspection without approving knowledge.
The request requires explicit human review of classification/selection. Every
transaction is classified once, including unresolved items; transfers need
reciprocal reviewed equal-and-opposite same-currency pairs across accounts.
Conflicting revisions require an explicit exact source choice. No exchange rate,
category, balance, account coverage or legal conclusion is guessed.

`packet` exposes the complete calculated report in its private preview, alongside
the file inventory and digest. Inspect it before applying:

```sh
mindgarden packet --local-config /private/bindings.json --scope /private/session.json \
  --input /private/reviewed-request.json --output-directory /private/packet-01
```

Repeat with `--apply --plan-digest SHA256`; `--check` verifies the existing exact
bundle against current authority and inputs. Changed sources, review, questions,
selection or live authority invalidate reuse. The complete inventory, including
ownership metadata, fits both the explicit request and session limits. Sources,
grants and scope are checked before reads; expiry/revocation is checked again
before output and writes.

Outputs are `packet.json`, literal source-safe `packet.md`, the reviewed request
and explicitly selected normalized evidence rows, all mode 0600 in a new mode
0700 private directory. Existing different/unknown files are retained. Partial
attempts remain inspectable; retry into a new private directory after fresh
verification. No raw statements/PDFs, public export or automatic sharing is
implemented by this command. Original files remain in the private source vault.

## Synthetic proof and remaining scope

```sh
python -S scripts/consultation_demo.py --workspace /tmp/new-synthetic-consultation \
  --require-source --check-golden
python -m unittest tests.test_consultation tests.test_v1_contracts \
  tests.test_scope_bundle_outputs tests.test_source_adapters --quiet
```

The committed [proof](../tests/fixtures/consultation/expected-proof.json) records
eight unique transactions across overlapping exports, 11 retained immutable
objects, reviewed transfer pairs, explicit uncertainty/coverage and independently
expected net movement USD 2259.76. A separately authored reviewed garden summary
is searchable with exact evidence and a 6,128-byte context pack. Source review
stays unreviewed; kept knowledge remains epistemically proposed. Vault relocation,
restore and clean rebuild reproduce the exact packet/index/context/evidence.
Network, HTTP, external processes and models are blocked in this proof.

The wider parent retains arbitrary bank-format adapters, richer reconciliation
and analysis, source-backed balances/assets/liabilities, raw selected attachments,
optional chart/PDF/UI consumers and an approved real private pilot. Drive and
Codex integrations consume these same services in subsequent checkpoints. The
restricted-document/runtime gate remains unchanged; personal documents are not
silently reclassified to make this demonstration pass.

## Reviewed alternate CSV layouts

The [explicit mapping adapter](csv-ledger-mappings.md) now feeds the same ledger and packet services from two authored synthetic layouts. It preserves exact original spans and reviewed configuration, while the packet retains independent source grants, classifications, revisions and export review. Strict declared CSV remains compatible; arbitrary bank/PDF formats and real pilot acceptance remain open.
