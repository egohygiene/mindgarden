# Original-roadmap closeout sprint

The maintainer authorized merging the existing #93–#109 stack and starting the
remaining #43 → #46 → #17 → #18 → #20 checkpoints. They also explicitly selected
one bounded optional Jev/TypeSafe decision integration. New work stays in small
reviewable drafts. Release #19, publication, architecture self-ratification and
unapproved real private pilots remain outside this execution.

## Dependency corrections and current checkpoints

| Work | Contract / checkpoint | Current evidence / next action |
| --- | --- | --- |
| Existing PR stack | Merge in dependency order with exact expected heads; do not bypass a genuine failing validator | All #93–#109 merged into main `f3a88cc`; [exact receipt](merged-closeout-checkpoints.md). New drafts remain separate. |
| #43 Decisions | Native validator and shared renderer remain owner implementations | Rust 1.85.1 and exact Relay/EgoLint/Hygiene/Observatory runtime prepared locally. Three ADRs lacked required body sections; all status/approval fields remain proposed/null. Unmodified native collector reports ready on merged main; repaired #97 hosted preview and Test jobs passed, preserving unknown roadmap/history warnings |
| TypeSafe first pass | New explicit authority for a narrow read-intent seam; no research agent or full web/runtime adoption | [Draft #110](https://github.com/egohygiene/mindgarden/pull/110), based on main; [optional provider/checkpoint](typesafe-decisions.md); typed Choice + applicability Noul, static authorized read handlers, disabled/unconfigured behavior and labeled fixtures; live key unavailable |
| #46 Compaction | First raw-only source access must extend existing session/source contracts; derived persistence/expiry grants no source deletion | [Draft #111](https://github.com/egohygiene/mindgarden/pull/111), functional `3bdbdc7`, on `feature/46-source-compaction` over #110: exact private source grants, authored first summary, immutable private bundle plan/apply/check, TTL/revocation and partial recovery. Tests: 22 focused Python 3.12, 10 new cases Python 3.13; full combined suite follows. Private pilot/destructive retention remain open. |
| #17 Public garden | Reuse current pinned Quartz adapter and tokens; no framework replacement | Actual 0/3/205-note/claim output qualified; keyboard activation, theme contrast, mobile/reflow and bounded graph fallbacks corrected. [Evidence](rendered-closeout-evidence.md) retains the external mobile Explorer critical ARIA finding; full accessibility/performance acceptance remains open. |
| #18 Portal | Mindgarden owns output/composition, Relay owns shared action and consumers own hosting | Actual 60-file artifact composes/retries/checks beside three sibling surfaces and rejects damaged candidates. Relay #40 remains open with no action at the inspected pin; no host promotion/deployment. |
| #20 Consumer | Reuse the proved synthetic journey and external package boundary | Empathy #120 refreshed at `6d6630c`; fresh installed merged engine and staged entrypoint regeneration pass, 12 consumer tests pass. Canonical entrypoint acceptance, required holistic run, shared action, deployment and approved private pilot remain open. |

The TypeSafe checkpoint is independent of #43's renderer and #46's source-access
contract. Its SDK is optional and receives only explicitly supplied request text,
not protected source content. This does not activate deferred #86–#91. #42 human
disposition and #41/#47 architecture/runtime gates still apply to their full scope.

## Verification and handoff

Exact branches/PRs, commits, commands, outcomes and blockers are updated at each
bounded checkpoint in this ledger, CONTINUITY.md and the 44-row issue coverage.
Tests with mocks demonstrate software behavior, not model accuracy. Native shared
validation, hosted CI and local engine tests remain distinct evidence. No manual
paid workflow is launched.

## Review stack

- [#110](https://github.com/egohygiene/mindgarden/pull/110): `feature/typesafe-read-workflow`, functional `284dc63`, merge/verification receipt `3ac1edd`, base `main`.
- [#111](https://github.com/egohygiene/mindgarden/pull/111): `feature/46-source-compaction`, functional `3bdbdc7`, schema/vault guard correction `55393de`, base #110.
- [#112](https://github.com/egohygiene/mindgarden/pull/112): `feature/17-rendered-portal-proof`, functional `2b800f516296abb3116a317f9a149a1e1ca81d45`, base #111. This tip is the reproducible combined checkout.
- [Empathy #120](https://github.com/egohygiene/empathy/pull/120): independent public consumer draft, `6d6630c`, pins already merged Mindgarden `f3a88cc`; accepted cutover/full-profile/deployment remain open.

The first full local 403-test run found the omitted new schema inventory
and the expected downstream site-golden revision change. They were corrected;
only generated site hashes changed in inspected goldens. The final frozen-source
qualification records its own exact commands/results below. All new drafts remain
for review, and parent issues retain their listed acceptance gates.

Live issue reconciliation: GitHub #30 closed at 2026-11-08T19:59:56Z. There
are now 43 open issues and 44 tracked coverage rows, retaining closed #30 with
its unsupported platform/assurance scope explicit. It was not reopened.

## Frozen functional verification

Source `2b800f516296abb3116a317f9a149a1e1ca81d45` was checked in a separate
detached worktree with no tracked changes. On Python 3.12 and 3.13:

- `PYTHONPATH=<frozen>/src python -m unittest discover -s tests -q`: 404
  discovered; 402 pass and two distribution-prerequisite skips, in 320.686s and
  303.261s respectively. The frozen build was initially in a separate output
  directory. After placing those exact artifacts in the expected `.cache/dist`,
  `python -m unittest tests.test_distribution -q` passes both cases on each
  Python (0.035s). All 404 cases are therefore verified; the skipped full-run
  cases are not represented as having executed in that run.
- Optional SDK environments: `python -m unittest
  experiments.typesafe.test_sdk_contract -q`, three passes per Python
  (0.214s/0.224s). These test actual SDK serialization with mock HTTP, not accuracy.
- `python -S examples/typesafe_workflow.py`: disabled fallback;
  `python -m experiments.typesafe.evaluate`: 16 labels, zero model cases,
  accuracy null. The key remains unavailable.
- `python -m build --sdist --wheel`; install with `--no-index` into a clean
  environment; `python -I` installed source-only fixture: exact capture/summary,
  private create/check, zero knowledge anchors, unreviewed state and original
  bytes preserved. The committed receipt includes the frozen source and wheel hash.
- Unmodified native Relay collector on the exact frozen commit: ready, publication
  denied. No ADR is ratified or source validator weakened.
- Broad source Ruff E9/F, compilation, diff, owner ADR/continuity schemas and
  live 43-open/44-tracked issue coverage checks pass.

Automatic hosted CI is separate: #110 Test `42521750360` and release-preparation
`42521750359` succeeded. #111 Test `42524095943` subsequently succeeded. #112 Test `42524541261`
was still in progress at the last observation; its release-preparation run
succeeded. Later documentation receipts can trigger their own new runs, so a
passing functional run is not substituted for an unobserved latest-head result.
