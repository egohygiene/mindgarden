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
