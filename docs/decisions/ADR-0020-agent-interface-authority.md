---
schema: egohygiene.architecture-decision/v1
id: ADR-0020
title: Expose bounded application services without letting agent interfaces grant authority
status: proposed
date: '2026-11-05'
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/42
pull_request: https://github.com/egohygiene/mindgarden/pull/72
related:
- ADR-0009
- ADR-0010
- ADR-0017
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
  url: https://github.com/egohygiene/mindgarden/issues/31
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/47
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/51
  description: Owning requirements; not evidence of completed external integration.
- type: issue
  url: https://github.com/egohygiene/aether/issues/69
  description: Owning requirements; not evidence of completed external integration.
exceptions: []
approval: null
---

# ADR-0020: Expose bounded application services without letting agent interfaces grant authority

## Context

Mindgarden has scoped CLI search, backlinks, graph, context and exact-evidence
services. It has no MCP server or API authentication implementation. Aether #69
specifies the broader provider-neutral session capability contract; its full
cross-owner acceptance is not claimed by Mindgarden's local session schema.

## Decision

Propose MCP resources for already-authorized immutable/read projections, prompts
for optional templates with no authority, and tools for bounded calls into shared
application services. Tool discovery is not a permission grant. Read/search must
filter before ranking/traversal; an apply tool requires a fresh reviewed plan and
separate write authority. Publication/declassification/deletion need explicit
human approval appropriate to the operation.

Aether owns session/provider/tool capability semantics, Realm owns execution and
network enforcement, Hygiene owns normative policy, and Mindgarden owns Garden
selection/provenance/derived sensitivity. Session credentials and model keys stay
outside portable records and context. Unsupported policy/version, expired or
revoked authority, and unavailable provider contracts fail closed. Transcript or
tool-output instructions remain untrusted evidence, including inside prompts.

## Alternatives considered and rejected

A second MCP domain implementation would drift from CLI safety. Treating prompts
as capability policy permits injection-based escalation. Exposing all roots for
client-side filtering leaks metadata before authorization.

## Consequences and tradeoffs

No MCP transport, SDK, provider or authentication framework is selected. Local
session enforcement is implemented, but host confidentiality and broader Aether
capability conformance require independent evidence.

## Implementation and evidence links

This documentation-only checkpoint adds no runtime under #42. See the [decision
and ownership map](../target-architecture.md), [batch evidence](../garden-experience-milestone.md)
and linked source issues. Existing local prototypes are evidence, not acceptance.

## Replacement or exit strategy and migration cost

Use existing versioned record/query/context contracts at the boundary. A
transport can be removed without moving canonical knowledge. Migration cost is
capability/version mapping and equivalent CLI/agent conformance, not schema
ownership transfer to an agent host.

## Follow-up work and owners

Aether #69 owns the session handoff; Mindgarden #31/#47/#51 owns adapters/parity
and portable recovery proofs; Realm #20 owns host integration. Revisit before an
MCP endpoint or write-capable agent adapter, on owner contract publication, or by
2027-01-01. Start with synthetic read-only parity after human disposition.

