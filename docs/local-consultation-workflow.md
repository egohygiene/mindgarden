# Local source-to-reviewed-packet workflow

The maintainer selected these five steps on 2026-11-13. This changes the earlier
end-of-original-queue scheduling gate for bounded work under #86/#87/#89/#90.
It does not ratify proposed ADRs, authorize unspecified private inputs or replace
the remaining acceptance of those parents. #88/#91 and release #19/#27 stay
deferred. The [44-row coverage ledger](open-issue-coverage.md) retains the original
issue dispositions; no parent is closed by changing the schedule.

## Delivery order and dependency corrections

| Step | Selected checkpoint | Status and next action |
| --- | --- | --- |
| 1 | Review and merge #133 → #134 → #135 → #136 → #137. | Completed: #133–#137 merged in order at main `9c94245`. Every selected head has passing Test/preparation; #134 reconciled normally with identical source tree and a passing new preview. See the merge receipt below. |
| 2 | Activate the bounded local phase under #86. | Selected #87/#89/#90 scheduling is updated; #88/#91 remain deferred. This document maps existing owners rather than adding a competing garden or session model. |
| 3 | Produce a synthetic, reviewed, source-backed preparation packet (#90). | Implemented on `feature/90-reviewed-ledger-packet`: strict CSV normalization, pinned source grants, explicit reconciliation/review and exact-decimal calculations. The source demonstration passes; clean artifact qualification follows. |
| 4 | Connect explicitly selected Drive capture and the scoped Codex workflow (#87/#89). | Verify current official provider contracts. Reuse normalization, source storage, review and retrieval services. Codex can use the existing CLI; a private web app, MCP server, second model and new query database are not prerequisites. |
| 5 | Prepare and run the selected private pilot where authorized and available. | Build a concrete preflight/runner and operator guide first. The actual OS, private workspace, selected Drive folders, credentials and classification/runtime evidence must be supplied outside public fixtures before real execution. |

The synthetic packet is independent of Drive: acquisition supplies captured
artifacts to the existing adapter boundary. Existing #13 authored/extraction
proposals and #46 compaction contracts are available inputs, not prerequisites
that require finishing their every remaining integration. Scope and publication
contracts still apply. A polished private browser application remains #47 and
requires its actual architecture/runtime decisions; the initial workflow uses
the CLI, local files and an explicitly configured agent.

## Reuse and ownership

| Concern | Existing owner | Bounded extension |
| --- | --- | --- |
| Captured source, normalization and evidence | #11, #15, #35 and #45 | Source adapters consume supplied bytes; provider acquisition is separate. Exact originals and evidence survive relocation. Restricted processing is not enabled by an ordinary filesystem flag. |
| Interpretation and review | #13, #29 and #31 | Proposed classifications/interpretations stay distinguishable from observations. Existing explicit human review and fresh plan digests gate application and selected export. |
| Calculations | #90 | Explicitly declared ledger fields and exact decimal arithmetic; no inferred balances, invented amounts or silent transfer/duplicate resolution. |
| Search/context and agent use | #12, #16, #31, #47 and #89 | Existing scoped services and CLI enforce authority before reads, ranking, traversal and output. Source instructions never become commands. |
| Refresh and recovery | #37, #46 and #45 | Captured revisions invalidate affected inputs/approvals. Original and previous output revisions remain retained and traceable. |

## Verification and privacy boundary

Public fixtures contain two synthetic accounts, overlapping exports, an explicitly
reviewed transfer ambiguity and a correction. Tests must cover malformed inputs,
stale approvals, exact source spans, unavailable/denied inputs, budgets, interrupted
operations, duplicate-safe replay and clean rebuild/relocation. Mocked provider
tests are software evidence, not proof of live Drive or model accuracy.

Private garden records, originals, reports, review configuration and credentials
belong outside this public software repository. A selected report remains private
unless an independent export policy permits another destination. Financial
transactions demonstrate movement, not current assets/liabilities or completeness
of account history. The packet states observed versus declared coverage, reviewed
categories, unresolved questions and separately supplied evidence.

The PDF/document path currently refuses restricted inputs without actual
confidential-runtime assurance; see [the document contract](document-ingestion.md).
That requirement is preserved. A private pilot must report missing contracts and
configuration explicitly, not relabel data or manufacture approval. A synthetic
packet does not complete #20's real legacy archive/Empathy/publication journey.

## Checkpoint log

The activation checkpoint changes scheduling and documentation only. Runtime,
schemas, v0 behavior and all proposed/null-approval ADRs are unchanged. Existing
source/wheel, browser and recovery evidence remains in [the journey ledger](journey-sprint.md).
Each implementation PR will append its actual commits, commands, results,
remaining criteria and next action here and update CONTINUITY.md.

## Ordered merge and activation receipt

[#138](https://github.com/egohygiene/mindgarden/pull/138) preserves the bounded activation and owner map. Its branch is `docs/86-local-workflow-activation`, reconciled normally onto main `9c94245`; initial documentation commit `e77a395` is retained. [The machine-readable merge receipt](evidence/consultation-merge-receipt.json) records each expected head, merge and automatic passing run. Main is byte-equivalent to the qualified #137 combined tree (`git diff --exit-code 0697145 origin/main`). #134 failed preview 43284993775 remains historical evidence; normal main reconciliation `0a6a387` preserved its exact prior tree and new preview 43345132986, Test 43345132543 and preparation 43345132522 pass. Nothing was manually dispatched or weakened. No new implementation draft is authorized for automatic merge by this receipt.

## #90 declared ledger and private packet checkpoint

The [packet contract and commands](consultation-packets.md) reuse source adapters,
exact offline source grants, private scope/review and generated-file ownership.
Three versioned schemas describe normalized rows, reviewed requests and packets;
the official positive-fixture/schema inventory is updated. Eight unique synthetic
transactions across three overlapping exports produce independently expected
USD net movement **2259.76**; transfer pairs, unclassified movement, missing account
and declared coverage gaps remain explicit. A new ordinary `packet` command
previews the computed report and binds reviewed application to exact inputs.

Fifteen focused ledger/packet cases pass (Python 3.12, 63.497s), including a
discovered null-pin guard before any source body access. The preceding combined
60-case source/schema/scope/compaction/memory/extraction selection passes both
Pythons (153.156s / 147.059s); final-source combined qualification is repeated
after that null-pin hardening. A batch source resolver prechecks every exact grant,
uses one fresh verified snapshot per plan, and checks live authority for each
row/output. No cache crosses plan/session boundaries. Existing single-source
evidence bytes and authority semantics are retained.

The source proof imports through ordinary CLI/services, applies a separately
authored reviewed summary, retrieves exact source evidence and produces a
**6,128-byte** context. Eleven immutable source objects and all original CSVs are
retained. Relocation, restore and a clean garden reproduce the packet, index,
context and evidence exactly with network/HTTP/process/model entry points blocked.
The [complete golden](../tests/fixtures/consultation/expected-proof.json) preserves
all output evidence. Installed wheel/source qualification is still pending here.

Initial attempts found a nested attachment filename incompatible with the shared
flat writer, a test budget whose own changed field affected its size, and a
mutated test baseline. These were corrected; they are not passing evidence.
The complete request ceiling now covers ownership metadata as well as report,
review and selected normalized evidence. No raw statement/PDF export, live Drive,
model-quality evidence, actual private pilot or parent completion is claimed.
