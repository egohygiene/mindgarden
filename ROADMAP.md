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
updated: 2026-08-24
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
updated: 2026-08-24
-->
## 2026-08-24 execution snapshot

> This evidence-reconciled snapshot is the issue-generation and visual-roadmap handoff. The longer-horizon strategy below remains canonical context; generated HTML, JSON, progress, issue plans, and commit lists are projections.

**Lifecycle:** seed, extraction stage  
**Current gate:** Extract the incubated implementation from Empathy and establish a tested knowledge contract.  
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
issues: []
-->
#### MIG-Q02 — Extract the incubated implementation

**State:** `active`  
**Depends on:** `MIG-Q01`

**Outcome:** Mindgarden owns runnable code and fixtures rather than depending on Empathy cache composition.

**Exit criteria:**

- [ ] The authoritative implementation lives in this repository.
- [ ] Empathy consumes it through a declared version or build interface.

**Current evidence:**

- No code, schemas, tests, or workflows were observed in Mindgarden.
- Empathy currently composes .cache/mindgarden output.

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

- No ingestion, index, or context-pack implementation was observed.

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
- No CI, Pages, or release publication was observed.

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

- **Observed:** The repository README establishes the intended boundary as a versioned knowledge-garden and second-brain foundation for repositories, people, and organizations; significant implementation remains incomplete.
- **Decided for this draft:** The repository owns the bounded concern described here and participates through versioned contracts.
- **Proposed:** Target systems and later roadmap phases remain proposals until accepted and implemented.
- **Open question:** Which parts of this draft should become active in the first independently versioned release?
