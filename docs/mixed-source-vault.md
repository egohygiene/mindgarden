# Mixed source/media vault checkpoint (#45)

This draft extends the existing filesystem baseline with private asset inventory,
non-destructive triage, an explicit storage factory boundary, and a combined
archive/PDF/image/audio recovery proof. [ADR-0024](decisions/ADR-0024-private-assets-and-explicit-storage-ports.md)
is proposed with null approval. No encrypted/provider/native-platform acceptance,
destructive migration, package release or real private consumer is claimed.

## Contracts and ownership

`mindgarden.vault/v1` keeps its existing shipped schema and filesystem
`vault.json`; its bytes and format remain unchanged. The versioned
`mindgarden.storage-capabilities/v1` contract separates read, immutable put,
checksums, audit, export, restore, relocation, encryption, networking and deletion.
Capabilities describe an adapter; they never grant policy or runtime assurance.

The new opaque-media source adapter preserves explicitly supplied PNG/JPEG, WAV,
MP4 or octet-stream bytes and emits one normalized identity per content/media
pair. It does not claim to decode or validate formats. Media type is supplied,
unverified metadata. There is no automatic thumbnail, OCR, transcription,
quality model, URL fetch or executable interpretation. Identical bytes share
storage; repeated or renamed captures can retain distinct origin observations
without duplicating the normalized unit or manifest asset. Unknown rights remain
source assertions and confer no copy/publication permission.

`mindgarden.asset-manifest/v1` is a rebuildable private projection, never a new
canonical garden model. It groups immutable content identities and retains exact
capture references, media declarations, origins, rights, provenance, scope,
encryption expectation, human review and retention metadata. Original filenames,
machine paths and credentials are absent. Every raw source remains excluded from
publication. Counts and content identities in this inventory are private too.

`asset inventory --local-config FILE --scope SESSION` requires an explicit
`assets` projection grant and a source review-state grant. Ordinary reviewed
knowledge sessions do not gain raw-source inventory access. Authorization and
sensitivity closure precede body reads. Candidate/result/output-byte limits,
expiry, revocation and final authority checks use the existing query service.
Public request scopes are denied before inventory access; diagnostics are
sanitized. Source metadata and review events enter the authorized view revision,
so changed represented inputs require a fresh session. No counts of denied
assets, filenames, previews or review metadata enter public discovery artifacts.

## Human triage is metadata, not deletion

`asset review --local-config FILE --garden-id ID --input REQUEST --plan` previews
an authored `mindgarden.asset-review-request/v1`; repeat with `--apply` and its
`--plan-digest`. The request names exact captured-source evidence, an explicit
human reviewer, disposition/rationale and the previous review's immutable revision.
Application adds an `x-asset-review` event to an existing provenance record. It
never rewrites sources, normalizations, old reviews or knowledge. Original files
and content-addressed objects stay intact.

The local checkpoint implements unreviewed, keep, useful-reference, duplicate,
low-quality, discard-proposed and archived. These are human selection labels,
not inferred quality scores. Restricted state is represented by the contract but
unavailable until actual confidential storage/runtime exists. Reference-only is
the supported copy policy; approved-copy is reserved and rejected pending separate
rights/publication authority. No event approves public release or declassification.

Retention is explicitly `retain-originals`, with legal-hold metadata and no
deletion authority. Unknown policy fails closed. Timed expiration, organization
holds, incident reclassification and destructive garbage collection remain #46
and parent #45 work. Conflicting review forks/cycles fail validation and preserve
all events; timestamps never silently choose a winner. Independent conflicting
cross-garden review chains need explicit reconciliation.

The combined recovery work also adds two boundary regressions: initial PDF human
authority must be named among its reviewers, and an old quarantine plan cannot
undo a prepared/interrupted restore. They extend the #35 and #30 checkpoints.

## Replaceable storage without ambient integrations

A caller may pass its own `StorageAdapters` instance to `open_vault`,
`content_resolver`, source plan/apply and `QueryContext.load`. Register factories
explicitly and remove them explicitly; the default contains only filesystem.
Bindings select a logical adapter ID and a private control root. Extension
credentials/configuration remain outside portable records and are the caller's
responsibility. There is no entry-point scan, provider installation or credential
lookup. Unknown/removed adapters fail unavailable without fallback.

The core hashes actual returned bytes even if an adapter claims checksum success.
A synthetic in-memory port proves ingestion, scoped inventory, removal, same-size
corruption detection and unsupported read-only writes. It deliberately lacks
backup, restore, relocation and encryption. The existing recovery plan supports
filesystem only. Remote/encrypted adapters and cross-provider migration require
independent implementations and evidence; self-reported flags cannot enable
restricted processing. Existing missing, unavailable, corrupted and unsupported
states remain explicit.

## Reproduce the evidence

```bash
.venv/bin/python -m unittest tests.test_assets tests.test_storage_adapters tests.test_mixed_vault_workflow -q
.venv/bin/python scripts/mixed_vault_demo.py --workspace .cache/mixed-port-proof \
  --recorded-synthetic-pdf --require-source --report .cache/mixed-port-proof.json
.venv/bin/python scripts/mixed_vault_demo.py --workspace .cache/mixed-real-proof \
  --tool-directory /usr/bin --require-source --report .cache/mixed-real-proof.json
```

The first/second commands use the explicitly named **recorded synthetic PDF
reader port**, so CI and clean core operation require no parser package or model.
They do not claim that CI installed Poppler. The third proves the same mixed
workflow with real local **Poppler 25.03.0** here. The separate
[document proof](document-ingestion.md) covers six actual parser states.

The [complete committed golden](../tests/fixtures/assets/expected-proof.json)
checks four assets, twelve vault objects, two reviewed prompt-bank entries,
exact archive/PDF citations and a **4,486-byte** bounded JSON context pack
(maximum 16,384). Both modes verify the same data; the report explicitly records
the selected reader mode. Networking is blocked in-process, provider environment
variables are cleared, and Google/model services are unused. This is no-service
operation, not host/network isolation attestation.

The proof interrupts relocation after target verification but before binding
replacement, retries the exact reviewed plan, retains the original vault,
exports/restores into a clean location, removes generated projections from a
copied garden, and rebuilds identical index/context/inventory. Both exact evidence
references still resolve. The synthetic asset marked discard-proposed remains
present and hash-verified. No machine path appears in portable records.

This extends #20's bounded consumer evidence. It does not complete #20's broader
publication/consumer acceptance, or #45's encrypted/provider/platform/power-loss,
approved-copy, timed retention and real private-pilot criteria. Exact source and
installed-wheel checks, commands, commits and CI are recorded in the
[private-storage sprint](private-storage-sprint.md).
