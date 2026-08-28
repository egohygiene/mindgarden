---
schema: aether.architecture-document/v1
id: mindgarden-decisions
title: Mindgarden Decisions
kind: architecture-document
version: 1.0.0
status: active
owners:
  - egohygiene
created: 2026-08-19
updated: 2026-08-28
governed_by:
  - architecture-decisions
depends_on:
  - mindgarden-principles
  - mindgarden-epistemology
  - mindgarden-foundations
  - mindgarden-system
  - mindgarden-architecture
related:
  - mindgarden-purpose
  - mindgarden-vision
  - mindgarden-pillars
  - mindgarden-manifesto
supersedes: []
---

# Mindgarden Decisions

## Purpose

This document preserves significant accepted architectural choices and their rationale. Issues coordinate work, proposals explore alternatives, and this file records decisions that constrain future implementation.

## Governance

Do not rewrite historical context to fit current understanding. Amend a record for corrections that do not change meaning; supersede it with a new record when the decision changes materially.

## Index

- ADR-001: Keep the consumer garden repository-owned
- ADR-002: Separate reviewed public projection from private source
- ADR-003: Provide deterministic context packs for agents
- ADR-004: Keep classification independent from folder layout
- ADR-005: Use stable cross-garden identities and immutable revisions
- ADR-006: Introduce v1 additively through reviewed migration

## ADR-001: Keep the consumer garden repository-owned

- **Status:** Accepted as the current architectural direction
- **Date:** 2026-08-19
- **Context:** Repository evidence and ecosystem ownership require an explicit durable boundary.
- **Decision:** Keep the consumer garden repository-owned.
- **Consequences:** The choice improves ownership and predictability while requiring maintained contracts, validation, and migration discipline.
- **Reconsider when:** New evidence shows that the boundary prevents standalone usefulness, safety, portability, or maintainability.

## ADR-002: Separate reviewed public projection from private source

- **Status:** Accepted as the current architectural direction
- **Date:** 2026-08-19
- **Context:** Repository evidence and ecosystem ownership require an explicit durable boundary.
- **Decision:** Separate reviewed public projection from private source.
- **Consequences:** The choice improves ownership and predictability while requiring maintained contracts, validation, and migration discipline.
- **Reconsider when:** New evidence shows that the boundary prevents standalone usefulness, safety, portability, or maintainability.

## ADR-003: Provide deterministic context packs for agents

- **Status:** Accepted as the current architectural direction
- **Date:** 2026-08-19
- **Context:** Repository evidence and ecosystem ownership require an explicit durable boundary.
- **Decision:** Provide deterministic context packs for agents.
- **Consequences:** The choice improves ownership and predictability while requiring maintained contracts, validation, and migration discipline.
- **Reconsider when:** New evidence shows that the boundary prevents standalone usefulness, safety, portability, or maintainability.

## ADR-004: Keep classification independent from folder layout

- **Status:** Accepted
- **Date:** 2026-08-28
- **Context:** Knowledge may belong to multiple conceptual domains while a file has only one path. Folder-derived taxonomy encourages duplication and makes identity unstable during moves.
- **Decision:** Make `domains` and `topics` authoritative metadata. Treat folders, aliases, and tags as authoring and discovery conveniences.
- **Consequences:** Consumers must read metadata to classify knowledge, but file moves no longer change meaning and multi-domain knowledge remains one canonical artifact.
- **Reconsider when:** A future storage model can preserve stable identity and multi-axis classification without metadata.

## ADR-005: Use stable cross-garden identities and immutable revisions

- **Status:** Accepted
- **Date:** 2026-08-28
- **Context:** Organization federation and repository references cannot rely on mutable branches, rendered URLs, or copied note bodies.
- **Decision:** Identify artifacts by `{garden, id}` and allow only Git commit, SHA-256, or v1 semantic-version revisions when a reference is pinned.
- **Consequences:** References remain portable and auditable. Consumers must resolve garden identities through explicit catalogs rather than guessing repository layouts.
- **Reconsider when:** A stronger content-addressed identity standard is adopted without weakening offline resolution or ownership.

## ADR-006: Introduce v1 additively through reviewed migration

- **Status:** Accepted
- **Date:** 2026-08-28
- **Context:** The shipped 0.1 CLI and existing consumers use v0, while v1 separates sources, knowledge, claims, synapses, review, classification, and publication authority.
- **Decision:** Preserve v0 schemas and runtime behavior while publishing v1 in a parallel registry. Migration must plan before apply, preserve identifiers and provenance, stage atomically, and never invent missing evidence.
- **Consequences:** The transition takes more than one issue but remains rollback-safe and independently reviewable. v1 schema availability does not imply v1 runtime support.
- **Reconsider when:** All supported consumers have migrated and the compatibility policy permits retiring v0.

## Open decisions

- Exact self-hosted, managed, and organization-integrated deployment boundaries.
- Which target systems must exist before the architecture status may become active.

## Evidence and uncertainty

- **Observed:** The v1 schema registry, compatibility matrix, and conformance fixtures implement ADR-004 through ADR-006 as reviewable contracts.
- **Decided:** Consumer ownership, private/public separation, deterministic projections, metadata classification, stable references, and additive migration constrain 1.0 implementation.
- **Proposed:** Runtime migration, validation, routing, federation, and garden rendering remain later roadmap work.
- **Open question:** When may v0 move from supported compatibility surface to archived contract evidence?
