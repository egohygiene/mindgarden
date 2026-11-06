---
schema: egohygiene.architecture-decision/v1
id: ADR-0018
title: Keep the local runtime minimal and let Realm own optional service composition
status: proposed
date: '2026-11-05'
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/42
pull_request: null
related:
- ADR-0009
- ADR-0013
- ADR-0017
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
- egohygiene/realm
- egohygiene/relay
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
  url: https://github.com/egohygiene/realm/issues/20
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/relay/issues/40
  description: Owning requirements; not evidence of completed external integration.
exceptions: []
approval: null
---

# ADR-0018: Keep the local runtime minimal and let Realm own optional service composition

## Context

The core Python workflow requires no service, hosted database, Google integration
or model call. Optional rendering consumes a pinned Node/Quartz toolchain prepared
separately. #40 eventually requests a Compose product; Realm #20 owns its profile.

## Decision

Propose one Python process with explicit local garden/vault/control paths for
the initial workflow. Add the pinned renderer only for static publication.
Provisioning software and allowing network execution are separate from a query's
scope; an offline fixture is not host-level network-isolation certification.

Realm owns any future Compose/dev-container profile, volumes, secrets, ports,
health, resource limits and teardown. Mindgarden provides a pinned CLI/package,
application-service contracts and capability/error states. A first self-hosted
API/UI may use one application service after framework/auth decisions; add a
worker or query service only when a measured requirement justifies it. No Compose
file, application server or model gateway is implemented by this decision.

## Alternatives considered and rejected

A database, queue, model service and reverse proxy by default add deployment
and backup failure modes. Copying Realm provisioning into Mindgarden duplicates
ownership. Public binding of the preview would turn a local helper into an
unsupported hosted application.

## Consequences and tradeoffs

Development setup remains small; production topology is still undecided.
Containers do not establish confidentiality by themselves. Renderer acquisition,
engine release availability and native platform support remain separately verified.

## Implementation and evidence links

This documentation-only checkpoint adds no runtime under #42. See the [decision
and ownership map](../target-architecture.md), [batch evidence](../garden-experience-milestone.md)
and linked source issues. Existing local prototypes are evidence, not acceptance.

## Replacement or exit strategy and migration cost

Preserve portable records and machine-local locations outside them. A Realm
profile can be removed after verified canonical export while discarding only its
owned generated state. Migration cost is packaging/volume/port configuration,
not conversion to a runtime-owned knowledge database.

## Follow-up work and owners

Realm #20 owns released composition and #41 the opt-in Papra lab; Relay #40
owns CI/build mechanics. Mindgarden #47 supplies application requirements.
Revisit before a long-running/private network service, a measured process need,
a compatible released profile, or by 2027-01-01.

