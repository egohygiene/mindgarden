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
updated: 2026-11-05
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
   frontmatter, stable identifiers, sources, knowledge, claims, typed synapses,
   provenance, review, confidence, privacy, classification, and lifecycle.
2. **Garden engine** — initialization, validation, migration, indexing, and
   deterministic transformations.
3. **Adapters** — Obsidian configuration, agent CLI/MCP access, search, and
   GitHub Pages publishing.
4. **Consumer gardens** — repository-owned `.garden/` instances such as
   Empathy's initial garden.

Dependencies flow downward from consumer adapters toward the knowledge
contract. The knowledge contract cannot depend on Obsidian, a particular LLM,
an embedding provider, or a site generator.

## Package structure

The installable Python package mirrors those dependency boundaries:

- `mindgarden.domain` owns contract parsing and validation;
- `mindgarden.application` owns deterministic use cases over the domain;
- `mindgarden.adapters` owns filesystem and renderer integrations;
- `mindgarden.interfaces` owns CLI parsing, diagnostics, and process exit codes.

The stable `mindgarden` console entry point depends inward through those
layers. Root-level `scripts/` files are temporary 0.x compatibility shims and
contain no reusable implementation. Package construction includes the public
schemas, profiles, and templates without moving their repository source of
truth.

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

## Contract-version boundary

The shipped v0 runtime and root contract files remain the 0.1 compatibility
surface. The additive [`contracts/v1/`](contracts/v1/) registry defines the
target semantic model without silently changing consumer behavior. V1 uses
stable `{garden, id}` identities, optional immutable revisions, independent
semantic axes, authoritative domain/topic metadata, and explicit publication
allowlists.

V1 schema availability alone is not hardened v1 runtime support. Issue #7 adds
deterministic initialization and review-gated migration with lifecycle-level
integrity checks; the merged milestone stack now adds general cross-record, path,
body, attachment, and leak validation for #10. Migration remains side-by-side,
digest-bound, atomic, and rollback-safe.

## Current evidence and target evolution

The v1 semantic contract, valid/adversarial schema fixtures, v0 compatibility
matrix, v0 validation, local artifact ingestion, lexical indexing, context
packs, Obsidian profile, public projection, and Quartz adapter are implemented
behind the installable 0.1 package and CLI. The merged milestone stack extends
general v1 validation, source adapters and reviewed projections. Local public
federation is merged through #66; broader federation remains a target capability.
Implementation and merging do not ratify proposed ADRs.
[SYSTEM.md](SYSTEM.md) owns the capability inventory and [ROADMAP.md](ROADMAP.md)
owns delivery order.

## Portable private-garden milestone

The bounded [milestone specification](docs/private-garden-milestone.md) and
[proposed ADR-0007 through ADR-0010](docs/decisions/README.md) extend the existing
consumer-ownership, review, deterministic projection and additive migration
directions. New decisions remain proposed; the user authorized their bounded
implementation and subsequently merging #52–#64, without architecture ratification.

Reviewed portable records own semantic knowledge. Captured originals have a
separate private storage boundary. Logical artifact identity, immutable content
identity and machine-local storage bindings are distinct. Query stores and
graphs remain rebuildable. CLI and future interfaces call shared Python
application services; adapters normalize supplied artifacts without acquisition
or model calls. Hosted storage and model providers are optional.

The first target is single-user, single-writer and local-first. Authentication,
collaboration, multi-writer synchronization, deployment topology, specialized
databases and web frameworks remain deferred. Runtime confidentiality claims
require separate Realm/Hygiene evidence.

The local implementation now includes filesystem vault recovery and exact
reviewed-citation resolution. [The finite proof](docs/private-garden-evidence.md)
records the archive-to-context and relocation boundary. Portable records, immutable
content and explicit location bindings remain separate; ordinary application
services require no hosting, model provider, web framework or specialized store.
The merged [private-storage sprint](docs/private-storage-sprint.md) adds bounded
ordinary PDF/media preservation, private inventory and append-only asset triage.
Confidential/provider/platform assurance, destructive retention and consumer
publication remain unverified integration scope. Proposed ADRs remain proposed after implementation.

The [open-issue coverage ledger](docs/open-issue-coverage.md) records the
2026-11-05 merge receipts, remaining parent scope and proposed delivery batches.

## Public discovery checkpoint

The merged #16 checkpoint (#66) adds [reviewed public discovery artifacts](docs/federation.md)
over existing scoped retrieval and `mindgarden.projection/v1` profiles. Proposed
[ADR-0011](docs/decisions/ADR-0011-public-federation-projections.md) records the
sanitized represented-revision, canonical-route and supplied-catalog boundaries.
Session/profile hashes and local storage locations remain control state. Public
bundles and catalogs are rebuildable projections; original knowledge ownership
does not move. Unsigned checksums establish consistency, not authenticated human
authority. Remote acquisition, serving, private federation and signing are
explicit unavailable capabilities rather than hidden integrations.

## Machine-local registry checkpoint

Merged [#67](https://github.com/egohygiene/mindgarden/pull/67) implements the bounded
[#30 registry lifecycle](docs/local-registry.md), under proposed
[ADR-0012](docs/decisions/ADR-0012-machine-local-registry.md). Existing portable
manifests own garden IDs, owners and declared scope. Application services manage
optional metadata in existing local bindings; a Linux filesystem adapter owns
private control files, kernel writer leases, atomic replacement and snapshots.
Named selections constrain existing session grants without expanding authority.
Originals and knowledge remain read-only inputs. Public projections exclude
registry paths, labels, membership and control hashes. Restricted/encrypted
runtime, native macOS/Windows mutation and owned-cache cleanup remain deferred.

The [v1 preview checkpoint](docs/v1-site.md) reuses the same public selection
service and existing Quartz adapter, with proposed [ADR-0013](docs/decisions/ADR-0013-reviewed-v1-site-projections.md).
Prepared software acquisition is separate from offline rendering; canonical
records remain read-only and output manifests contain public lineage only.


## Proposed target-product decision sequence

The [target decision/ownership map](docs/target-architecture.md) covers all ten
#42 topics and links #40's product/ADR gate. ADR-0007–0021 remain proposed with
null approval; implementation, verification, review and merge state are separate.
The additional query, tenancy, topology, lifecycle, agent-interface and
build-versus-integrate proposals introduce no runtime implementation here.

Portable consumer records, private originals, canonical public catalogs, machine-
local authority and disposable query/rendered outputs have distinct owners. The
map assigns capture/normalization/storage/curation and all named repository/runtime
boundaries, plus independent bookmark cleanup and publication approvals.
Conditional follow-ups become executable only after the relevant human and owner
dispositions. Authentication, collaboration, specialized stores, jobs, MCP and
new product integrations retain evidence requirements and revisit triggers.
