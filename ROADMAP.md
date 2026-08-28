---
schema: aether.architecture-document/v1
id: mindgarden-roadmap
title: Mindgarden Roadmap
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-19
updated: 2026-08-28
governed_by:
  - architecture-roadmap
depends_on:
  - mindgarden-vision
  - mindgarden-pillars
  - mindgarden-architecture
  - mindgarden-decisions
related:
  - mindgarden-purpose
  - mindgarden-principles
  - mindgarden-manifesto
  - mindgarden-epistemology
supersedes: []
---

# Mindgarden Roadmap

<!-- BEGIN ROADMAP EXECUTION SNAPSHOT -->
<!-- roadmap-manifest
schema: hygiene.roadmap/v1alpha1
repository: egohygiene/mindgarden
visibility: public
publication: central
route: /roadmap/mindgarden/
updated: 2026-08-28
-->
## 2026-08-28 execution snapshot

> This evidence-reconciled snapshot is the issue-generation and visual-roadmap handoff. The longer-horizon strategy below remains canonical context; generated HTML, JSON, progress, issue plans, and commit lists are projections.

**Lifecycle:** seed, extraction stage  
**Current gate:** Complete standalone extraction, then move Empathy to an immutable consumption interface.
**North-star outcome:** A private-by-default personal knowledge garden with versioned ingestion, indexing, context-pack, and publication boundaries.

### Visual roadmap publication

**Mode:** `central`  
**Route:** `/roadmap/mindgarden/`  
**Current publication evidence:** Documentation only; Pages or Quartz publication is planned but absent.

Publish the public-safe projection through egohygiene.io at /roadmap/mindgarden/. This repository owns intent and acceptance evidence; it does not add a second site deployment.

### Quest line

<!-- roadmap-step
id: MIG-Q01
status: complete
depends_on: []
issues: [1, 2]
-->
#### MIG-Q01 — Define the standalone architecture

**State:** `complete`  
**Depends on:** None

**Outcome:** A repository and architecture shell identify Mindgarden as a standalone product.

**Exit criteria:**

- [x] Architecture and extraction intent are documented.
- [x] Initial knowledge and projection work is tracked.

**Current evidence:**

- Architecture PR #3 merged at 857bccf0c848c3730875b45a997703ead54c473e on 2026-08-20.
- Issues #1 and #2 opened on 2026-08-19.

<!-- roadmap-step
id: MIG-Q02
status: active
depends_on: [MIG-Q01]
issues: [6]
-->
#### MIG-Q02 — Extract the incubated implementation

**State:** `active`  
**Depends on:** `MIG-Q01`

**Outcome:** Mindgarden owns runnable code and fixtures rather than depending on Empathy cache composition.

**Exit criteria:**

- [x] The authoritative implementation lives in this repository.
- [ ] Empathy consumes it through a declared version or build interface.

**Current evidence:**

- Issue #6 imports the v0 engine with nine commits of provenance-linked source history.
- Contracts, commands, profiles, synthetic fixtures, and Python/Node CI are now standalone.
- Empathy consumer content and generated/private state remain excluded.
- Empathy cutover to a pinned standalone release or commit remains open.

<!-- roadmap-step
id: MIG-Q03
status: planned
depends_on: [MIG-Q02]
issues: [1]
-->
#### MIG-Q03 — Implement the knowledge contract

**State:** `planned`  
**Depends on:** `MIG-Q02`

**Outcome:** Issue #1 yields a versioned schema and validator for private knowledge records.

**Exit criteria:**

- [ ] Valid and invalid fixtures are tested in CI.
- [ ] Identity, provenance, privacy, and migration fields are explicit.

**Current evidence:**

- Issue #1 tracks the knowledge contract.
- Seven v0 schemas, dependency-free validation, and valid/invalid contract tests provide a baseline for v1 stabilization.

<!-- roadmap-step
id: MIG-Q04
status: planned
depends_on: [MIG-Q03]
issues: []
-->
#### MIG-Q04 — Build adapters, index, and context packs

**State:** `planned`  
**Depends on:** `MIG-Q03`

**Outcome:** Captured records become searchable and can yield bounded context packs through stable interfaces.

**Exit criteria:**

- [ ] At least one Mindcap fixture indexes deterministically.
- [ ] Context packs record selection and redaction provenance.

**Current evidence:**

- The extracted v0 engine implements supplied-file ingestion, hash-bound provenance, deterministic lexical indexing, explainable search, and bounded context packs.
- Mindcap/archive interpretation and the stable adapter boundary remain unimplemented.

<!-- roadmap-step
id: MIG-Q05
status: planned
depends_on: [MIG-Q04]
issues: [2]
-->
#### MIG-Q05 — Publish privacy-safe projections

**State:** `planned`  
**Depends on:** `MIG-Q04`

**Outcome:** Issue #2 produces an opt-in Pages or Quartz projection that cannot expose private records by default.

**Exit criteria:**

- [ ] Publication requires explicit inclusion and passes leak fixtures.
- [ ] A green workflow builds and deploys the public projection.

**Current evidence:**

- Issue #2 tracks projections.
- The v0 reviewed-public projector and immutable Quartz adapter are tested with a synthetic consumer fixture.
- Consumer deployment workflows and an organization-level garden route remain unimplemented.

### Roadmap-to-issue handoff

- A step is complete only when its exit criteria and required evidence are satisfied; commit count never determines progress.
- Ready steps without an issue are candidates for the private, duplicate-aware roadmap.issue-plan.json dry run. Planned steps remain preview-only unless a reviewer explicitly opts them in with issue_policy: propose.
- Issue creation or reconciliation requires human approval or an explicitly authorized Pace operation and returns issue references through a reviewable roadmap pull request.
- Pull requests and commits should include Roadmap-Step: <ID>; historical evidence may be linked through existing issue and pull-request relationships.
- Public rendering uses only allowlisted build-time evidence and never places a GitHub token or private issue plan in the browser artifact.

<!-- END ROADMAP EXECUTION SNAPSHOT -->

## Strategic context

This roadmap describes capability evolution, not promised dates or an issue queue. Sequence follows architecture dependencies and may change when evidence or risk changes.

## Phase 1: Extract the Empathy incubation

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Phase 2: Stabilize garden and provenance schemas

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Phase 3: Harden deterministic indexing

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Phase 4: Publish privacy-safe projections

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Phase 5: Support interoperable knowledge adapters

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Cross-cutting tracks

- Security, privacy, accessibility, licensing, and provenance.
- Documentation, architecture portals, examples, and onboarding.
- Packaging, release, compatibility, and self-hosting.
- Organization integration through explicit contracts.
- Observatory evidence and Pace conformance when those systems exist.

## Deferred direction

Optional managed services, enterprise controls, marketplaces, and the conversational organization compiler remain later architecture work. Current choices should preserve portability and avoid foreclosing them.

## Evidence and uncertainty

- **Observed:** A provenance-linked v0 implementation, synthetic fixture, and standalone test workflow now exist in this repository.
- **Decided:** Source ownership graduates before Empathy consumer cutover and before v1 contract expansion.
- **Proposed:** Stable archive adapters, v1 schemas, initialization, release packaging, publication composition, and federation remain later steps.
- **Open question:** Which consumption format should Empathy pin first: a release archive, package, or immutable source checkout?
