---
schema: aether.architecture-document/v1
id: mindgarden-system
title: Mindgarden System
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-19
updated: 2026-11-04
governed_by:
  - architecture-system
depends_on:
  - mindgarden-foundations
  - mindgarden-ontology
related:
  - mindgarden-purpose
  - mindgarden-vision
  - mindgarden-principles
  - mindgarden-pillars
supersedes: []
---

# Mindgarden System

## Purpose and scope

This document identifies Mindgarden's logical systems and responsibilities. It answers what the major systems do; [ARCHITECTURE.md](ARCHITECTURE.md) owns their structural organization and dependency rules.

## System inventory

| System | State | Responsibility |
| --- | --- | --- |
| Garden contract | V1 contract implemented; v0 runtime supported | Defines garden identity, sources, knowledge, claims, typed synapses, provenance, review, classification, projections, and migration history while preserving the v0 compatibility surface. |
| Ingestion pipeline | V0 preserved; v1 adapters on draft stack | Normalizes supplied UTF-8/Markdown and bounded v3.2.2/v3.2.3 conversation archives; acquisition and model-assisted proposal production are separate integrations. |
| Normalization and indexing | V0 preserved; reviewed v1 on draft stack | Builds authorized knowledge/claim indexes and explainable lexical search without provider state. |
| Synapse model | V1 runtime on draft stack | Validates typed local/cross-garden references and builds scoped graphs/backlinks with review boundaries. |
| Context-pack builder | V0 preserved; bounded v1 on draft stack | Emits reviewed, sensitivity-labelled Markdown/JSON with exact evidence and item/candidate/byte budgets. |
| Obsidian projection | Implemented v0 profile | Defines a portable vault topology with native Bases and no required community plugins. |
| Quartz publication | Implemented v0 baseline | Projects reviewed public notes, rewrites source-boundary links, and renders through an immutable Quartz checkout. |
| Validation | V0 preserved; general v1 on draft stack | Fails closed on version/schema, paths, relationships, provenance, scope and private-by-default publication, including empty allowlists. |
| Package and command interface | Implemented 0.1 | Provides a dependency-free installable Python package, unified `mindgarden` command, stable exit codes, public library surface, and temporary 0.x script shims. |
| Initialization and migration | V1 lifecycle implemented | Creates deterministic gardens and applies digest-bound, identity-preserving, provenance-safe migration with an exact v0 rollback tree. |
| Candidate routing | Local checkpoint on draft stack | Places authored reviewed candidates with private fallback, one home, typed references and recoverable multi-garden writes. |
| Source storage | Filesystem checkpoint on draft stack | Preserves immutable content identities, verifies checksums and supports bounded audit/export/restore/relocation independently from location. |
| Federation | Deferred integration | Later repository discovery and organization-level projections consume explicit contracts. |

## External systems

- Mindcap capture
- Aether agents
- repository-local .garden directories
- Obsidian
- Quartz and GitHub Pages

External systems are integrations, not hidden implementation units. Each requires version, authentication, availability, data, error, and replacement boundaries appropriate to its risk.

## System interactions

Inputs enter through an adapter or validated contract, move through domain systems, produce artifacts and diagnostics, and leave through a stable interface. Evidence flows back to validation, review, and future decisions.

## Failure model

Systems fail closed at destructive, publication, privacy, and security boundaries. Partial results identify coverage and remain distinguishable from complete success.

## Evidence and uncertainty

- **Observed:** The v1 schemas, adversarial fixtures, lifecycle regression suite, v0 runtime, installable package, profiles, clean-wheel smoke tests, and conformance tests provide runnable evidence for the implemented states above.
- **Decided:** Mindgarden owns reusable capability; each consumer owns its canonical `.garden/` knowledge.
- **Implemented on the milestone draft stack:** General v1 validation, local source storage, normalized-source adapters, reviewed retrieval/context, and authored curation have local conformance evidence. See CONTINUITY.md for exact revisions and checks.
- **Proposed/deferred:** Architecture ratification, federation, full media/registry/provider integration and external runtime assurance remain open. Local checkpoint evidence does not complete the parent issues.
- **Open question:** Which later consumer milestone permits deprecating the v0 runtime surface?

## Milestone ownership and state

| Concern | Owner | Milestone state |
| --- | --- | --- |
| Faithful capture and captured bundles | Mindcap or supplying capture tool | External input; no capture implementation here |
| Source normalization and exact evidence selectors | Mindgarden adapters/application | Text and bounded v3.2.2/v3.2.3 archive adapters on draft stack; full producer conformance unclaimed |
| Immutable original bytes | Explicit private vault, owned by consumer | Bounded filesystem identity/checksum/audit/export/restore/relocation on draft stack; media/triage/encrypted/provider acceptance open |
| Reviewed knowledge and typed relationships | Consumer garden; Mindgarden contracts/services | General v1 validation and reviewed projections on draft stack |
| Review, curation, routing and context selection | Mindgarden services; human authority | Authored curation, bounded context, candidate routing/recovery and local scope adversaries on draft stack; external policy/assurance integration open |
| Archival reservoir | Athena | Separate integration, deferred |
| Public reviewed resource catalog | Akashic | Separate publication approval and integration, deferred |
| Agent behavior and capabilities | Aether | Optional producer/session integration |
| Runtime and environment composition | Realm | Separate from semantic storage and policy |
| Normative policy and information flow | Hygiene | ADR policy ratified; confidential policy contract unavailable |
| Scaffolding, validation and build orchestration | Holon, EgoLint, Relay | Consume owner contracts; no copied implementations |
| Evidence read models and convergence | Observatory, Pace | Read-only evidence and reviewed adoption |
| Brand, visual and distribution outputs | Identity, Renderflow, Beacon | Downstream optional projections |
| Product/process orchestration and intake | Flow, organization .github | Consumers/coordination, not canonical garden owners |

See [the checkpoint specification](docs/private-garden-milestone.md) for dependency
corrections, implemented versus proposed behavior, and the finite usable proof.
The [evidence report](docs/private-garden-evidence.md) owns the synthetic result,
verification commands and remaining consumer/publication boundaries.
