---
schema: egohygiene.architecture-decision/v1
id: ADR-0015
title: Compose pinned public site artifacts into caller-owned portal mounts
status: proposed
date: "2026-11-05"
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/18
pull_request: https://github.com/egohygiene/mindgarden/pull/71
related:
- ADR-0011
- ADR-0013
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
- egohygiene/relay
affected_contracts: []
implementation_status: in_progress
evidence:
- type: issue
  url: https://github.com/egohygiene/relay/issues/40
  description: Relay owns reusable orchestration; Mindgarden owns CLI and output contracts.
exceptions: []
approval: null
---

# ADR-0015: Compose pinned public artifacts into caller-owned portal mounts

## Context

A garden must coexist with intelligence, decisions and history without an engine
owning the entire portal. Represented source revision and actual rendered artifact
identity differ. The current Relay tree does not supply a Mindgarden portal action.

## Decision

Propose an explicit private request and digest-bound local composition plan.
Require the exact rendered manifest checksum as well as represented revision.
Verify complete source membership and public discovery contracts before copying
into a caller-selected mount. Create or verify only owned garden files and write
the portable ownership receipt last. Relay and consumers retain deployment control.

## Alternatives considered and rejected

Whole-directory synchronization risks deleting sibling surfaces. A represented
revision alone does not identify renderer output. Copying Relay workflows would
duplicate a separate owner's implementation. Silent repair could overwrite human
content or conceal an incomplete prior operation.

## Consequences and tradeoffs

The local checkpoint has no deployment credentials or cross-surface atomicity.
Unsigned artifacts need a trusted checksum handoff. Partial/conflicting outputs
are retained; complete copies can recover a failed final receipt through retry.

## Implementation and evidence links

[The composition contract](../portal-composition.md) pins inspected Relay state
and records recovery, CLI, schemas, fixtures and remaining consumer acceptance.

## Replacement or exit strategy

Rebuild into a fresh owned staging mount from the pinned public artifact. Replace
workflow orchestration without changing canonical records or portable lineage.

## Follow-up work

Human disposition, pinned Relay #40 action, approved consumer migration and actual
host promotion/rollback remain separate. Implementation does not ratify this ADR.
