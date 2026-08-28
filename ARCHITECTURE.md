---
schema: aether.architecture-document/v1
id: mindgarden-architecture
title: Mindgarden Architecture
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-19
updated: 2026-08-28
governed_by:
  - architecture-architecture
depends_on:
  - mindgarden-foundations
  - mindgarden-system
related:
  - mindgarden-purpose
  - mindgarden-vision
  - mindgarden-principles
  - mindgarden-pillars
supersedes: []
---

# Mindgarden Architecture

## Architectural intent

Mindgarden is a local-first knowledge substrate. A repository's `.garden/`
directory is canonical; every user interface, search index, agent integration,
and published site is an adapter or derived projection.

## Layers

1. **Knowledge contract** — versioned manifests, Markdown notes, YAML
   frontmatter, stable identifiers, provenance, confidence, and lifecycle.
2. **Garden engine** — initialization, validation, migration, indexing, and
   deterministic transformations.
3. **Adapters** — Obsidian configuration, agent CLI/MCP access, search, and
   GitHub Pages publishing.
4. **Consumer gardens** — repository-owned `.garden/` instances such as
   Empathy's initial garden.

Dependencies flow downward from consumer adapters toward the knowledge
contract. The knowledge contract cannot depend on Obsidian, a particular LLM,
an embedding provider, or a site generator.

## Source and projection boundary

- Markdown and YAML committed under `.garden/` are durable source.
- Generated indexes, embeddings, caches, and rendered sites are disposable.
- Deterministic ingestion records the supplied artifact, declared origin,
  transformations, and hashes without fetching or interpreting the source.
- Agent search and context packs are bounded projections with explainable
  lexical ranking; reviewed knowledge is the default trust boundary.
- The publishing projector admits only reviewed public notes, rewrites links
  across the source boundary, and produces a disposable renderer input.
- Quartz is an immutable external adapter; neither its checkout nor rendered
  output is committed as canonical knowledge.
- Agent-authored knowledge enters as `draft` or `proposed` and remains visibly
  unreviewed until a human promotes it.
- A public repository may commit only public garden material.
- Private or internal material belongs in an ignored external overlay such as
  `.garden.local/`, not in a build-exclusion convention.

## Ownership and integration boundary

This repository is the sole durable source owner for reusable Mindgarden
capability. Consumer repositories own their `.garden/` knowledge and integrate
through an immutable Mindgarden release, package, or commit. Mindgarden does not
import consumer internals, and consumers do not copy or fork this source as an
embedded implementation.

Empathy remains the first golden consumer. Its migration from the incubated
copy to a pinned standalone dependency is tracked separately so extraction and
consumer cutover remain independently reviewable.

## Dependency rules

- Sibling capabilities integrate through versioned public contracts.
- Generated artifacts never become canonical source.
- Provider and platform adapters depend on stable contracts; core behavior does
  not depend on a provider implementation.
- Read, plan, apply, verify, publish, and recover remain separate authority
  boundaries when consequential.
- Cross-repository references use releases, immutable commits, schemas,
  packages, or documented APIs rather than mutable default branches.

## Current evidence and target evolution

The contract schemas, validation, local artifact ingestion, lexical indexing,
context packs, Obsidian profile, public projection, and Quartz adapter are
implemented as a preserved v0 baseline. Initialization, migrations, richer
relationship semantics, archive interpretation, and federation remain target
capabilities. [SYSTEM.md](SYSTEM.md) owns the capability inventory and
[ROADMAP.md](ROADMAP.md) owns delivery order.
