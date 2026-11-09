---
schema: egohygiene.architecture-decision/v1
id: ADR-0023
title: Classify new document inputs explicitly before optional local parsing
status: proposed
date: '2026-11-06'
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/35
pull_request: https://github.com/egohygiene/mindgarden/pull/83
related:
- ADR-0008
- ADR-0010
- ADR-0019
- ADR-0021
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
affected_contracts: []
implementation_status: in_progress
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/35
  description: Document bundle, confidentiality, page evidence and parser-state requirements.
exceptions: []
approval: null
---

# ADR-0023: Initial document classification and optional local parsing

## Context

Confidential documents require actual storage/runtime assurance, not a scope label.
Hygiene #39/#40 and Realm #25/#28/#29/#30 have not supplied accepted contracts or verified
confidential capabilities here. Ordinary synthetic PDF evidence can exercise the
existing source-adapter boundary independently.

## Decision

Treat a new document as restricted by default and stop before parsing when the
required runtime is unavailable. Permit a new ordinary source only with an
explicit approved human initial classification bound to its immutable hash.
Persist that review in the document bundle; it cannot authorize reclassification
of an existing restricted record, review of derived knowledge or publication.
Local operator assertions are not an authenticated multi-user identity service.

Select optional local parser executables explicitly, fingerprint their versions
and bytes, bound resource use and contain temporary state inside the supplied
vault. Keep original bytes, page coordinates, normalized UTF-8 spans, parser
provenance and losses. Refuse incomplete/OCR/encrypted/malformed bundles; no
implicit acquisition, OCR, model call, attachment extraction or active content.

## Alternatives considered and rejected

A mandatory parser would burden the dependency-free engine. A restricted label
on ordinary disk would misstate assurance. Refusing ordinary synthetic fixtures
would unnecessarily block independent adapter evidence.

## Consequences and tradeoffs

This proposed boundary
keeps those concerns separate and leaves confidential runtime adoption to its
owners. Poppler shared libraries and host security remain environment evidence,
not attested by executable hashes alone.

## Implementation and evidence links

[Document checkpoint](../document-ingestion.md), tests/test_documents.py and
scripts/document_demo.py provide bounded synthetic implementation evidence.
The maintainer must disposition this proposal. Approval remains null; no parent
issue, organization policy or confidential processing capability is accepted.

## Replacement or exit strategy

Keep the parser behind the normalized-source adapter and retain original bytes, explicit classification and parser provenance. An alternative parser or contract revision requires conformance and a reviewed migration; disabling parsing preserves original sources.

## Follow-up work

Mindgarden #35 owns wider layout/OCR/format proofs; Hygiene #39/#40 and Realm #25/#28/#29/#30 own normative confidential runtime assurance. Human disposition, native dependency/temporary-state evidence and an approved private pilot remain separate.

The 2026-11-09 [follow-through](../privacy-storage-followthrough.md) adds managed process-group cleanup, owner-only child defaults and native six-state evidence without changing proposed status or claiming a confidential sandbox. Realm #60 remains a platform/distribution tracker; encrypted-vault and confidential acceptance belong directly to #28/#29/#30.
