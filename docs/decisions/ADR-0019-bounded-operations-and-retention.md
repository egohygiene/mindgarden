---
schema: egohygiene.architecture-decision/v1
id: ADR-0019
title: Keep background operations and retention reviewable and recoverable
status: proposed
date: '2026-11-05'
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/42
pull_request: https://github.com/egohygiene/mindgarden/pull/72
related:
- ADR-0008
- ADR-0009
- ADR-0010
- ADR-0015
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
- egohygiene/realm
- egohygiene/aether
affected_contracts: []
implementation_status: in_progress
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/37
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/45
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/46
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/aether/issues/69
  description: Owning requirements; not evidence of completed external integration.
exceptions: []
approval: null
---

# ADR-0019: Keep background operations and retention reviewable and recoverable

## Context

Current synchronous services already separate read/plan/apply/verify, exact
input digests, owned output markers, vault export/restore and write recovery.
#46 introduces retention requirements; #37 needs targeted dependency rebuilds.

## Decision

Propose the same application services for future background work. A job declares
bounded inputs/revisions, authority, outputs, budgets, expiration and recovery
state. Retry may verify an identical completed output; it cannot broaden authority,
reapprove knowledge or silently overwrite conflicts. Cancellation/revocation
stops further reads/writes and records incomplete coverage.

Keep archival/source, durable-knowledge, model-context and public-publication
retention separate. Preserve originals by default. Context expiry or projection
invalidation never authorizes source deletion. Compaction is a proposal bound to
exact evidence and an authored transformation; durable review, public export and
destructive retention require independent human authority. No deletion scheduler,
source cleanup or new queue implementation is included.

## Alternatives considered and rejected

A generic always-on queue is unnecessary for the current finite CLI. Automatic
source deletion after summarization destroys the evidence needed to evaluate a
summary. Retrying with changed inputs would conceal a different operation.

## Consequences and tradeoffs

Long jobs require explicit checkpoints and may remain incomplete after failure.
Local baseline recovery is bounded, not distributed atomicity or a full backup
system. Backup copies inherit source sensitivity and need their own retention.

## Implementation and evidence links

This documentation-only checkpoint adds no runtime under #42. See the [decision
and ownership map](../target-architecture.md), [batch evidence](../garden-experience-milestone.md)
and linked source issues. Existing local prototypes are evidence, not acceptance.

## Replacement or exit strategy and migration cost

Export canonical knowledge and source-vault inventories separately, verify both,
restore to clean locations and rebuild projections. Version operation/retention
contracts explicitly. Migration cost grows when job stores or deletion are added;
require a dry-run inventory and recovery proof before either affects real data.

## Follow-up work and owners

Mindgarden #37/#46 owns dependency/retention contracts; #45 owns source integrity;
Realm owns scheduling/runtime; Aether owns agent cancellation/continuity.
Revisit before any destructive retention, automatic recurring job or shared
worker, on policy changes, or by 2027-01-01.



## Bounded #46 contract evidence

The [read-only evaluator and authored proof](../compaction-retention.md) implement
a local contract checkpoint using existing scoped evidence and curation services.
There is no queue, deletion, retention scheduler, raw-only authorization expansion
or private-pilot claim. This partial implementation does not accept this proposal.
