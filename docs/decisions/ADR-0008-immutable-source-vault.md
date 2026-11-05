---
schema: egohygiene.architecture-decision/v1
id: ADR-0008
title: Separate source identity, immutable content, and location
status: proposed
date: '2026-11-04'
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/42
pull_request: null
related: []
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
affected_contracts: []
implementation_status: in_progress
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/11
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/15
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/30
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/35
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/45
  description: Owning requirements and remaining acceptance criteria.
- type: implementation
  url: https://github.com/egohygiene/mindgarden/pull/64
  description: Merged bounded local checkpoint; broader parent acceptance remains open.
exceptions: []
approval: null
---

# ADR-0008: Separate source identity, immutable content, and location

## Context

The private-garden milestone extends the shipped v0 engine and additive v1 lifecycle. Legacy ADR-0001 through ADR-0006 remain preserved in the root decision log. This proposal does not retroactively ratify them or close the architecture program.

## Decision

Keep captured originals in a separately configured private vault. Logical source references retain garden/artifact identity and immutable content hashes; local bindings resolve a logical vault identity to physical storage. The filesystem baseline verifies immutable objects and supports non-destructive recovery. Content deduplication never proves conversation or message identity.

## Alternatives considered and rejected

Garden-relative source paths remain supported for existing v1 records. Absolute paths in portable records would break relocation and disclose private topology. Requiring a storage provider would prevent offline recovery.

## Consequences and tradeoffs

The local workflow needs explicit versioned contracts, safe plan/apply operations, compatibility fixtures and recovery evidence. Human disposition remains separate from implementation. The user authorized implementation of the bounded plan; that instruction does not change this ADR from proposed.

## Implementation and evidence links

See the linked owning issues and [milestone checkpoint specification](../private-garden-milestone.md). Implementation and verification are recorded per draft PR in the root continuity checkpoint. The original documentation checkpoint claimed no runtime implementation. The bounded local implementation is now merged through #56, #63, #64. See [the merge/coverage ledger](../open-issue-coverage.md); remaining scope is in progress. Decision status and approval are unchanged.

## Replacement or exit strategy

Retain portable records, immutable evidence references and existing v0/v1 readers. Replace integrations through adapter conformance and explicit migration plans. Any incompatible contract or ownership change requires a separately reviewed decision.

## Follow-up work

[#11](https://github.com/egohygiene/mindgarden/issues/11), [#15](https://github.com/egohygiene/mindgarden/issues/15), [#30](https://github.com/egohygiene/mindgarden/issues/30), [#35](https://github.com/egohygiene/mindgarden/issues/35), [#45](https://github.com/egohygiene/mindgarden/issues/45). Full parent acceptance remains open.
