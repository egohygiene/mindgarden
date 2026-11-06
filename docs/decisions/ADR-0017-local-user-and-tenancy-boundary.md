---
schema: egohygiene.architecture-decision/v1
id: ADR-0017
title: Keep the first workflow single-user and require a separate collaboration model
status: proposed
date: '2026-11-05'
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/42
pull_request: https://github.com/egohygiene/mindgarden/pull/72
related:
- ADR-0007
- ADR-0009
- ADR-0010
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
- egohygiene/aether
- egohygiene/realm
affected_contracts: []
implementation_status: not_started
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/40
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/47
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/aether/issues/69
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/realm/issues/20
  description: Owning requirements; not evidence of completed external integration.
exceptions: []
approval: null
---

# ADR-0017: Keep the first workflow single-user and require a separate collaboration model

## Context

The finite local workflow uses explicit bindings, expiring sessions, a single
writable garden and bounded single-writer operations. It has no authenticated
application, shared tenant database, sync engine or network write endpoint.

## Decision

Propose the initial product wedge as one person using a local garden through
the supported CLI, with optional public read-only static output. An operating
system account and filesystem permissions are the current host boundary, not a
claim of encryption or confidential-runtime assurance. The loopback public
preview is not a private hosted application.

Treat authenticated self-host, household/team collaboration, multiple writers,
sync and multi-tenancy as distinct deferred profiles. Before enabling any, decide
identity/session lifecycle, memberships, roles, record-level authorization,
revocation, conflicts, audit, export/deletion and recovery. A login screen alone
cannot authorize a private garden or create tenant isolation.

## Alternatives considered and rejected

Starting with a multi-tenant service increases policy and recovery scope without
a selected audience. Treating multiple local paths as independent tenants would
confuse storage location with authorization. Silent last-writer-wins sync loses
review/evidence history.

## Consequences and tradeoffs

This limits concurrent editing and remote access intentionally. Existing scoped
sessions remain useful but are not a general authentication protocol. The native
platform and runtime support matrix remains explicit.

## Implementation and evidence links

This documentation-only checkpoint adds no runtime under #42. See the [decision
and ownership map](../target-architecture.md), [batch evidence](../garden-experience-milestone.md)
and linked source issues. Existing local prototypes are evidence, not acceptance.

## Replacement or exit strategy and migration cost

Keep consumer identities and source references independent of user accounts.
A later collaboration adapter needs a versioned identity/authorization mapping
and conflict migration, tested on exported synthetic gardens before real data.
No current single-user store is silently converted into tenant state.

## Follow-up work and owners

Mindgarden #40/#47 owns audience and collaboration requirements; Aether owns
session capability contracts; Realm owns host/runtime isolation. Revisit before
any private network interface or second writer, on owner-contract changes, or by
2027-01-01. Restricted assurance remains gated on Hygiene/Realm evidence.

