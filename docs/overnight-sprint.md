# Overnight acceptance and integration sprint — 2026-11-09

The maintainer authorized merging the existing stack and continuing the remaining
issues while away, including merging completed, tested checkpoints. This does not
authorize release publication, ADR ratification, private-data access or activation
of the deferred #86–#91 cohort. Open each bounded checkpoint as a draft first,
push its evidence, and merge only after local checks and automatic CI succeed.
An unavailable prerequisite leaves the checkpoint draft and the parent open.

## Merged starting point

Mindcap [#42](https://github.com/egohygiene/mindcap/pull/42) merged at
`02d30d6eb19037b3f770aad3a12c598778b5ae22`. Mindgarden #110–#119 merged in
ancestry order with merge commits, preserving all feature heads and the combined
`milestone/pipeline-completion-proof` checkout. Final main is
`2eda2f4785caf9729b2c486b87436fc894c8e685`; its tree is exactly the tested
`e996fb39c91964486d81cebe03d47f259d1866d4` tree.

| PR | Merge commit |
| --- | --- |
| [#110](https://github.com/egohygiene/mindgarden/pull/110) | `4fa8906010ee9d5b777e2ce428f28efaf7f16807` |
| [#111](https://github.com/egohygiene/mindgarden/pull/111) | `5fbb9d2610048462dbede2188888c0c4a531256a` |
| [#112](https://github.com/egohygiene/mindgarden/pull/112) | `a0c83b915e9478753805931603ba8b0697cbcf44` |
| [#113](https://github.com/egohygiene/mindgarden/pull/113) | `7cff15373eb89f171e5d3368c141d50d547f624e` |
| [#114](https://github.com/egohygiene/mindgarden/pull/114) | `b70e6cad752df929f5f9a196aef0860ef4eb3dd2` |
| [#115](https://github.com/egohygiene/mindgarden/pull/115) | `c94a252af86abd1cac5b0df89e7d2a3408acacf2` |
| [#116](https://github.com/egohygiene/mindgarden/pull/116) | `cf7a747ac19a7fd0de2cdd23d51c46c59fb7ea0b` |
| [#117](https://github.com/egohygiene/mindgarden/pull/117) | `fdc5d915120ba82f39368ae77243148e54ee342b` |
| [#118](https://github.com/egohygiene/mindgarden/pull/118) | `ba254cbd0817d5fb9dce491930009227db453a5f` |
| [#119](https://github.com/egohygiene/mindgarden/pull/119) | `2eda2f4785caf9729b2c486b87436fc894c8e685` |

Every exact PR head had successful automatic Test/release-preparation runs and
no submitted reviews or outstanding comments when refreshed before merge. The
maintainer's explicit instruction supplies merge authority. The latest #119
head Test run is [42555925438](https://github.com/egohygiene/mindgarden/actions/runs/42555925438).
Mindcap #42's CI run is [42547007196](https://github.com/egohygiene/mindcap/actions/runs/42547007196).
No workflow was manually dispatched. Merging implementation does not accept a
proposed architecture or promote a producer wire contract to a released version.

The unchanged functional baseline passed **446 tests, zero skips** on Python
3.12.14 and 3.13.5. Source and isolated-wheel offline proofs matched the committed
golden after vault relocation, restore and projection rebuild. Exact commands,
artifact hashes and limitations remain in [the pipeline receipt](pipeline-completion-sprint.md)
and [qualification report](evidence/pipeline-qualification.json).

## Acceptance reconciliation

Audit the current issue text against implementation, rather than carrying forward
older draft labels or adding new acceptance gates. The following existing issue
criteria are satisfied. Closing an evaluation records its bounded result; it does
not adopt a dependency or ratify an ADR.

| Issue / criterion groups in listed order | Evidence | Disposition |
| --- | --- | --- |
| #10: public allowlist, raw/unreviewed exclusion (1–2) | `tests.test_v1_validation`, `tests.test_publish_garden`, `tests.test_publication_conformance` | Supported public and private record rules enforced |
| #10: unsafe paths, hashes/transformations, relationships (3–5) | V1 validation negatives, exact-evidence and scoped-retrieval suites | Deterministic diagnostic codes; incomplete cross-garden validation is not success |
| #10: source instructions, eight leak surfaces, stable diagnostics, reusable suite, negatives (6–10) | [Publication conformance](publication-conformance.md), its committed surface matrix and source/installed runner | Complete listed engine validation criteria; confidential-runtime assurance and future media integrations belong to their owners |
| #11: versioned interface, text adapter, digest-bound plan/apply (1–3) | `tests.test_source_adapters`, `tests.test_adapter_conformance`, `mindgarden.source-adapter/v1`, `mindgarden.change-plan/v1` | Explicit registration; no ambient plugin loading |
| #11: no acquisition/model calls, deduplication, ordered transformations, original identity, negatives, version compatibility (4–9) | Source-adapter/conformance suites and [adapter contract](source-adapters.md) | Old represented evidence stays resolvable |
| #11: custom registration, archive/bookmark consumers, example adapter (September additions) | `tests.test_captured_source`, archive suites, `examples/adapters/reference_capture.py`, [producer receipt](evidence/capture-handoff-proof.json) | Both actual adapters use the same normalization/plan/apply path; capture deltas remain Mindcap work |
| #12: reproducibility, portable output, explainable scores, reviewed default, complete bounded context ledger (1–5) | `tests.test_projection_corpus`, query/context suites, clean source/wheel [combined proof](pipeline-completion-proof.md) | Exact golden bytes; no cache is canonical |
| #12: typed graph, denied/missing endpoints, clean rebuild, measured larger corpus, schemas/goldens (6–10) | `tests.test_projection_selection`, [projection matrix and 2048-note envelope](projection-conformance.md) | All listed projections qualified; interactive latency and wider hardware are future improvements, not added closure gates |
| #51: inventory, unchanged canonical state, recovered project/artifact/decision/correction, exact references (1–4) | `tests.test_provider_continuity`, committed provider inventory and golden | Two distinguishable local adapters |
| #51: denial, limitations, first-adapter loss, equivalent rebuild, report (5–9) | [Recovery procedure](provider-switch-proof.md), `scripts/provider_switch_demo.py` | No live-provider account or identical model wording required by the issue |
| #26: comparison, reusable ideas, canonical boundary, threat model, costs, follow-ons, synthetic-only/no deployment (1–8) | [Pinned OpenAleph comparison](evaluations/openaleph.md) | Evaluation complete: adapt selected patterns, defer service adoption; optional FtM prototype remains blocked and unclaimed |
| #33: pins/adapter/scoped corpus/vectors/compatibility/resources (1–6) | [Pinned CozoDB evaluation](evaluations/cozodb.md), five native adapter cases and committed resource/native probes | Evaluation complete: retain removable experiment, defer adoption |
| #33: backup/restore/corruption/version mismatch/removal, disposition, synthetic data, removable rejection (7–10) | Actual native backup/restore and exit tests; explicit unsupported capabilities and revisit conditions | Other platforms, real cross-release migration and confidential runtime are not claimed; no default dependency |

#34 stays **partial**: producer tests and a documented native startup failure are
useful evidence, but native useful-query/session/lifecycle comparisons are still
missing. #13 retains its actual live extraction-evaluation gap. #20 retains its
approved private pilot and consumer acceptance. #19 remains deliberately parked.

## Dependency-ready sleep queue

These are bounded checkpoints, not promises to close every parent. Reconcile
each issue again at its start. Prefer one reviewable PR for 1–3 related issues.

1. **Acceptance receipt — #10/#11/#12/#26/#33/#51.** Refresh exact evidence,
   run focused regressions, correct roadmap state and close satisfied issues.
2. **#48 — captured bookmark integration.** Consume the merged producer's
   verified bundle in private cleanup, distinguish metadata from page content,
   and prove evidence-backed review with a conversation-derived item. Akashic
   intake/publication and recurring producer deltas stay owner-gated.
3. **#14 — incoming-reference moves and recovery.** Extend the reviewed private
   lifecycle only where current deterministic move semantics need it; preserve
   old provenance and test partial failure. No inferred public destination.
4. **#37 — targeted build execution.** Compose existing dependency plans with
   explicit built-in projection services, reviewed input digests and full
   reconciliation. No daemon, arbitrary executable renderer or private pilot.
5. **#49 — memory refresh/expiry.** Revalidate current source revisions,
   expiration and revocation at local export; memory removal never deletes
   canonical knowledge or claims recall of an already copied snippet.
6. **#28 — daily learning review.** Add a bounded selected due queue and useful
   local review round trip with stale-source checks. Notifications and sync
   remain outside the engine.
7. **#17 — mobile navigation.** Reproduce and fix the pinned Quartz Explorer
   accessibility defect at the owned adapter boundary, then rerun browser checks.
   Full WCAG acceptance and actual hosted publishing remain separate.

Keep optional #32 performance work behind measurements. #46 retention governs
every disposable output now; no destructive pruning is authorized. #41/#42 ADR
ratification, #43 publication, #47 hosted runtime and #20 real private pilot retain
their explicit external/human gates. Blocked work does not serialize independent
local checkpoints. The six deferred context-package issues are not activated.

## Verification and handoff

This section is updated after each checkpoint with exact commands/results, PR,
functional revision, remaining scope and one next action. Local verification and
hosted CI are separate observations. Preserve all 44 coverage rows, including
closed issues; do not erase completed history to make the queue look smaller.


### Checkpoint A — acceptance receipt

Branch: `sprint/overnight-acceptance`; PR recorded after push. No engine bytes
changed from merged main. The receipt closes #10, #11, #12, #26, #33 and #51
through their actual listed criteria; #34 remains partial. Open count is 43 before
this PR merges and 37 after those six automatic closures. All 44 rows remain.

Fresh local checks:

- `.venv/bin/python scripts/publication_conformance.py --require-source --report .cache/overnight/publication-conformance.json` — **80 pass, zero skips**.
- `.cache/python313/bin/python -m unittest tests.test_adapter_conformance tests.test_captured_source tests.test_projection_corpus tests.test_projection_selection tests.test_provider_continuity --verbose` — **27 pass, zero skips**, 32.873s.
- `.cache/evaluations/cozo-python/bin/python -m unittest experiments.cozo.test_adapter --verbose` — **five actual native cases pass**, 10.955s, pinned Cozo 0.7.6.
- `git diff e996fb39c91964486d81cebe03d47f259d1866d4 origin/main --exit-code` — **exact merged-tree equality** before this documentation checkpoint.

Automatic CI for this new head is recorded separately after it completes; the
previous passing head runs are not substituted for it. Next action: merge this
receipt after CI, refresh live closure state, then implement the #48 captured
bookmark checkpoint. No optional library is added to the core.
