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
merged or parent issue closed by this audit; all 24 ADRs stay proposed.
