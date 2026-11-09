# Document/PDF checkpoint (#35)

This draft implements an optional local PDF source adapter over the existing
captured-byte ingestion/plan/apply service. The Python engine still has no runtime
dependencies. [ADR-0023](decisions/ADR-0023-document-classification-and-local-reader.md)
is proposed, with null approval. It does not supply Hygiene or Realm assurance.

## Classification and authority

A document defaults to restricted. With no classification review, the service
returns `RUNTIME_UNVERIFIED` before reading the input, running a parser or creating
temporary files. Restricted/encrypted and mixed organization/personal inputs are
also unavailable in this ordinary filesystem runtime. Normative Hygiene #39/#40,
Realm #25/#60, encryption/key broker and confidential runtime evidence remain
external dependencies.

For a **new ordinary or wholly synthetic input**, supply a
`mindgarden.document-classification/v1` document: `kind: initial-classification`,
exact `source_sha256`, complete supported `scope`, human `authority` and approved
`review` with reviewers, timestamp and rationale. This is a trusted local operator
assertion, not authenticated organizational authority. It never changes an
existing restricted record. Derived knowledge remains unreviewed until separately
curated. Source records stay excluded from publication. The shared ingestion
service joins declared source scope with garden scope before normalization; a
custom adapter cannot weaken it.

## Optional adapter and evidence

Select an absolute `--tool-directory` containing regular `pdfinfo` and
`pdftotext` executables. No PATH lookup, tool installation or remote acquisition
occurs. The verified local implementation is Linux/Poppler **25.03.0**, using
`pdfinfo -` and `pdftotext -bbox-layout -enc UTF-8 - -`. Executable versions,
SHA-256 values, normalization and bounds enter the portable document bundle and
plan digest. Changed input, review, configuration, tool bytes or target invalidates
application before persistent blob writes.

Temporary stdout, stderr, working directories and HOME/cache/temp variables stay
inside the selected initialized vault; owned scratch is removed on normal errors
and completion. Each process receives source bytes over stdin, a small clean
environment, a 15-second timeout, CPU/memory/file/core limits and bounded output.
Original filenames and raw parser errors are not returned in diagnostics. This
is resource containment, not a confidential or network isolation attestation.
Host libraries, crash/power-loss cleanup and OS-level isolation remain limitations.

Immutable original PDFs, embedded assets and active content are preserved as
untrusted bytes. They are never executed or fetched. Each normalized page is
`mindgarden.document-page/v1`: page number, geometry, text, ordered words, bounding
boxes and exact UTF-8 byte spans. Text joins words with spaces and lines with LF;
its offsets do **not** claim to address PDF byte positions. `json:/text` addresses
the exact page evidence; `json:/words/N/text` addresses an individual word through
the ordinary evidence service. Source metadata links the original hash and page.
A separate `mindgarden.document-bundle/v1` records page hashes, parser profile,
classification review, attachment preservation and explicit extraction losses.

Reading order is estimated. Semantic sections, tables, complex layout fidelity,
OCR, office formats and attachment extraction are deferred. A complete bundle is
required: `DOCUMENT_OCR_NEEDED`, `DOCUMENT_PARTIAL`, `DOCUMENT_ENCRYPTED`,
`DOCUMENT_MALFORMED`, `DOCUMENT_UNSUPPORTED`, `DOCUMENT_UNAVAILABLE` and
`DOCUMENT_LIMIT` are explicit failures with no successful partial ingestion.

## CLI and verification

`mindgarden document` accepts `--local-config`, `--garden-id`, `--vault-id`,
`--input`, `--source-id`, `--title`, `--origin`, `--owner`, `--rights`, `--captured`,
`--classification-review` and `--tool-directory`. First use `--plan`; inspect its
private result, then repeat the inputs with `--apply --plan-digest SHA256`.
`--diagnostic-format json` emits sanitized stable diagnostics. No model is needed.

```bash
.venv/bin/python -m unittest tests.test_documents tests.test_source_adapters tests.test_v1_contracts -q
.cache/python313/bin/python -m unittest tests.test_documents -q
.venv/bin/python scripts/document_demo.py --workspace .cache/pdf-proof \
  --tool-directory /usr/bin --require-source --report .cache/pdf-proof.json
```

The first two commands pass 20 and 8 tests respectively. Unit tests use a recorded
synthetic reader port, explicitly independent of installed PDF tools. The third
command proves the real optional tools here against six committed synthetic
states, page/layout golden, duplicate imports, immutable originals, removed
scratch and a valid garden. It records actual parser versions/hashes; no other
Poppler version, native platform or confidential consumer is claimed tested.
The exact command/workspace used at this checkpoint is in the sprint handoff.

This is implementation and local evidence. Restricted processing, OCR/office
coverage, host/runtime integration and real private consumer acceptance keep #35
open. Its ordinary mixed-source recovery proof follows in #45.


## Managed parser processes

The Linux local runner cleans its started process group after timeout and normal parent completion, uses owner-only file creation defaults and points standard child temporary/cache/config/data/state paths at the supplied vault workspace. Synthetic descendant, permission and diagnostic regressions and the actual six-state Poppler receipt are in [the privacy follow-through](privacy-storage-followthrough.md). This is bounded resource/lifetime management, not containment of an executable that escapes its process group or host/network/encryption assurance. Restricted inputs still fail before parsing.
