---
schema: egohygiene.architecture-decision/v1
id: ADR-0022
title: Preserve canonical home changes as reviewed append-only provenance
status: proposed
date: '2026-11-06'
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/14
pull_request: https://github.com/egohygiene/mindgarden/pull/77
related:
- ADR-0007
- ADR-0008
- ADR-0009
- ADR-0010
- ADR-0019
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
affected_contracts: []
implementation_status: in_progress
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/14
  description: Move, merge, canonical reference and recovery requirements.
exceptions: []
approval: null
---

# ADR-0022: Reviewed canonical transitions

## Context

Existing routing places new knowledge but cannot move a canonical home without
rewriting history. Portable identity, immutable revision and physical location
remain distinct. Exact old references must survive a later home change.

## Decision

Carry a versioned, human-reviewed transition event in an existing provenance
record. Retain all old bytes and attribution; create a reviewed destination
derivative, or retire inputs only after an authored merge has exact lineage.
Treat old homes as historical before retrieval ranking and follow aliases only
within separately authorized records. Bind events into session revisions.

## Alternatives considered and rejected

Destructive moves would break old references. Silent copies would create two
canonical homes.

## Consequences and tradeoffs

This proposal adds append-only metadata and alias resolution,
with conflict/cycle rejection. The first draft supports matching personal
policies and simple notes through the existing recoverable group transaction.
Public/policy-changing moves and attached graph migration require later proofs.

## Implementation and evidence links

[Routing checkpoint](../private-routing.md) and tests/test_routing_lifecycle.py
show bounded implementation, not acceptance. The maintainer must disposition
this proposed decision; approval remains null. No deletion or real-garden
migration is authorized by implementation or by merging a draft.

## Replacement or exit strategy

Retain versioned transition readers and all original records. A successor can replace the projection/alias adapter after a reviewed migration while exact historical references and provenance remain resolvable. No rollback deletes captured evidence.

## Follow-up work

Mindgarden #14 owns public/policy-changing transfers, attached graph migration and broader recovery proofs. The maintainer owns disposition of this proposal; no historical decision is ratified by section normalization.

## Proposed lifecycle extension — 2026-11-08

The next bounded implementation retains exact outgoing graph records during
matching-policy personal moves, including their independent review state.
Explicit v2 transition/event schemas leave v1 unchanged and add reviewed split
anchors and replacements. One canonical successor preserves old references;
children are distinct authored units. Split segmentation and human approval are
not inferred. See tests/test_routing_transfers.py and the routing checkpoint for
lineage, stale/collision, policy and second-cutover rollback proofs. Incoming edge
retargeting and public/policy-changing migration remain open. This extends the
proposal only: status remains proposed and approval remains null.
