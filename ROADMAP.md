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
updated: 2026-11-12
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
updated: 2026-11-12
-->
## 2026-11-12 execution snapshot

> This evidence-reconciled snapshot is the issue-generation and visual-roadmap handoff. The longer-horizon strategy below remains canonical context; generated HTML, JSON, progress, issue plans, and commit lists are projections.

**Lifecycle:** seed, extraction stage  
**Current gate (2026-11-12):** Main `f5baa3d` contains authorized merges #127–#132, with the exact combined #132 tree. All six original heads have passing hosted checks. #10 stays closed and the other parents keep their wider acceptance scope. Proposed ADRs, release #19/#27 and deferred #86–#91 remain parked.
**Selected follow-through:** [The reading/evidence journey](docs/journey-sprint.md) records merged #15/#13 proofs and the new reviewed incoming-reference repair (#14), followed by #16 → #17 → #20. Execution recovered; focused checks run as changes land. Broader full/local `act` qualification is deferred by the maintainer and never represented as passing. Keep new bounded PRs reviewable and synthetic.
**North-star outcome:** A private-by-default personal knowledge garden with versioned ingestion, indexing, context-pack, and publication boundaries.

### Complete open-issue coverage and next batches

The [open-issue coverage ledger](docs/open-issue-coverage.md) records every current
open issue's purpose, implementation/PR evidence, unmet acceptance, dependencies,
status and proposed batch. It also records proposed dependency corrections and
early retention requirements. This roadmap owns delivery order; the ledger makes
its evidence and remaining scope inspectable.

The authorized stack #52–#64 is merged at
`9fae752b3cf7eb9c74033a72a12d125c42f8659e`, with exactly the tested combined
tree. Both supported Python versions pass 139 tests. These bounded checkpoints
do not close their parents or ratify ADR-0007–0010, which remain proposed.

