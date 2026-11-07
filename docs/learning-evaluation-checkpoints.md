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
| #28 | [draft #105](https://github.com/egohygiene/mindgarden/pull/105), `3510b22`, over #104; authored cards/summaries/private grading/versioned schedules/export round trip | 12 focused tests on Python 3.12/3.13 + 5 schema tests; Chromium static accessibility proof | Full hosted #17 study UI, reminders/sync and runtime assurance; optional automatic proposals; review #105 |
| #21 | [draft #106](https://github.com/egohygiene/mindgarden/pull/106), `4e12dcd`, over #105; public reviewed candidates/series, rights, duplicates and artifact-feedback projections | 9 focused tests on Python 3.12/3.13 + 5 schema cases | Approved private redaction and accepted downstream intake/publication remain open; review #106 |
| #26 | [draft #107](https://github.com/egohygiene/mindgarden/pull/107), `c5b1f52`, over #106; [pinned architecture/privacy/cost/ownership matrix](evaluations/openaleph.md), proposed adapt/defer recommendation | Official 5.3.2 source/license/docs reviewed; native FtM binary probe blocked, not passed | Maintainer disposition; optional native FtM export blocked by PyICU/ICU; no service adoption |
| #33 | [draft #108](https://github.com/egohygiene/mindgarden/pull/108), `7c75d12`, over #107; [native adapter/measurements/recovery/exit](evaluations/cozodb.md), proposed defer adoption | Five native cases; 262-record exact parity; native FTS/HNSW smoke; no-Cozo exit probe | Maintainer disposition, other platforms, actual upgrades, installed restore dispatch and confidential runtime remain open |
| #34 | `experiment/34-openviking-projection` over #108; [producer/native blocked-runtime evaluation](evaluations/openviking.md), proposed adapt/defer | Four producer cases on Python 3.12/3.13; native 0.5.3/SDK 0.1.18 config/model/network/startup observations, explicitly blocked | Native quality/retrieval/memory/backup/upgrade/encrypted-runtime proofs blocked; review proposed defer disposition |

## Existing gates retained

Draft #104's exact-head engine Test 42314280753 and release-preparation check
42314280811 pass. Decisions preview 42314281186 fails; its earlier native
source-validation finding remains #43's gate. #41 historical migration and #47
full framework/runtime work remain gated. Real #20 pilot/consumer cutover,
restricted runtime assurance and #48 external handoffs remain unverified.
Release #19, further release work and deferred #86–#91 are not activated.

The exact next action is final combined validation, then morning maintainer review of #105 → #106 → #107 → #108 → the OpenViking draft. No automatic merge. Every
checkpoint will record source/PR, commands/results, supported interfaces, genuine
blockers and the following action. Leave all new drafts for the morning sync.

## Reproducible validation of the combined stack

`python -S scripts/learning_insight_demo.py --require-source` proves exact
committed learning/insight goldens through CLI preview/apply and learning import.
Run with an isolated installed wheel using `python -I ... --require-installed`
for the packaging proof. Parent/CLI Python sockets are blocked; only temporary
synthetic fixtures are accepted. Optional native experiment commands, limits
and blocked steps are recorded in their linked evaluations. Baseline full-suite
results and exact functional revisions are added after final verification;
unavailable checks must remain explicit.
