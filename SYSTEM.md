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
updated: 2026-11-09
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
| Ingestion pipeline | V0 preserved; v1 adapter checkpoint merged | Normalizes supplied UTF-8/Markdown and tested v1/v2/v3 conversation profiles and pinned captured-source bundles; acquisition and model-assisted proposal production are separate integrations. |
| Normalization and indexing | V0 preserved; reviewed v1 checkpoint merged | Builds authorized knowledge/claim indexes and explainable lexical search without provider state. |
| Synapse model | V1 runtime checkpoint merged | Validates typed local/cross-garden references and builds scoped graphs/backlinks with review boundaries. |
| Context-pack builder | V0 preserved; bounded v1 checkpoint merged | Emits reviewed, sensitivity-labelled Markdown/JSON with exact evidence and item/candidate/byte budgets. |
| Obsidian projection | Implemented v0 profile | Defines a portable vault topology with native Bases and no required community plugins. |
| Quartz publication | Implemented v0 baseline | Projects reviewed public notes, rewrites source-boundary links, and renders through an immutable Quartz checkout. |
| Validation | V0 preserved; general v1 checkpoint merged | Fails closed on version/schema, paths, relationships, provenance, scope and private-by-default publication, including empty allowlists. |
| Package and command interface | Implemented 0.1 | Provides a dependency-free installable Python package, unified `mindgarden` command, stable exit codes, public library surface, and temporary 0.x script shims. |
| Initialization and migration | V1 lifecycle implemented | Creates deterministic gardens and applies digest-bound, identity-preserving, provenance-safe migration with an exact v0 rollback tree. |
| Candidate routing | Local checkpoint merged | Places authored reviewed candidates with private fallback, one home, typed references and recoverable multi-garden writes. |
| Source storage | Filesystem checkpoint merged | Preserves immutable content identities, verifies checksums and supports bounded audit/export/restore/relocation independently from location. |
| Federation | Local public checkpoint merged through #66 (#16) | Builds reviewed checksum-bound descriptor/index/graph/agent artifacts and supplied-directory catalogs; hosting, private federation and external adoption remain open. |
| Local registry | Linux lifecycle merged #67; owned cache recovery merged #82; [native macOS checkpoint merged #93](docs/registry-native-platforms.md) | Saved plans, named scope selections, non-destructive unregister, private restore and native ACL/path checks have bounded evidence; Windows, restricted/host assurance and destructive cleanup remain open. |
| V1 public preview | Merged #68; responsive correction #69 | Reuses scoped public selection for literal reviewed content, exact citations, typed links and pinned offline Quartz; broader UI/consumer acceptance remains open. |
| First-pass compaction | Merged #111 | Extends existing sessions with exact private source grants and authored first summaries; expiring private proof bundles preserve originals and grant no knowledge approval. |
| Optional semantic decisions | Merged #110 | Official TypeSafe SDK suggests a closed read intent; ordinary application code owns handlers, source access and permissions. Default commands require no model service. |
| Assistant-memory projection | Local reviewed checkpoint implemented | Provider-neutral seven-action compaction, bounded copyable snippets and optional live-checked expiring bundles; canonical sources stay independent. |
| Learning projection | Local authored/static-web checkpoint implemented | Reviewed factual/cloze cards, summaries, private history, versioned schedules and bounded due-card views with exact source revisions. |

The [rendered closeout checkpoint](docs/rendered-closeout-evidence.md) adds actual
browser and portal recovery evidence. Pinned renderer accessibility, shared Relay
action adoption and complete consumer acceptance remain open.

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
- **Implemented in the merged milestone checkpoint:** General v1 validation, local source storage, normalized-source adapters, reviewed retrieval/context, and authored curation have local conformance evidence. See CONTINUITY.md for exact revisions and checks.
- **Proposed/deferred:** Architecture ratification, full federation/consumer acceptance, remaining media/registry/provider integration and external runtime assurance remain open. Local checkpoint evidence does not complete the parent issues.
- **Open question:** Which later consumer milestone permits deprecating the v0 runtime surface?

