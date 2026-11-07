# Learning and optional-system evaluation checkpoints

The maintainer selected #28 → #21 → #26 → #33 → #34 for an overnight batch,
then a morning sync. This is implementation/evaluation authority for bounded
reviewable drafts, not merge, publication, release or ADR-ratification authority.
The combined checkout extends draft #104 (`0d436f49af1a8593676f7c77451c93dbc34b543f`)
and preserves #93–#104. Main remains `d5edb13`; all 44 issues remain open.

## Dependency reconciliation before implementation

- #28 authored candidate, private review history, deterministic exports and
  replaceable scheduling use the existing #12/#13/#31 services. Full #17 web
  adoption and Realm #20 runtime are later integration proofs. A static accessible
  study document is a disposable adapter, not a new web application framework.
- #21 says post-1.0 and lists #19. The maintainer explicitly selected its bounded
  candidate work now while deferring releases. Treat that as a scheduling change
  for the producer schema/fixture/export checkpoint. Publishing, downstream
  consumer acceptance and release acceptance remain separate; do not silently
  reinterpret the release gate as complete.
- #26 is an architectural evaluation, independent of deploying OpenAleph.
  Inspect exact official source/release/license and distinguish useful patterns
  from dependency or service adoption. No real data or production service.
- #33/#34 follow the available optional #32 port/reference/SQLite checkpoint.
  #26 supplies evaluation framing, not a new mandatory service. Realm #25 and
  Aether capability work remain gates for confidential/runtime/agent assurance;
  an ordinary offline synthetic experiment cannot satisfy those contracts.
- #46 retention separates originals, canonical knowledge, learning/memory views
  and publication. Review history is private. No source deletion or knowledge
  promotion follows from grading, compaction or generated artifacts.

These corrections are recorded for review. Existing proposed ADRs remain
proposed; the evaluations may recommend adapt/defer/reject without adopting any
new default store, framework, model provider or product.

## Checkpoint ledger

| Issue | Branch / PR and implemented checkpoint | Verification | Remaining / exact next action |
| --- | --- | --- | --- |
| #28 | [draft #105](https://github.com/egohygiene/mindgarden/pull/105), `3510b22`, over #104; authored cards/summaries/private grading/versioned schedules/export round trip | 12 focused tests on Python 3.12/3.13 + 5 schema tests; Chromium static accessibility proof | Authored cards/summaries, exact provenance, private events, schedule versions and export round trip; full hosted UI remains separate |
| #21 | [draft #106](https://github.com/egohygiene/mindgarden/pull/106), `4e12dcd`, over #105; public reviewed candidates/series, rights, duplicates and artifact-feedback projections | 9 focused tests on Python 3.12/3.13 + 5 schema cases | Reviewed renderer-independent insight/series candidates, public-safe provenance, duplicate/lifecycle/privacy fixtures; no rendering or posting |
| #26 | Planned evaluation draft | Pending | Pin OpenAleph evidence; architectural/privacy/license/cost matrix and removable synthetic export experiment |
| #33 | Planned optional CozoDB experiment | Pending | Exact native version/adapter, multi-garden parity, resource/recovery/exit proof; no canonical store change |
| #34 | Planned optional OpenViking experiment | Pending | Exact version/license, synthetic provenance adapter, network/model/storage behavior, baseline comparison or explicit blockers and removal |

## Existing gates retained

Draft #104's exact-head engine Test 42314280753 and release-preparation check
42314280811 pass. Decisions preview 42314281186 fails; its earlier native
source-validation finding remains #43's gate. #41 historical migration and #47
full framework/runtime work remain gated. Real #20 pilot/consumer cutover,
restricted runtime assurance and #48 external handoffs remain unverified.
Release #19, further release work and deferred #86–#91 are not activated.

The exact next action is #26 pinned OpenAleph architectural evaluation. Every
checkpoint will record source/PR, commands/results, supported interfaces, genuine
blockers and the following action. Leave all new drafts for the morning sync.
