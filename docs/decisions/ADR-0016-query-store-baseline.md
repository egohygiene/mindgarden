---
schema: egohygiene.architecture-decision/v1
id: ADR-0016
title: Keep portable records canonical and measure query adapters before adoption
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
- ADR-0010
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
affected_contracts: []
implementation_status: not_started
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/32
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/33
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/34
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/egohygiene/issues/478
  description: Owning requirements; not evidence of completed external integration.
exceptions: []
approval: null
---

# ADR-0016: Keep portable records canonical and measure query adapters before adoption

## Context

The shipped lexical/index/graph services rebuild deterministic JSON from explicitly
scoped records. #32 requests a replaceable SQLite FTS baseline; #33/#34 are optional
evaluations. Organization search #478 remains a hypothesis, not an engine mandate.

## Decision

Propose retaining the dependency-free JSON/lexical baseline as the reference
implementation. A query-store port consumes an already authorized record view,
its represented revisions and query/budget contracts; it never opens all registered
roots or becomes canonical storage. SQLite FTS is the next bounded candidate under
#32 after disposition, measured against reference ranking, exact citations,
visibility/review filtering, stale/revoked input rejection and clean rebuilds.

CozoDB, Meilisearch and vector adapters remain optional/deferred. Adoption requires
pinned versions, synthetic relevance and latency/memory/size measurements, offline
and failure behavior, license/operating-cost evidence, export/rebuild/teardown and
privacy parity. Do not invent a benchmark threshold before selecting a workload.

## Alternatives considered and rejected

Immediate SQLite adoption would make a second implementation authoritative before
parity evidence. A graph/search service by default adds processes and recovery
cost. A vector-only baseline removes useful no-model/offline lexical behavior.

## Consequences and tradeoffs

The JSON baseline may be slower for a large corpus; this proposal makes that
measurable rather than promising scale. No new store or benchmark implementation
is included. Capabilities must expose unsupported query features explicitly.

## Implementation and evidence links

This documentation-only checkpoint adds no runtime under #42. See the [decision
and ownership map](../target-architecture.md), [batch evidence](../garden-experience-milestone.md)
and linked source issues. Existing local prototypes are evidence, not acceptance.

## Replacement or exit strategy and migration cost

Rebuild an adapter from portable records and discard its owned cache. Migration
cost is bounded by index conversion/rebuild and query-parity fixtures; no canonical
record migration is justified. A future store version uses a new owned cache and
can fall back to the JSON reference.

## Follow-up work and owners

Mindgarden owns #32's port/parity/benchmark checkpoint; #33/#34 own optional
experiments. Revisit before #32 implementation, on a measured resource/relevance
failure, on the #478 contract release, or by 2027-01-01. Human disposition precedes
consequential store adoption.

