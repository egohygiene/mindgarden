---
schema: egohygiene.architecture-decision/v1
id: ADR-0024
title: Keep source asset triage append-only and storage adapters explicitly supplied
status: proposed
date: '2026-11-06'
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/45
pull_request: https://github.com/egohygiene/mindgarden/pull/84
related:
- ADR-0008
- ADR-0010
- ADR-0012
- ADR-0019
- ADR-0023
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
affected_contracts: []
implementation_status: in_progress
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/45
  description: Source/media inventory, non-destructive triage and portable recovery requirements.
exceptions: []
approval: null
---

# ADR-0024: Private asset inventory, triage and explicit storage ports

## Context

Immutable source blobs already have separate logical identities and machine-local
bindings. Media need inventory and human selection without destructive cleanup.
Projection state and a provider's capabilities must not become canonical knowledge
or implicit authority. #46 retention constraints apply before any deletion design.

## Decision

Keep a versioned private asset manifest as a rebuildable, explicitly authorized
projection. Group exact content identities while preserving every capture's
origin, rights and attribution. Preserve opaque media bytes without interpretation.
Store human triage as append-only events in existing provenance records, with
exact source/prior-review revisions. Reject ambiguous review forks. State such as
`discard-proposed` grants no deletion, publication or declassification authority.
Retain originals and legal-hold metadata; timed retention and garbage collection
require separate accepted policy and recovery plans.

Require an explicit assets session grant and source review-state grants, enforce
all existing output/live-authority budgets, and prohibit public inventories.
Keep safe reference as the baseline; approved copies require another rights and
publication contract. Unsupported restricted runtime remains unavailable.

Register removable storage factories explicitly in the caller. Verify actual
returned bytes at the core boundary regardless of an adapter's claims. Keep the
filesystem recovery implementation bounded and do not infer migration, encryption
or confidential execution from capability booleans. No ambient plugin/provider,
credential, model or network discovery is part of this port.

## Alternatives considered and rejected

Mutating source records would lose review history. A canonical generated manifest
would become stale after relocation or policy changes. Automatic provider loading
would expand execution and credential authority.

## Consequences and tradeoffs

These proposals instead add
explicit review metadata and projections over existing contracts. Conflicting
cross-garden review histories need human reconciliation; they are not silently
ordered by timestamps.

## Implementation and evidence links

[Mixed-vault checkpoint](../mixed-source-vault.md), synthetic asset/adapter tests
and scripts/mixed_vault_demo.py demonstrate the local boundary. Proposed decision
status and null approval remain unchanged by implementation. Confidential,
provider, native platform, power-loss and real private consumer acceptance remain
open. No destructive retention action is implemented.

## Replacement or exit strategy

Discard and rebuild generated asset inventories from authorized records and immutable vault objects. Replace explicitly registered storage factories through byte/integrity conformance and reviewed relocation plans. Retain originals and append-only review history when disabling a provider.

## Follow-up work

The [2026-11-09 local migration checkpoint](../vault-migration.md) implements
reviewed copy/verify/rebind for explicit initialized local adapters. It preserves
canonical references, source stores and private binding history, with independent
byte verification and retry fixtures. It does not accept this ADR, select a new
provider or claim encrypted/remote/runtime or destructive recovery assurance.

Mindgarden #45 owns remaining provider/platform/power-loss and real-consumer acceptance; #46 owns approved retention and destructive recovery policy. Cross-garden review reconciliation and approved-copy rights require their own contracts and human review.
