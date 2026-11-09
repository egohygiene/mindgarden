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
`milestone/pipeline-completion-proof` checkout. The merged starting main is
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

Branch: `sprint/overnight-acceptance`; [draft #120](https://github.com/egohygiene/mindgarden/pull/120), functional receipt `041190d`. No engine bytes
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


### Checkpoint B — #48 captured bookmark review

Branch: `feature/48-captured-bookmark-review`, [draft #121](https://github.com/egohygiene/mindgarden/pull/121), functional `11439dc`, stacked on acceptance #120 until
it merges. Implements explicit bundle input, exact evidence/observation lineage,
private immutable export, incomplete-capture reporting and reviewed graph proof.
No schema, canonical format, publication authority or runtime dependency changes.
The parent remains open for actual owner intake/publication and recurring deltas.

`python -m unittest tests.test_captured_bookmarks tests.test_bookmarks tests.test_captured_source tests.test_extraction --verbose`
passes **26 cases** on Python 3.12.14 and 3.13.5. The later-observation regression
also passes separately after extending it to changed raw observation bytes.
Focused Ruff E9/F and formatting pass. The actual pinned Mindcap producer check
passes with networking blocked and two distinct synthetic observations; exact
receipt and command are in [the bookmark checkpoint](bookmark-cleanup.md).
New-head automatic CI is recorded separately. Next action: qualify/merge this
bounded checkpoint, then inspect #14 incoming-reference move semantics.


### Checkpoint C — #14 incoming-reference review inventory

Branch: `feature/14-incoming-reference-inventory`, [draft #122](https://github.com/egohygiene/mindgarden/pull/122), functional `559e0e1`, stacked on bookmark #121 until
it merges. The private transition preview now records exact independently
reviewed incoming links requiring separate repair, without changing original
links or their meaning. Inventory is limited to matching ordinary personal
policies and 128 references; it reports no denied counts. Edge/source changes
invalidate the group plan before output. Six new cases plus existing routing
lifecycle/transfer/recovery suites run with **24 cases per supported Python**.

Dependency correction: incoming edge *repair* is a separately reviewed operation,
not an implicit side effect of moving its target. This checkpoint delivers the
inventory needed to author that future operation. It does not hold independent
#37/#49 work behind a new repair contract. No current v1/v2 request schema or
canonical bytes change; #14 remains open for general repair and broader policy
transitions. Next action: qualify/merge this checkpoint, then implement explicit
selected-output dependency builds (#37).

Acceptance #120 merged at `2c4c465ef92000339eceb521f9690c531b0fcdc0` after
[Test 42558542393](https://github.com/egohygiene/mindgarden/actions/runs/42558542393)
and release-preparation 42558542304 succeeded. GitHub confirms #10/#11/#12/#26/
#33/#51 closed; **37 issues remain open**. No feature/evaluation ADR was ratified.


### Checkpoint D — #37 selected-output dependency builds

Branch: `feature/37-selected-projection-builds`, [draft #123](https://github.com/egohygiene/mindgarden/pull/123), functional `cf963e8`, stacked after routing #122.
Repeatable `--select-output` narrows an authored request before renderer calls.
Full reconciliation recovers from missed events; exact selected outputs retain
complete-build fingerprints while unrelated artifacts are not rendered/copied.
The selected plan binds full input configuration and authority, snapshots mutable
caller input, and retains existing digest-bound review/apply/expiry/revocation.

`python -m unittest tests.test_selected_builds tests.test_dependency_builds --verbose`
passes **12 cases, zero skips**, Python 3.12.14 (15.986s) and 3.13.5 (15.580s).
Five new cases cover renderer invocation, missed events, invalid early selection,
CLI digest/replay/source immutability, complete-request binding and revocation.
Focused Ruff, changed-file formatting, pinned owner/continuity and diff checks
pass. No worker, canonical observation migration or private pilot is claimed.
Next action: qualify/merge this bounded checkpoint, then add live-expiring local
assistant-memory bundles (#49) and audit that issue against its actual criteria.


### Checkpoint E — #49 expiring assistant-memory bundles

Branch: `feature/49-expiring-memory-bundles`, [draft #124](https://github.com/egohygiene/mindgarden/pull/124), functional `79fa120`, stacked after selected-build #123.
Optional explicit `--created-at` binds a managed validity receipt; `--check`
revalidates sources, authority, expiry and immutable bytes without creating a
missing bundle or changing old output. Expiry is bounded by the existing #46
retention/session/snippet windows and is checked before source body access.
Legacy unqualified exports remain compatible and are not claimed managed.

The 16-case memory/validity suite passes on Python 3.12.14 (30.200s) and 3.13.5
(25.775s), zero skips. An additional authored one-source refresh case passes on
both: five unaffected snippets and the old bundle remain exact. Nine new cases
cover deterministic managed metadata, strict schema/checksums, expiry/session/
half-life, no-write checks, corruption, denied sources, revocation and vault
separation. Focused Ruff/format, pinned owner/continuity and diff checks pass.
New-head CI is separate. [The acceptance mapping](assistant-memory.md) covers all
#49 deliverables/criteria; this checkpoint closes that local issue after merge.
Provider copying/recall and richer UI are not silently claimed implemented.
Next action: qualify/merge, confirm the new live count, then finish #28's bounded
due-card review view and verify its actual accessible static-web criteria.


### Checkpoint F — #28 bounded due-card review

Branch: `feature/28-due-review-queue`, [draft #125](https://github.com/egohygiene/mindgarden/pull/125), functional `31f46e5`, stacked after managed-memory #124.
Adds an explicit bounded/paged due view, exact item-revision queue, transparent
remaining counts and private grade-history round trip. The complete deck JSON
remains intact; edits/superseded sources do not inherit an old grade. Invalid
view options fail before source access, and output cannot enter source vaults.

`python -m unittest tests.test_learning_queue tests.test_learning --verbose`
passes **20 cases, zero skips**, Python 3.12.14 (26.442s) and 3.13.5 (25.986s).
Eight new cases cover bounded exact views, grade/stale history, suspended/empty
states, invalid selection, timezone ordering, CLI digest/import/replay, revocation
and storage separation. Actual Chromium full/due checks pass at 320/1280 with
keyboard/zoom/reduced motion and **zero axe findings/incompletes**. Exact commands,
limits and the ten-criterion mapping are in [learning.md](learning.md).

The local learning issue closes after this checkpoint merges; full hosted #17/#47,
notifications and sync are not invented prerequisites. No model/publishing/account
or private consumer is used. Next action: qualify/merge and then fix the recorded
mobile Explorer ARIA defect in the pinned #17 adapter, keeping full WCAG acceptance
separate from that bounded defect proof.


### Checkpoint G — #17 mobile Explorer disclosure semantics

Branch: `fix/17-mobile-explorer-aria`, [draft #126](https://github.com/egohygiene/mindgarden/pull/126), functional `ffa66d4`, stacked after learning #125. The owned
runtime adapter moves disclosure state from ordinary containers to native
controls, binds controlled content IDs and tracks the pinned controller's class.
No vendor source, canonical note, renderer pin or dependency changes.

Actual offline Quartz empty/small/205-note builds and **15 browser/axe audits**
pass with zero violations/incompletes, including expanded mobile Explorer, both
closed themes/viewports, keyboard controls, search, graph limits, no-JS fallback
and portal interruption/retry. Small actual output reproduces complete bytes.
`node --check profiles/quartz/v1.graph.js` passes. Updated source/portal goldens
reflect derived asset/manifest revisions only. The 33-case site/design/portal/
publication suite passes on Python 3.12.14 (45.255s) and 3.13.5 (43.936s).
See [the exact browser receipt/command](rendered-closeout-evidence.md).

The schema-inventory corrections from parent #124 and learning #125 are merged
into this combined branch without rewriting stack history. Parent #124's first
473-case CI attempt failed only its missing `memory-validity` inventory entry;
that failure is explicitly retained, not called passing. Corrected memory+contract
checks pass 22 cases on Python 3.12; contract checks pass on Python 3.13. Learning
plus contract checks pass 25 cases/5 contract cases respectively. Fresh automatic
head checks and the complete combined/source/wheel qualification follow.

#17 remains open for full manual WCAG, visual/consumer and hosted acceptance.
Next action: run complete compatibility on both Pythons, build clean artifacts,
repeat offline recovery/source/installed proofs, then merge #124 → #125 → this
checkpoint only after their corrected exact heads qualify. Release and deferred
context-package work remain parked.


Combined qualification correction: detached `ffa66d4` ran 481 cases on both
Pythons (484.985s / 463.205s): 480 passed and one nested journey golden failed.
The actual replay differs only at `/site/revision`, because its owned script was
corrected. That nested synthetic receipt is refreshed from the no-network demo;
no release/version/publishing behavior changes. The first run is not passing
qualification. Both full suites and artifact proofs are rerun after this fix.

Memory #124 is merged at `412e5f74e185771cf88023c24dc2d368c710b992` after
corrected Test 42563037646/release-preparation 42563037671 passed. Learning #125
is merged at `b38dbc82e237309358e2b99b2163bfc75e13657c` after Test 42563253994/
release-preparation 42563254071 passed. GitHub closes #49 and #28 respectively;
35 original/deferred issues remain open, with all 44 coverage rows preserved.


## Completed sleep queue and final qualification

The following status supersedes the draft-at-opening labels in the checkpoint
history above. All eight closed issues have their GitHub checklists and linked
acceptance receipts refreshed; no umbrella is closed by a bounded proof.

| Checkpoint / PR | Result | Remaining parent scope / next action |
| --- | --- | --- |
| Acceptance [#120](https://github.com/egohygiene/mindgarden/pull/120) | Merged `2c4c465`; closes #10/#11/#12/#26/#33/#51 | Optional evaluations are dispositions, not dependency adoption |
| Captured bookmarks [#121](https://github.com/egohygiene/mindgarden/pull/121) | Merged `4016958`; verified bundle→private review and authored graph handoff | #48 stays open for actual Akashic intake/publication and Mindcap recurring deltas |
| Incoming references [#122](https://github.com/egohygiene/mindgarden/pull/122) | Merged `1c01649`; exact safe inventory | #14 stays open; separately review general repair and public/policy changes |
| Selected builds [#123](https://github.com/egohygiene/mindgarden/pull/123) | Merged `51c29c4`; selected renderer invocation and missed-event reconciliation | #37 stays open for broader observation integration and approved pilot |
| Managed memory [#124](https://github.com/egohygiene/mindgarden/pull/124) | Merged `412e5f7`; closes #49 | External copied snippets cannot be recalled by local expiry |
| Due-card review [#125](https://github.com/egohygiene/mindgarden/pull/125) | Merged `b38dbc8`; closes #28 | Full hosted app remains #17/#47; notifications/sync are explicit non-goals |
| Mobile Explorer [#126](https://github.com/egohygiene/mindgarden/pull/126) | Qualified `32bcb3c`; final documentation head merges after its own CI | #17 stays open for manual WCAG, visual/consumer and hosting acceptance |

Complete frozen-source qualification is **481 tests, zero skips** on Python
3.12.14 (**493.978s**) and 3.13.5 (**463.964s**). Both earlier failed attempts
remain recorded above and in the [structured receipt](evidence/overnight-qualification.json).
The corrected functional head has successful automatic Test
[42564846322](https://github.com/egohygiene/mindgarden/actions/runs/42564846322)
(all four Linux/macOS jobs) and release-preparation
[42564846458](https://github.com/egohygiene/mindgarden/actions/runs/42564846458).
These runs are distinct from the final documentation head's CI; no workflow was
manually launched, and no release was prepared or published.

Executed from the clean detached functional checkout:

```bash
../qualified-python312/bin/python -m unittest discover --start-directory tests --verbose
../qualified-python313/bin/python -m unittest discover --start-directory tests --verbose
../qualified-python312/bin/python -m build --no-isolation --sdist --wheel --outdir .cache/dist
```

The two interpreters resolve `mindgarden` to that frozen source before shared
verification-only development packages. Build a new empty venv and install only
the local wheel with `python -m pip --python EMPTY_VENV/bin/python install
--no-index --no-deps LOCAL_WHEEL`. The installed distribution has **zero runtime
dependencies** and imports from that venv's prefix. The unpacked source archive
runs in another empty venv. The actual isolated commands were:

```bash
.cache/overnight/qualified-wheel/bin/python -I .cache/overnight/frozen-qualified/scripts/pipeline_completion_demo.py --workspace /tmp/mindgarden-qualified-wheel-pipeline --require-installed --report .cache/overnight/qualified-wheel-pipeline.json
.cache/overnight/qualified-wheel/bin/python -I .cache/overnight/frozen-qualified/scripts/provider_switch_demo.py --workspace /tmp/mindgarden-qualified-wheel-provider --require-installed --report .cache/overnight/qualified-wheel-provider.json
.cache/overnight/qualified-wheel/bin/python -I .cache/overnight/frozen-qualified/scripts/release_journey_demo.py --workspace /tmp/mindgarden-qualified-wheel-journey --require-installed --report .cache/overnight/qualified-wheel-journey.json
.cache/overnight/qualified-source/bin/python -I .cache/overnight/qualified-sdist/mindgarden-0.1.0/scripts/pipeline_completion_demo.py --workspace /tmp/mindgarden-qualified-sdist-pipeline --require-source --report .cache/overnight/qualified-sdist-pipeline.json
.cache/overnight/qualified-source/bin/python -I .cache/overnight/qualified-sdist/mindgarden-0.1.0/scripts/release_journey_demo.py --workspace /tmp/mindgarden-qualified-sdist-journey --require-source --report .cache/overnight/qualified-sdist-journey.json
```

All five reports match their committed golden **byte for byte**. Synthetic
conversation/PDF/image/audio evidence produces explicitly reviewed knowledge,
search returns its exact archive member/pointer and normalized source revision,
and the context is **4,419 bytes within 8,192**. A private canonical-home move,
vault relocation, export/restore and cache-free rebuild retain the exact source,
index, graph and context. Networking/external process entry points are blocked
inside these proofs; Google and models are unused. The journey script's name
reflects its historical fixture, not a release action. Local artifact hashes and
sizes are in the structured receipt; archive timestamps are not claimed
bit-reproducible release evidence. Subsequent documentation-only commits do not
change the tested runtime/contracts/profiles/scripts/tests/templates.

Actual pinned renderer checks, 15 zero-finding axe audits and learning full/due
browser checks are linked in [the browser receipt](rendered-closeout-evidence.md)
and [learning evidence](learning.md). Focused changed-code Ruff/format, Node
syntax, compileall, pinned owner schemas, all 24 proposed/null-approval ADRs,
44 unique coverage rows and bounded continuity checks pass. Historical whole-tree
lint findings and unavailable external evidence are not called passing checks.

There are **35 open issues**. After the final #126 merge, the next bounded task
is #15: add explicit selected binary diagram, excluded scratch/caption and
speaker/stance/correction fixtures through the existing curation workflow.
Then review #14's general incoming-reference repair as a distinct plan/apply
checkpoint. Do not invent Ollama accuracy, OpenViking useful native retrieval,
confidential runtime, accepted Aether/Akashic contracts, a real private archive
pilot or consumer hosting. Release #19/#27, proposed ADR ratification and deferred
#86–#91 remain parked. If #126 is still open when resuming, inspect its current
head/comments/checks and finish that authorized merge before starting new work.