B0 coverage (#65) and B1 local public descriptors/projections (#66) are merged
at `44cc1e8`, with 159 baseline tests passing on both supported Python versions.
B2 [#67](https://github.com/egohygiene/mindgarden/pull/67) is merged at `8a9650e`:
saved lifecycle plans, named scoped selections, non-destructive unregister,
private snapshots/restore and synthetic public isolation evidence. Its tree is
the tested `3463d46` tree; 188 tests pass on both supported Python versions.
See [the registry proof](docs/local-registry.md). Full #30 and ADR acceptance
remain open. The [six-checkpoint map](docs/garden-experience-milestone.md)
records #68–#73, now merged at `30a2966`. The
[merge receipt](docs/merged-experience-checkpoints.md) verifies the unchanged tested
tree and separates proposal, implementation, test and acceptance state. ADRs remain
proposed. The confirmed sprint #11 → #13 → #15 → #14 → #12 → #16 is merged through #74–#79, followed by policy/storage #80–#84; see
[the merge receipt](docs/merged-pipeline-storage-checkpoints.md).
Public `/garden`/portal proofs (#17/#18) and the complete #20 consumer path follow
their actual contracts. #27 release preparation and #38 design tokens can advance
independently. #46 retention policy is considered early; full compaction, SQLite,
broader API/web product work and optional evaluations retain their own gates.

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
issues: [6, 8]
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
- Issue #8 packages the v0 engine behind the dependency-free `mindgarden` command and importable Python API while retaining 0.x script compatibility.
- Source and wheel distributions build successfully and pass clean-environment installation tests; final PyPI trusted publication remains a 1.0 release gate.
- Empathy consumer content and generated/private state remain excluded.
- Empathy cutover to a pinned standalone release or commit remains open.

<!-- roadmap-step
id: MIG-Q03
status: active
depends_on: [MIG-Q02]
issues: [1, 9, 7, 10]
-->
#### MIG-Q03 — Implement the knowledge contract

**State:** `active`
**Depends on:** `MIG-Q02`

**Outcome:** Issue #1 yields a versioned schema and validator for private knowledge records.

**Exit criteria:**

- [x] Valid and invalid fixtures are tested in CI.
- [x] Identity, provenance, privacy, and migration fields are explicit.
- [x] Deterministic v1 initialization and migration are implemented.
- [x] Bounded general v1 cross-record and privacy diagnostics are merged; the reusable 80-test publication conformance pack passes; broader private/runtime pilots remain with their owning issues.

**Current evidence:**

- Issue #1 tracks the knowledge contract.
- Seven v0 schemas, dependency-free validation, and valid/invalid contract tests provide a baseline for v1 stabilization.
- Issue #9 adds nine JSON Schema 2020-12 v1 contracts, a canonical ontology, executable golden/adversarial fixtures, and a non-destructive v0 → v1 compatibility specification.
- Issue #7 adds deterministic initialization plus digest-bound, atomic, rollback-safe v0 → v1 migration.
- The v0 runtime remains supported while issue #10 adds hardened v1 validation around the implemented lifecycle operations.

<!-- roadmap-step
id: MIG-Q04
status: active
depends_on: [MIG-Q03]
issues: [11, 12, 13, 14, 15, 29, 31, 45]
-->
#### MIG-Q04 — Build adapters, index, and context packs

**State:** `active`
**Depends on:** `MIG-Q03`

**Outcome:** Captured records become searchable and can yield bounded context packs through stable interfaces.

**Exit criteria:**

- [ ] At least one Mindcap fixture indexes deterministically.
- [ ] Context packs record selection and redaction provenance.
- [x] A bounded current-profile synthetic archive produces reviewed knowledge,
  exact-source search and context, surviving vault relocation and clean rebuild.

**Current evidence:**

- The extracted v0 engine implements supplied-file ingestion, hash-bound provenance, deterministic lexical indexing, explainable search, and bounded context packs.
- Merged #57–#64 add normalized-source adapters, authored curation, bounded
  v3.2.2/v3.2.3 archive interpretation, private routing, scoped retrieval and vault
  recovery. [Exact commands and limits](docs/private-garden-evidence.md) distinguish
  the implemented checkpoint from full Mindcap producer/legacy compatibility,
  media selection, redaction and parent conformance still open.

<!-- roadmap-step
id: MIG-Q05
status: active
depends_on: [MIG-Q04]
issues: [2, 16, 17, 18]
-->
#### MIG-Q05 — Publish privacy-safe projections

**State:** `active`
**Depends on:** `MIG-Q04`

**Outcome:** Issue #2 produces an opt-in Pages or Quartz projection that cannot expose private records by default.

**Exit criteria:**

- [ ] Publication requires explicit inclusion and passes leak fixtures.
- [ ] A green workflow builds and deploys the public projection.

**Current evidence:**

- Issue #2 tracks projections.
- The v0 reviewed-public projector and immutable Quartz adapter are tested with a synthetic consumer fixture.
- Consumer deployment workflows and an organization-level garden route remain unimplemented.
- B1 implements #16's local versioned descriptor, reviewed-public artifacts and
  supplied synthetic catalog, merged through #66 after #65. See the
  [contract and reproducer](docs/federation.md). A local build does not establish
  consumer deployment, organization adoption or full federation acceptance.

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
- **Merged local checkpoint:** General v1 validation, local source adapters, reviewed retrieval/context, authored curation, candidate routing, scope enforcement and bounded filesystem recovery have synthetic local evidence.
- **Proposed/deferred:** Architecture ratification, full archive/document/media acceptance, released packaging, consumer publication and federation remain separate gates.
- **Open question:** Which consumption format should Empathy pin first: a release archive, package, or immutable source checkout?

## Portable private-garden checkpoint sequence

This user-selected milestone advances bounded parts of #42, #10, #11, #12, #13,
#15, #14, #29, #31 and #45. It does not replace parent acceptance criteria.
[The checkpoint specification](docs/private-garden-milestone.md) records the
proposed dependency corrections and [CONTINUITY.md](CONTINUITY.md) records live
implementation, PR stack, verification, blockers and the exact next action.

Order: architecture/ownership proposal; general v1 validation; scope and explicit
local bindings; source-reference/filesystem foundation; text adapter; reviewed
retrieval/context; authored curation; current archive profiles; routing; complete
scoped retrieval; vault recovery and clean offline end-to-end proof.

#29 supplies a prerequisite contract earlier than its original position. #45
splits its early source-storage contract from its final relocation proof. #30
contributes only explicit safe local bindings; full registry composition and #35
PDF/media ingestion remain integration work. #41 historical backfill and hosted
product/publication work do not become blanket blockers for existing v1 work.

SQLite #32, web/API productization, provider integrations and broader compaction
remain deferred. The next B1 checkpoint covers local public federation contracts;
full federation/consumer acceptance remains open. Retention policy is considered
early without authorizing destructive operations. New ADRs stay proposed and all partial PRs use Refs.

The [finite evidence report](docs/private-garden-evidence.md) links the synthetic
archive, reviewed prompt entry, exact source retrieval, bounded context and vault
relocation/restore proof. This supports #20 without marking its real legacy archive,
Empathy, publication, federation or final consumer acceptance criteria complete.


## Proposed architecture disposition and conditional follow-ups

[The #42 map](docs/target-architecture.md) links focused ADRs for all ten required
topics, canonical/generated/control ownership, every named repository/runtime
owner, independent bookmark approvals and deferred choices. ADR-0007–0021 remain
proposed/null approval. #41's legacy authority migration and human/cross-owner
disposition remain gates on consequential broader product choices under #40.

The proposed order is: dispose the relevant decisions; deliver #46's bounded
non-destructive contracts/proof; then #32 scoped adapter parity after its store
decision, #37 dependency manifests and selected downstream outputs, and #47's
minimal shared CLI/API/web slice after its audience/auth/runtime decisions.
#48 retains actual capture/intake contracts and independent private/public
approvals. #20/#19 retain consumer/release acceptance. Optional experiments are
not blanket gates. No framework, new store, worker, provider or topology is
implemented under #42. Deferred choices trigger evidence review by 2027-01-01 or
earlier stated events, never automatic adoption.

## Private policy and storage continuation — merged checkpoints

The authorized #29 → #31 → #30 → #35 → #45 follow-ups are recorded in the
[private-storage sprint](docs/private-storage-sprint.md). They extend the merged
#74–#79 stack with local policy decisions, output enforcement, reversible cache
recovery, optional ordinary PDF extraction, private assets and mixed-vault proofs.
The [coverage ledger](docs/open-issue-coverage.md) retains every parent criterion.
Hygiene/Realm policy and confidential-runtime contracts, native platforms, remote
providers, approved copy and destructive/timed retention are explicit remaining
gates. Review/merge of drafts is distinct from owner ADR or consumer acceptance.

The bounded [native macOS registry follow-up](docs/registry-native-platforms.md)
is implemented in merged #93: extended ACL and exact ownership-path checks,
44 tests per native Python job and clean installed-wheel evidence pass on
macOS 15.8.2/arm64. Windows/confidential-host gaps remain explicit. This extends
the merged checkpoints without repeating #80–#84; native tests and merge do not
imply wider-host acceptance or ADR ratification.

## Provider and release verification

The current authorized batch is [provider, consumer and release checkpoints](docs/release-checkpoints.md):
#51 local provider recovery, parked #27 release preparation and #20 synthetic/approved-private
consumer proof. The maintainer explicitly deferred #19 (ordinal 21) and additional
release work pending organization release conventions. [Consumer composition](docs/consumer-journey.md)
and Empathy draft #120 retain actual cutover/private-pilot gaps.

## Broader product checkpoints

The merged batch covers [the eight product checkpoints](docs/product-checkpoints.md):
#41, #43, #44, #32, #37, #49, #48 and #47. Verify shared
gates before ADR backfill and the framework-dependent web slice. Reuse Relay for
Decisions; keep query stores and all generated views replaceable. Implement ready
local projection, dependency-build, memory and bookmark contracts through bounded
checkpoints. The overnight continuation closes #49 and extends #37/#48 without
inventing owner acceptance. [The #47 service/parity proposal](docs/shared-service-slice-proposal.md)
preserves the accepted-ADR gate. Deferred #86–#91 are not activated.

## Deferred after the current queue and reconciliation

The maintainer authorized filing #86–#91, grouped as native sub-issues under
[#86](https://github.com/egohygiene/mindgarden/issues/86). They remain deferred
until the original 38-issue queue is completed/dispositioned and its final
reconciliation/refactor is finished, followed by explicit later scheduling.
See [the proposed sub-issue roadmap](docs/deferred-context-package-roadmap.md).

The proposed sequence is source/location integration (#87), data-only packages
and semantic/provenance evaluation (#88/#91), optional scoped AI research (#89),
and a synthetic analysis-to-reviewed-packet composition (#90). Actual dependencies
and independent fixtures are documented there. Existing #13/#46/#49 already own
AI curation, refreshed summaries and memory views; do not duplicate or delay those
current requirements. No new feature, provider or ADR is adopted by this capture.

## Learning and optional evaluations

The maintainer selected [#28 → #21 → #26 → #33 → #34](docs/learning-evaluation-checkpoints.md)
for the next batch. Learning and infographic candidate contracts can advance as
file/CLI projections without full web/runtime or release adoption. Evaluations
remain optional, exact-version experiments over synthetic fixtures and the
reference/SQLite baseline. Results are recommendations for review; source/privacy,
canonical ownership and ADR gates remain unchanged. The later sleep-session
authorization permits qualified merges: #28/#26/#33 are now closed, while
#21 and native #34 retain explicit unmet criteria.

## Authorized original-roadmap closeout

The maintainer authorized merging #93–#109 and bounded follow-through for
#43 → #46 → #17 → #18 → #20. See [the closeout ledger](docs/closeout-sprint.md).
One separately requested [optional TypeSafe decision seam](docs/typesafe-decisions.md)
can proceed independently of web/runtime and private-pilot gates. It does not
activate deferred #86–#91 or release work. That batch is merged; the later
sleep-session authorization permits tested bounded checkpoints to merge after CI.

## Authorized pipeline completion sprint

The maintainer selected #11–#16 and necessary dependencies. Execute the bounded
checkpoints as #11 → #15 → #13 → #14 → #12 → #16. This corrects the presentation
order: the existing authored #13 curation contract already satisfies #15 parsing,
while the new v2 fixtures support the later optional producer proof. #14 can use
existing #12 retrieval before the new performance matrix. The Mindcap captured
source contract is a pinned proposed owner draft, not an accepted shared policy.

[Merged #113–#118](docs/pipeline-completion-sprint.md) add capture conformance,
v2.0.0–2.0.2 source profiles, optional evidence-bound extraction/resumption,
reviewed graph moves/splits/replacements, typed projection coverage and measured
2048-note operation, and local private/internal discovery/selected reads. A
[combined source/installed proof](docs/pipeline-completion-proof.md) links evidence
to #20 without completing private-pilot, publication or Empathy acceptance.

The supported Python/v0 workflow, original sources, private fallback and canonical
record ownership remain. Models, Google, hosting and query stores are optional.
Source/controller state stays outside tracked gardens. Proposed ADRs, Aether #69,
Akashic #176, confidential runtime, real consumer acceptance and unselected parent
scope retain their gates. Deferred #86–#91 and release work remain parked.
