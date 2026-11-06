# Captured-source adapters and ingestion plans

`SourceAdapter` in `mindgarden.domain.sources` consumes captured bytes plus
explicit metadata and emits a `NormalizedBundle`. It does not fetch, execute
source instructions, invoke models, choose durable knowledge or publish.
The application owns storage and deterministic digest-bound application.

## First adapter and CLI

`plain-text` v1.0.0 accepts explicit `text/plain` or `text/markdown` with no archive
manifest version. It decodes UTF-8, removes one initial BOM, normalizes CR/CRLF,
and emits exactly one terminal newline. Originals remain byte-identical in the
private vault; both original and normalized hashes and ordered transformations
are retained. Text inputs are bounded to 2,000,000 bytes.

Origins are credential-free HTTP(S) or URN identities. File paths, URL userinfo
and known credential/signature query fields are rejected without echoing them.
Acquisition paths and provider credentials belong in private runtime bindings,
not portable source/provenance records. Generated metadata is bounded to 2 MB;
oversized metadata fails during planning before any immutable blob is written.

```bash
mindgarden ingest --repository-root "/private/garden" \
  --local-config "/private/bindings.json" --vault-id "private-sources" \
  --input "/private/captured.txt" --source-id "capture-example" \
  --title "Captured example" --origin "urn:example:captured" \
  --captured "2026-11-04T00:00:00Z" --owner "example-owner" \
  --rights "User-supplied private source; no publication grant" \
  --media-type "text/plain" --adapter "plain-text" --plan
```

Apply with identical arguments, replacing `--plan` with
`--apply --plan-digest "REVIEWED_SHA256"`. V1 requires an observed RFC3339 capture
timestamp. V0 retains its date argument, dry run and `--write` behavior. V1
relationships belong to curation; `--related` cannot silently create them.
The v0 public-confirmation flag does not grant v1 public-source import authority.

`mindgarden.change-plan/v1` binds explicit metadata, captured bytes, adapter and
manifest versions, external-configuration digest, canonical garden revision and
all output checksums. Plans carry the input scope and belong in that boundary.
Source/configuration or target drift rejects application before new blob writes.
Single-writer staging validates the complete resulting garden and never overwrites
conflicting records. Ordinary cutover failures restore the old tree. Immutable
objects retained after a failed staging check are non-destructive unreferenced
bytes; they are not automatically garbage-collected.

## Identity, overlap and evidence

Logical source-unit keys and represented content revisions are independent.
Each immutable source record preserves its full unit identity and byte hash;
compact filename IDs have explicit collision checks. Identical re-import is a
no-op. Changed content produces a separate revision record and preserves older
references. Different proven source identities do not merge merely because their
text matches.

An adapter can emit stable units independently. Unchanged units reuse their
existing normalized record; a new provenance observation records additional
package lineage without rewriting original evidence. Unknown cross-export
identity is not guessed from filenames or similar text.

Evidence locators currently support `artifact`, 1-based inclusive `lines:A-B`,
zero-based half-open `bytes:A-B`, and `json:/rfc6901/pointer` selecting exact text.
The selected bytes have their own hash, separate from the represented complete
source hash. JSON selectors do not execute or interpret selected strings.

## Consumer extension without domain edits

Implement `adapter_id`, `version`, `supported_inputs` and
`normalize(captured, metadata) -> NormalizedBundle`. Register the object explicitly
with `AdapterRegistry.register`, then pass the registry to
`build_ingestion_plan`. Declare supported media/manifest pairs; ambiguous or
unknown selection fails. There is no ambient plugin import or provider discovery.

`tests/test_source_adapters.py` supplies a synthetic consumer adapter, registers
it without modifying the domain, and exercises the same plan/apply path with
networking disabled. Each adapter version needs deterministic golden and unsafe
input fixtures. Changing normalization semantics requires a new adapter version;
all existing source records and exact represented revisions remain resolvable.

Mindcap #35/#48 bookmark integration and the #15 archive adapter remain separate
proofs over this contract. No support for their formats is implied by the text
adapter or extension example.

## Versioned declarations and conformance checkpoint

`describe_adapter` emits `mindgarden.source-adapter/v1`: software identity and
version, exact media/manifest pairs, captured-bytes protocol and explicit limits
for captured bytes, normalized units/bytes and portable metadata. Legacy explicit
adapters receive the documented bounded defaults. Registration validates the
declaration; later declaration mutation requires a fresh explicit registry.
The private ingestion plan binds its declaration digest. No executable plugin
is discovered or installed from data records.

`normalize_source` enforces limits, unique portable unit identities, strict JSON
metadata, ordered transformations and valid evidence selectors before writing
records or blobs. Adapter exceptions produce a failed result, while an empty
successful bundle remains explicit. `check_adapter_conformance` runs trusted
adapter code twice against identical explicit inputs and rejects different
results or input mutation. This is a fixture harness, not an OS sandbox; consumer
adapters are trusted application code and must supply their own unsafe fixtures.

The source tests include unchanged bytes imported under a newer adapter version
and a later capture observation. Old source and provenance bytes remain exact;
additional observations receive digest-derived immutable IDs only on conflict.
A new adapter version never rewrites the first attribution of unchanged evidence.

[The reference-capture example](../examples/adapters/reference_capture.py) is a
consumer-owned extension with a committed synthetic fixture and plan/apply proof.
It retains titles, URLs and notes, including inert bookmarklets, while marking
page content `not-captured`. It claims only `example.reference-capture/1`, not
Mindcap's still-unpublished provider-neutral snapshot/delta wire contract.
