---
schema: egohygiene.architecture-decision/v1
id: ADR-0009
title: Extend shared Python application services for the local workflow
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
  url: https://github.com/egohygiene/mindgarden/issues/8
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/10
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/11
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/13
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/42
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/47
  description: Owning requirements and remaining acceptance criteria.
- type: implementation
  url: https://github.com/egohygiene/mindgarden/pull/64
  description: Merged bounded local checkpoint; broader parent acceptance remains open.
exceptions: []
approval: null
---

# ADR-0009: Extend shared Python application services for the local workflow

## Context

The private-garden milestone extends the shipped v0 engine and additive v1 lifecycle. Legacy ADR-0001 through ADR-0006 remain preserved in the root decision log. This proposal does not retroactively ratify them or close the architecture program.

## Decision

Preserve the dependency-free Python engine, existing CLI and v0 contracts. Interfaces invoke application services for validation, ingestion, curation, routing, retrieval and recovery. Captured-source, filesystem and future provider/model adapters depend inward on explicit contracts. Models and remote acquisition are optional producers outside normalization.

## Alternatives considered and rejected

A rewrite or parallel web implementation would duplicate policy and migration behavior. Mandatory models or databases would remove the useful offline baseline.

## Consequences and tradeoffs

The local workflow needs explicit versioned contracts, safe plan/apply operations, compatibility fixtures and recovery evidence. Human disposition remains separate from implementation. The user authorized implementation of the bounded plan; that instruction does not change this ADR from proposed.

## Implementation and evidence links

See the linked owning issues and [milestone checkpoint specification](../private-garden-milestone.md). Implementation and verification are recorded per draft PR in the root continuity checkpoint. The original documentation checkpoint claimed no runtime implementation. The bounded local implementation is now merged through #57, #59, #62, #64. See [the merge/coverage ledger](../open-issue-coverage.md); remaining scope is in progress. Decision status and approval are unchanged.

## Replacement or exit strategy

Retain portable records, immutable evidence references and existing v0/v1 readers. Replace integrations through adapter conformance and explicit migration plans. Any incompatible contract or ownership change requires a separately reviewed decision.

## Follow-up work

[#8](https://github.com/egohygiene/mindgarden/issues/8), [#10](https://github.com/egohygiene/mindgarden/issues/10), [#11](https://github.com/egohygiene/mindgarden/issues/11), [#13](https://github.com/egohygiene/mindgarden/issues/13), [#42](https://github.com/egohygiene/mindgarden/issues/42), [#47](https://github.com/egohygiene/mindgarden/issues/47). Full parent acceptance remains open.
