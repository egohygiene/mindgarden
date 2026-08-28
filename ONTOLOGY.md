---
schema: aether.architecture-document/v1
id: mindgarden-ontology
title: Mindgarden Ontology
kind: architecture-document
version: 1.0.0
status: active
owners:
  - egohygiene
created: 2026-08-19
updated: 2026-08-28
governed_by:
  - architecture-ontology
depends_on:
  - mindgarden-purpose
  - mindgarden-vision
  - mindgarden-principles
  - mindgarden-epistemology
related:
  - mindgarden-pillars
  - mindgarden-manifesto
  - mindgarden-ai-constitution
  - mindgarden-personal-model
supersedes: []
---

# Mindgarden Ontology

## Domain scope

Mindgarden models the concepts needed to turn governed source material into
navigable, provenance-aware knowledge that humans and agents can use without
losing original context. The ontology names conceptual entities and
relationships. JSON Schemas define their serialized contracts; neither the
ontology nor those schemas prescribe a database or authoring-folder taxonomy.

## Canonical concepts

| Concept | Meaning |
| --- | --- |
| Garden | A stable knowledge identity, owner, visibility boundary, contract capability, classification scope, and publication policy. A repository, person, or organization may own a garden. |
| Source | A faithfully captured or deterministically normalized artifact. It remains distinct from durable knowledge and is unpublished by default. |
| Knowledge | A durable, human-readable unit such as a map, concept, decision, project, procedure, insight, reference, or note. |
| Claim | One checkable statement with an epistemic state, confidence, review state, and explicit evidence relationships. |
| Evidence | A source locator or artifact reference that supports, contradicts, leaves uncertain, or supersedes a claim. |
| Synapse | A typed, reviewable relationship between stable artifacts, including cross-garden artifacts. |
| Provenance | An ordered record connecting an artifact to input hashes, transformations, generator identity, origin, and rights. |
| Review | Human authority state independent of authorship, lifecycle, confidence, and visibility. |
| Classification | Authoritative `domains` and `topics`; aliases and tags provide discovery aids without replacing the taxonomy. |
| Routing declaration | A garden's declared domain/topic scope and optional explicit private fallback. It does not perform routing. |
| Projection | A disposable index, graph, context pack, agent entrypoint, site, or federation artifact produced under an allowlist policy. |
| Migration record | A plan or history record that preserves identity and provenance while describing movement between contract versions. |

## Independent axes

| Axis | Canonical fields | Rule |
| --- | --- | --- |
| Identity | `garden`, `id`, `canonical_uri`, immutable `revision` | A path or title never substitutes for identity. |
| Lifecycle | `status`, `created`, `updated` | Lifecycle does not imply review or truth. |
| Epistemic state | `epistemic_state`, `confidence` | Confidence does not imply approval. |
| Authority | `authors`, `review` | Agent authorship and human review remain distinguishable. |
| Classification | `domains`, `topics`, `aliases`, `tags` | Domains and topics are authoritative regardless of folder placement. |
| Privacy | `visibility`, `publication` | Visibility does not grant publication; publication requires an explicit allowlist and approval. |
| Evidence | `sources`, `evidence`, `provenance` | Missing evidence remains missing; migration never invents portable references. |

## Core relationships

- A garden owns sources, knowledge, claims, synapses, provenance records,
  projections, and migration records through stable identifiers.
- A source may yield multiple knowledge units; knowledge may cite precise source
  locators without copying raw private content into public metadata.
- Evidence supports, contradicts, leaves uncertain, or supersedes a claim.
- A synapse relates artifacts without moving either artifact from its canonical
  garden.
- Provenance connects every derived artifact to ordered transformations and
  content hashes.
- A projection reads approved canonical records and remains disposable.
- A migration record describes preservation and change; a later migration
  command controls plan and apply authority.

## Boundaries

- Conceptual identity is distinct from filesystem path, database identifier, or display label.
- Folder placement is an authoring convenience. It cannot override `domains` or `topics`, and knowledge is not duplicated merely to appear in multiple folders.
- Raw sources, unknown material, and agent proposals default to private, excluded, proposed, and unreviewed states as applicable.
- Observed state is distinct from desired state; a proposed relationship is not an accepted fact.
- Cross-garden references use stable garden/artifact identifiers and optional immutable revisions, never mutable branch names.
- Unknown values use an allowed `null`, an empty list, or an explicit unresolved state. Producers do not fabricate provenance.
- Extension fields require the `x-` prefix and cannot redefine canonical fields.
- Neighboring repositories retain ownership of their domain concepts.

## Evidence and uncertainty

- **Observed:** `contracts/v1/` serializes every canonical concept above through JSON Schema 2020-12 and exercises them with valid and adversarial fixtures.
- **Decided:** The v1 vocabulary and independent axes are active contract language; v0 remains available during migration.
- **Proposed:** Initialization, migration execution, routing, archive curation, and federation remain later roadmap work built on this vocabulary.
- **Open question:** Which optional extension vocabularies should be standardized after 1.0 consumer evidence exists?
