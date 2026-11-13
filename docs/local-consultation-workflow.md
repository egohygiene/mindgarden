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
| 4 | Connect explicitly selected Drive capture and the scoped Codex workflow (#87/#89). | Draft #140 implements capture/refresh, separate normalization and optional private OAuth. `feature/89-scoped-research-pilot` supplies the bounded read-only research CLI and packaged Codex profile. Mocked software proof is separate from live Drive/Codex acceptance. |
| 5 | Prepare and run the selected private pilot where authorized and available. | Metadata-only `pilot preflight` and the concrete operator guide are implemented; the composed synthetic fixture reports ready-to-attempt. Actual execution remains blocked on the unanswered OS/workspace/folder selection, credentials and applicable classification/consumer/runtime authority. |

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

At qualified source `9db4c202ec166a9a887db3d4c834919dff426f0b`, the combined
ledger/schema/scope/source/compaction/memory/extraction selection passes **61 cases
per Python**, zero skips: 3.12 in 157.739s and 3.13 in 154.728s. Automatic Test
43349432329 and preparation 43349432315 pass for that exact head of draft
[#139](https://github.com/egohygiene/mindgarden/pull/139). This includes a
discovered null-pin guard before any source body access. A batch source resolver prechecks every exact grant,
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

## #87 selected capture and refresh checkpoint

Draft [#140](https://github.com/egohygiene/mindgarden/pull/140), functional source
`69a5999e0be2c74951c79bdeb979909544442c15`, stacks on #139.
[The Drive guide](drive-capture.md) describes the current official v3 contract,
private optional OAuth setup and the separate captured-package adapter. Capture
requires controlled-import scope and an explicit reviewed operation/network flag;
normalization inherits the garden's stronger offline policy. An offline capture
is denied before provider access. Exact provider IDs/versions and verified bytes
survive rename, unchanged replay and partial recovery without deleting old evidence.

The focused Drive/credential/schema/scope/source selection passes **38 cases per
Python**, zero skips: 3.12 in 16.349s and 3.13 in 15.824s. The full synthetic Drive
journey matches its complete golden: two retained snapshots, eight reused evidence
rows, 13 immutable objects, a 6,129-byte context and exact report/evidence after
relocation/restore/clean rebuild. The original CSV golden remains a separate
qualification target. The optional official OAuth SDK 1.5.0 constructor was
checked offline; no consent/account or live provider request was performed.

This is selected My Drive capture of supported text/declared CSV. Native exports
have explicit losses; PDF/images are preserved-only. OAuth read-only permission
is account-wide while the application narrows actual reads. Capture refresh does
not silently approve/retire knowledge or assert that a packet is the latest/full
account history. Live Drive, Windows credential mutation, confidential assurance,
broader freshness and the actual private pilot remain separate acceptance.

## #89 bounded caller research and pilot preparation

The [research contract](scoped-research.md) composes the existing selected local
read handlers and exact reviewed/source-granted evidence. All steps, tool choices
and source grants are checked before any body; cumulative budgets, exact revisions,
request changes, expiry and revocation gate every step and final output. No model,
executable planner, write handler or persisted trace/cache is introduced. Caller
interpretations stay separate from observations and never approve knowledge.

Two distinguishable synthetic caller plans, provider removal/direct search and
all seven read tools work without a model. The focused research/pilot/schema/
scope/local-federation selection passes **37 cases per Python**, zero skips:
3.12 in 41.487s and 3.13 in 40.138s. Final clean artifacts follow qualification.
The composed `research_demo.py` golden reuses the entire Drive/packet/recovery
proof, exercises the ordinary CLI with all three clients and performs metadata-only
local pilot preflight. The [packaged Codex profile](../profiles/agent/codex.md)
requires actual caller/runtime authority; local offline reads do not authorize
forwarding private context to a hosted model. Actual Codex/model execution and
semantic-quality evaluation remain unperformed.

The [private-pilot guide](private-pilot.md) supplies initialization, existing local
bindings/sessions, optional OAuth/capture, separate import/review, packets, assistant
authority and non-destructive recovery steps. Preflight opens no original, network
or model, changes no file and reports cached credentials separately from live
authentication. It cannot certify unseen classification, integrity or completeness.
The actual private pilot has not run because the required user-specific setup is
unavailable; no parent issue, legal/financial conclusion or confidential assurance
is claimed. Initial fixture attempts used a nonexistent adapter ID and invalid empty
session fields; corrected tests retain the real contracts rather than weakening them.

Combined artifact qualification found that the source manifest omitted the new
CSV fixture extension: unpacked-source execution failed before import. #141
includes the manifest correction and explicit three-file distribution assertions.
The earlier source/wheel observations remain separate; only the corrected source
archive can satisfy the composed clean-artifact checkpoint. Packaging/release
guidance, declaration, changelog and pinned owner inventory were read before this
change; version, publication workflow and release policy are unchanged.
