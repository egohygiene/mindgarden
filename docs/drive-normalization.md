# Reviewed per-file normalization of Drive captures

This bounded #87/#90 checkpoint connects the existing
[captured Drive adapter](drive-capture.md) to the
[reviewed CSV mapping adapter](csv-ledger-mappings.md). It consumes already
captured bytes. It does not connect to Google, infer bank formats, run a model,
change source classification or approve knowledge.

## Select mappings by stable provider identity

The versioned [configuration](../contracts/v1/drive-normalization.schema.json)
contains an explicitly human-reviewed list of provider file IDs and embedded
`ledger-csv-mapping/v1` definitions. Each embedded mapping has its own human
review of header, date, account/currency and amount semantics. Review of a
mapping alone does not authorize applying it to an arbitrary file.

The [synthetic configuration](../tests/fixtures/consultation/mappings/drive-normalization.json)
maps two signed ISO-date exports, including overlap, and one debit/credit
US-date export. IDs are fictional. Replace them only with an explicitly selected
local configuration; fixture review is not authority for real data.

Add the new option to the ordinary digest-bound captured-source import:

```sh
mindgarden ingest --repository-root /private/garden \
  --local-config /private/bindings.json --vault-id source-vault \
  --input /private/capture-01/capture.zip --source-id selected-collection \
  --title "Selected captured collection" --origin urn:private:collection \
  --captured 2026-11-13T00:00:00Z --owner local-owner \
  --rights "Explicitly selected private sources" \
  --media-type application/vnd.mindgarden.drive-capture+zip \
  --adapter drive-capture --manifest-version 1.0.0 \
  --source-scope /private/capture-01/source-scope.json \
  --drive-normalization /private/reviewed-drive-normalization.json
```

Inspect the preview and repeat with `--apply --plan-digest SHA256`. Changed
capture/configuration bytes, target or bindings invalidate the reviewed plan
before any new source write. The config file is bounded to 262,144 bytes, at most
64 mapped provider IDs and the existing supported CSV semantics. Normalization
is bounded to 1,000 units; mapped capture provenance also caps total occurrences,
including duplicates, at 1,000 so overlap cannot expand metadata without limit.

Every selected mapping must match a currently captured CSV provider identity.
Unknown, repeated, missing or non-CSV targets fail with fixed diagnostics rather
than guessing or silently skipping a mapping. If a source disappears, retain its
old capture and review the changed source/configuration/coverage explicitly.
Unmapped CSV files retain the strict declared-ledger reader; plain text and
preserved-only media retain their prior behavior. V0 and unrelated adapters
reject the new option rather than ignoring it.

## Evidence, currentness and recovery

Original captures and member bytes remain immutable. Normalized row content
identity, mapping revision and provider location remain separate. Each mapped
row retains its primary provider ID/version, original ZIP member/checksum, raw
UTF-8 span, header, record and mapping revision. `provider_occurrences` retains
those exact details for every overlapping occurrence within the supplied capture.
The canonical config and file-to-mapping associations remain in normalization
provenance; machine-local config filenames and credentials do not.

Unchanged replay reuses normalized evidence and original attribution while
retaining new capture/provenance observations. A changed row yields new evidence;
the [packet currentness comparison](consultation-packets.md#compare-an-earlier-packet-with-current-selected-inputs)
marks a current reviewed request stale against its earlier manifest. The
operator still selects exact corrections and reviews reconciliation. Capturing
new bytes cannot silently choose a transaction revision or approve sharing.

The [complete synthetic proof](../tests/fixtures/consultation/expected-mapped-drive-proof.json)
uses ordinary CLI capture/import/review/search/context and vault relocation,
restore and clean rebuild. Two layouts and three files contain nine row
occurrences, reconcile to eight transactions and exactly USD 2259.76 net
movement. All original snapshots remain. Focused adversaries cover stale config,
unapproved/unknown/duplicate mappings, partial capture recovery, missing selected
files, occurrence limits and a correction to USD 2159.76. No network, account,
model accuracy, private pilot or complete parent acceptance is claimed.

```sh
python -S scripts/mapped_drive_consultation_demo.py \
  --workspace /var/tmp/new-synthetic-mapped-drive --require-source --check-golden
```

Existing ADR-0008/0009/0010/0019 boundaries are reused; every proposed decision
retains its status and null approval. Actual Drive/OAuth, confidential runtime,
wider platforms/private Git and broader #87/#90 acceptance remain separate.
