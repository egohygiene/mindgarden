---
schema: egohygiene.architecture-decision/v1
id: ADR-0010
title: Keep local scope, review and publication authority independent
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
  url: https://github.com/egohygiene/mindgarden/issues/13
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/14
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/29
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/31
  description: Owning requirements and remaining acceptance criteria.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/42
  description: Owning requirements and remaining acceptance criteria.
- type: implementation
  url: https://github.com/egohygiene/mindgarden/pull/64
  description: Merged bounded local checkpoint; broader parent acceptance remains open.
exceptions: []
approval: null
---

# ADR-0010: Keep local scope, review and publication authority independent

## Context

The private-garden milestone extends the shipped v0 engine and additive v1 lifecycle. Legacy ADR-0001 through ADR-0006 remain preserved in the root decision log. This proposal does not retroactively ratify them or close the architecture program.

## Decision

The initial workflow is single-user and single-writer with explicit authorized roots. Visibility, persistence, execution, publication and review remain independent. Derived outputs inherit every contributing restriction. Authored candidate plans carry explicit per-item reviewer evidence; applying a plan alone does not approve its knowledge. Unknown policy fails closed. Runtime isolation and organization compliance require separate owner evidence.

## Alternatives considered and rejected

One private flag cannot represent execution or publication authority. Letting model output or an apply operation grant review authority would silently expand permissions.

## Consequences and tradeoffs

The local workflow needs explicit versioned contracts, safe plan/apply operations, compatibility fixtures and recovery evidence. Human disposition remains separate from implementation. The user authorized implementation of the bounded plan; that instruction does not change this ADR from proposed.

## Implementation and evidence links

See the linked owning issues and [milestone checkpoint specification](../private-garden-milestone.md). Implementation and verification are recorded per draft PR in the root continuity checkpoint. The original documentation checkpoint claimed no runtime implementation. The bounded local implementation is now merged through #55, #61, #62, #64. See [the merge/coverage ledger](../open-issue-coverage.md); remaining scope is in progress. Decision status and approval are unchanged.

## Replacement or exit strategy

Retain portable records, immutable evidence references and existing v0/v1 readers. Replace integrations through adapter conformance and explicit migration plans. Any incompatible contract or ownership change requires a separately reviewed decision.

## Follow-up work

[#13](https://github.com/egohygiene/mindgarden/issues/13), [#14](https://github.com/egohygiene/mindgarden/issues/14), [#29](https://github.com/egohygiene/mindgarden/issues/29), [#31](https://github.com/egohygiene/mindgarden/issues/31), [#42](https://github.com/egohygiene/mindgarden/issues/42). Full parent acceptance remains open.

## Cross-owner authority and migration cost

Visibility, persistence, execution/network, publication ceiling and review remain
independent. Public/repository, organization, personal and restricted views use
the existing Garden/scope contracts. Local policy IDs are not an accepted
organization-wide declassification or confidential-runtime contract. Hygiene #39,
Aether #69 and Realm own those normative/runtime integrations.

A private cleanup approval cannot approve an Akashic publication candidate; each
requires its own exact-input human decision. Migration cost is explicit policy
version mapping, fixture parity, reauthorization and rebuild of affected outputs.
Never reinterpret an unsupported policy or old grant as permission to proceed.
