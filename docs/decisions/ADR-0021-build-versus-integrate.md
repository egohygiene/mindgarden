---
schema: egohygiene.architecture-decision/v1
id: ADR-0021
title: Keep optional product integrations behind evaluated replaceable boundaries
status: proposed
date: '2026-11-05'
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/42
pull_request: null
related:
- ADR-0007
- ADR-0009
- ADR-0013
- ADR-0018
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
- egohygiene/realm
affected_contracts: []
implementation_status: not_started
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/40
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/42
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/47
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/realm/issues/41
  description: Owning requirements; not evidence of completed external integration.
exceptions: []
approval: null
---

# ADR-0021: Keep optional product integrations behind evaluated replaceable boundaries

## Context

Obsidian configuration and pinned Quartz already provide useful file/static
consumers. #40/#42 name additional product references; Realm #41 owns a disposable
Papra evaluation. No such product is canonical Garden storage today.

## Decision

Propose retaining Obsidian as an optional file consumer and Quartz as the existing
replaceable static renderer. Evaluate new software against a selected workflow,
not feature similarity. Require immutable upstream version/license evidence,
provenance/scope mapping, failure and malformed-input fixtures, resource/cost
observations, export/restore/rebuild and complete removal.

SilverBullet, AFFiNE, Papra, OpenViking and Cognee remain unevaluated/deferred
references. No version, performance, compatibility or licensing approval is
inferred. Papra's AGPL concern is flagged by #40/Realm #41; current immutable
license terms and any code/asset reuse must be reviewed in the owning experiment.
No code/assets are copied here. Optional model/embedding providers remain outside
normalization and baseline retrieval.

## Alternatives considered and rejected

Replacing the domain with a reference product's database creates a canonical
ownership migration before evidence. Building every useful feature from scratch
ignores maintainable adapters. Adopting an unpinned product by reputation gives
no reproducible integration or exit proof.

## Consequences and tradeoffs

A richer editor/document experience remains future work. Comparative prototypes
must be bounded and synthetic. Requirements may be learned without adopting a
product or borrowing its implementation/assets.

## Implementation and evidence links

This documentation-only checkpoint adds no runtime under #42. See the [decision
and ownership map](../target-architecture.md), [batch evidence](../garden-experience-milestone.md)
and linked source issues. Existing local prototypes are evidence, not acceptance.

## Replacement or exit strategy and migration cost

Keep each integration's identifiers mapped to exact captured sources and
consumer-owned records. Remove its adapter/generated state after verified export.
Migration cost is measured in the experiment, including source identity, taxonomy,
license obligations and recovery; no zero-cost exit is promised.

## Follow-up work and owners

Mindgarden #42/#47 owns the choice and integration decision; Realm #41 owns
Papra provisioning. The architecture map assigns per-reference revisit evidence.
Revisit when an owner supplies a pinned experiment or before importing code,
assets or canonical data into any candidate, and by 2027-01-01.

