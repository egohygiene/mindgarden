# Repository audit and source-to-packet follow-through

The maintainer parked Mac setup and authorized repository work on 2026-11-13.
This audit refreshed all 34 open issues, #5/#40 and the selected issue comments,
the open documentation PR #148, main `270ced6`, architecture and proposed ADRs.
No real account, financial input, credential or model is needed for this batch.

## Selected bounded work

| Order | Existing owner | Observed gap | Checkpoint |
| --- | --- | --- | --- |
| 1 | #37/#90 | `packet --check` recomputes the selected request but lacks a concise old/current dependency comparison. | Add private dependency metadata and read-only reconciliation over explicit current authorized evidence. Corrections and source metadata changes stale the packet; unknown evidence blocks reuse; unrelated inputs remain current. |
| 2 | #87/#90 | Drive capture normalization selects strict `ledger-csv` for every CSV. The separate reviewed mapping adapter cannot yet be selected per provider file. | Compose explicit reviewed per-file mapping configuration with captured-byte verification, digest-bound import and ordinary packet/recovery services. |
| 3 | #15/#16/#32/#43/#44 | Coverage text mixes listed criteria with optional follow-ups. | Audit actual issue criteria against source/tests and record the exact unmet contracts before adding implementation or claiming closure. |

These reuse source, scope, review and adapter boundaries. They do not require
broader application decisions, real Drive consent, the approved private pilot,
release work or optional model/database adoption. #37/#46's required private
pilot and #20's actual archive/Empathy proof remain distinct later evidence.

## Dependency corrections and limits

The full #32 issue body explicitly includes incremental refresh and migration in
its adapter boundary. The preceding setup plan's checkbox-only interpretation
was too narrow. Unsupported capability declarations are truthful current state,
not proof that those remaining requirements have been implemented. A permanent
database choice remains optional; this does not block the source/packet batch.

Packet currentness is defined over explicitly supplied current reviewed inputs.
Ambient newly imported/ungranted sources are not silently selected, inspected or
treated as replacements. A local reconciliation is independent from a live
Drive/model proof. Source review, normalization review, transaction classification,
knowledge approval, runtime authority and publication remain separate.

The existing #90 explicitly requests a synthetic fixture. Richer formats,
account balances, a dashboard/PDF renderer and real financial acceptance are not
new criteria of that synthetic issue. No duplicate setup issue is needed;
#86/#87/#89 already own local setup and the actual operator workflow.

## Review stack and recovery

Base documentation PR #148 records the merged #144–#147 stack. The first new
branch is `feature/90-packet-freshness`, based on its exact `136c663` head; code
PRs remain drafts and depend explicitly on the unmerged documentation baseline.
The original four interrupted root entries and every existing worktree remain
untouched. The final child branch will be the reproducible combined checkout.

Verification, exact heads, PR links, remaining criteria and the next action are
recorded below and in `CONTINUITY.md` at each bounded checkpoint. No new PR is
merged or parent issue closed by this audit; the 18 indexed ADRs stay proposed/null approval and six legacy Accepted labels remain unchanged.

## Packet-currentness checkpoint

A further audit found `packet --check` delegated to the applying helper and
therefore rejected unchanged files after a session renewal. The new read-only
`verify_generated` checks the retained inventory against recomputed current
authorized bytes without adopting the marker's old authority or modifying any
file. Three focused verification/compatibility regressions pass on Python 3.12
in 78.488s; final combined qualification follows this implementation correction.

[Draft #149](https://github.com/egohygiene/mindgarden/pull/149) on #148 pins functional source `2373b77e43d43776bfbd128e9fca1501d4024816`. Python 3.12's broader packet/mapping/schema/package selection passes 44 cases in 325.556s; Python 3.13's focused currentness/schema selection passes 16 in 231.205s, zero skips. Scoped lint/format, pinned owner/continuity/coverage/native-child and whitespace checks pass. An initial test referenced a nonexistent helper; corrected to the actual vault object-path method before these successful runs. Exact-head CI and the combined artifacts remain separate.

The next implementation is the child `feature/87-reviewed-drive-normalization`. Its initial occurrence assertion confused the 11 immutable objects with the nine actual CSV row occurrences; the fixture expectation was corrected without weakening normalization. Its current checks and final proof will be reported independently.

## Per-file Drive checkpoint

The child `feature/87-reviewed-drive-normalization` adds the reviewed file-ID mapping contract and explicit import option. [The guide](drive-normalization.md) and committed mapped-source golden document exact original occurrences, two layouts, unchanged replay, correction, partial/missing-input behavior and clean packet/index/context recovery. Initial 44-case local checks pass; the corrected whole stack is qualified separately below.

## Acceptance and public-metadata checkpoint

The child `test/15-16-acceptance-audit` on #150 fixes reproduced historical-only catalog identifiers/ambiguity affecting new public refresh output. Comparison now considers only currently verified gardens; unavailable sources retain generic diagnostics and no old IDs. The known continuation artifact gains explicit exact-byte/unreviewed/no-execution proof. [The full acceptance audit](remaining-acceptance-audit.md) records five parents, real remaining gates and the next independent sprint. No broad parent is closed or new issue created.

## Final qualified handoff

[Draft #149](https://github.com/egohygiene/mindgarden/pull/149) → [#150](https://github.com/egohygiene/mindgarden/pull/150) → [#151](https://github.com/egohygiene/mindgarden/pull/151) stack on #148. Combined source `b35b597ca3a798ed4bf171244100a282151865f8` passes **184 targeted cases per Python**, zero skips (3.12 wall 590.908s / 3.13 570.121s). Each clean Git, isolated wheel and unpacked source form passes all eight selected boundaries and three complete golden proofs; all 100 imported engine module origins match that form. All nine proof reports match; the installed wheel contains only Mindgarden.

Eight isolated installed v0 commands, two distribution cases per Python, compilation on both, twelve-file formatting and pinned owner/continuity/44-row/native-child checks pass. Eighteen changed Python files introduce no lint findings; one inherited finding remains. All three functional heads pass automatic Test/preparation, including #151 direct Test run 43642186673. Final handoff changes docs only and its CI remains separate. [Exact commands, results, artifact/report hashes, runner sources, corrected initial attempts and limitations](evidence/repository-audit-qualification.json).

The audit counts **18 indexed proposals with null approval** and **six legacy inline Accepted labels**, preserving both. Earlier all-24-proposals wording is corrected without ratification or historical migration. Main remains `270ced6`, all 34 issues stay open and all 44 coverage rows remain; no duplicate issue, merge, release or real processing. [The next independent sprint](remaining-acceptance-audit.md#proposed-next-independent-sprint) prioritizes acceptance reconciliation, #15 delivery/bootstrap proof, #32 incremental/migration work and bounded #44 public relationships. Review the stack before changing main; Mac setup stays parked.
