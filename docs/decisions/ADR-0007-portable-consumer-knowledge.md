---
schema: egohygiene.architecture-decision/v1
id: ADR-0007
title: Keep portable consumer records authoritative
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
implementation_status: not_started
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/9
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/12
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/40
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/42
  description: Owning requirements and remaining acceptance criteria.
exceptions: []
approval: null
---

# ADR-0007: Keep portable consumer records authoritative

## Context

The private-garden milestone extends the shipped v0 engine and additive v1 lifecycle. Legacy ADR-0001 through ADR-0006 remain preserved in the root decision log. This proposal does not retroactively ratify them or close the architecture program.

## Decision

Consumer-owned records contain reviewed knowledge; indexes, graphs, context packs, previews, and sites are rebuildable projections. A garden can operate in an explicitly supplied local workspace without Git hosting. Raw capture is separate from semantic knowledge.

## Alternatives considered and rejected

A hosted database as canonical storage would add a recovery dependency. Mandatory Git hosting would prevent an ordinary private local workspace.

## Consequences and tradeoffs

The local workflow needs explicit versioned contracts, safe plan/apply operations, compatibility fixtures and recovery evidence. Human disposition remains separate from implementation. The user authorized implementation of the bounded plan; that instruction does not change this ADR from proposed.

## Implementation and evidence links

See the linked owning issues and [milestone checkpoint specification](../private-garden-milestone.md). Implementation and verification are recorded per draft PR in the root continuity checkpoint. No implementation is claimed by this documentation checkpoint.

## Replacement or exit strategy

Retain portable records, immutable evidence references and existing v0/v1 readers. Replace integrations through adapter conformance and explicit migration plans. Any incompatible contract or ownership change requires a separately reviewed decision.

## Follow-up work

[#9](https://github.com/egohygiene/mindgarden/issues/9), [#12](https://github.com/egohygiene/mindgarden/issues/12), [#40](https://github.com/egohygiene/mindgarden/issues/40), [#42](https://github.com/egohygiene/mindgarden/issues/42). Full parent acceptance remains open.