## Milestone ownership and state

| Concern | Owner | Milestone state |
| --- | --- | --- |
| Faithful capture and captured bundles | Mindcap or supplying capture tool | External input; no capture implementation here |
| Source normalization and exact evidence selectors | Mindgarden adapters/application | Text and bounded v3.2.2/v3.2.3 archive adapters implemented in the merged checkpoint; full producer conformance unclaimed |
| Immutable original bytes | Explicit private vault, owned by consumer | Bounded filesystem identity/checksum/audit/export/restore/relocation implemented in the merged checkpoint; merged ordinary PDF/media inventory/triage follow-up supplied; encrypted/provider acceptance open |
| Reviewed knowledge and typed relationships | Consumer garden; Mindgarden contracts/services | General v1 validation and reviewed projections implemented in the merged checkpoint |
| Review, curation, routing and context selection | Mindgarden services; human authority | Authored curation, bounded context, candidate routing/recovery and local scope adversaries implemented in the merged checkpoint; external policy/assurance integration open |
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

The [open-issue coverage ledger](docs/open-issue-coverage.md) records the
2026-11-05 merge receipts, remaining parent scope and proposed delivery batches.


## Merged six-checkpoint state

| Capability | State | Evidence and remaining gate |
| --- | --- | --- |
| V1 preview, optional design consumer | Merged #68/#69; tested | Actual pinned offline render and browser evidence; full UI/consumer acceptance open |
| Publication/preview conformance | Merged #70; tested | Reusable synthetic 80-test source/installed pack; normative runtime/consumer coverage open |
| Portal composition | Merged #71; tested | Pinned artifact/owned receipt, sibling preservation and recovery; Relay/deployment open |
| Target-product architecture | Merged #72 documentation; decisions remain proposed | [Ten-topic decision/ownership map](docs/target-architecture.md); human ratification and owner acceptance open |
| Hierarchical compaction/retention | Bounded #46 checkpoint merged through #73 | Read-only exact-evidence hierarchy, private invalidation manifests and authored curation proof; raw-only compaction, retention execution and approved pilot remain open |

The target map expands the repository/runtime responsibility table without
transferring canonical ownership. Shared services remain the existing Python
engine. Neither a tested draft nor its later merge accepts a proposed ADR.

The [merge receipt](docs/merged-experience-checkpoints.md) records main `30a2966`
and the exact tested-tree comparison. Broader parent acceptance remains separate.

## Source-workflow draft checkpoint

The [source-workflow sprint](docs/source-workflow-sprint.md) extends the same Python
services with adapter conformance, authored curation transformations, selective
archive attachments, private canonical-home transitions, projection coverage and
pinned rendered discovery. Drafts #74–#79 are implemented/tested and unmerged.
Original sources remain immutable private evidence; reviewed garden records own
knowledge; catalogs, rendered artifacts and package references remain rebuildable
data. Proposed ADR-0011's extension and ADR-0022 are not accepted by these tests.

The [private-storage checkpoints](docs/private-storage-sprint.md) extend Mindgarden's
normalization, policy, scoped output, registry-cache recovery and asset review
services. Capture still belongs to the supplying tool; immutable originals belong
to the consumer vault; human review owns knowledge and triage decisions. Optional
parser/provider factories do not acquire policy or runtime authority. Proposed
ADRs remain unapproved; merged implementation is separate from full parent acceptance.

## Product checkpoint status

[The broader product stack](docs/product-checkpoints.md) contains tested draft
checkpoints for ADR metadata, optional query storage, dependency-aware derived
builds, reviewed assistant memory and private bookmark exports. These remain
reviewable branches, not fully accepted parent issues. Canonical Gardens and
immutable sources retain ownership; projections can be rebuilt. Shared Decisions
preview currently retains a native source-validation finding. Historical backfill
and the API/web/runtime slice remain behind their respective decision gates.
Release work is deferred pending organization release conventions.
