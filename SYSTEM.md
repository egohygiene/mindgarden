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
updated: 2026-08-28
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
| Garden contract | Implemented v0 | Defines manifests, notes, provenance, context packs, indexes, Obsidian profiles, and publish profiles through versioned schemas. |
| Ingestion pipeline | Implemented v0 baseline | Normalizes a supplied local UTF-8 artifact into a proposed source note and hash-bound provenance record; acquisition and interpretation are not yet implemented. |
| Normalization and indexing | Implemented v0 baseline | Builds a deterministic lexical catalog and explainable search results without provider state. |
| Synapse model | Target | Will represent richer typed relationships and cross-garden knowledge links; v0 currently validates note identifiers, `related`, and `supersedes`. |
| Context-pack builder | Implemented v0 baseline | Selects reviewed notes through bounded profiles and emits source-labelled Markdown or JSON context. |
| Obsidian projection | Implemented v0 profile | Defines a portable vault topology with native Bases and no required community plugins. |
| Quartz publication | Implemented v0 baseline | Projects reviewed public notes, rewrites source-boundary links, and renders through an immutable Quartz checkout. |
| Validation | Implemented v0 | Fails closed on schema, path, lifecycle, relationship, provenance, privacy, and publication violations. |
| Package and command interface | Implemented 0.1 | Provides a dependency-free installable Python package, unified `mindgarden` command, stable exit codes, public library surface, and temporary 0.x script shims. |
| Initialization and migration | Target | Will create and upgrade consumer-owned gardens without replacing canonical knowledge implicitly. |
| Federation and routing | Target | Will discover repository gardens and assemble organization-level projections through explicit contracts. |

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

- **Observed:** The v0 schemas, installable package, unified command, profiles, fixtures, clean-wheel smoke tests, and conformance tests provide runnable evidence for the implemented states above.
- **Decided:** Mindgarden owns reusable capability; each consumer owns its canonical `.garden/` knowledge.
- **Proposed:** v1 stabilization, initialization, archive interpretation, richer synapses, and federation remain roadmap work.
- **Open question:** Which v0 compatibility guarantees must be retained in the first independently versioned release?
