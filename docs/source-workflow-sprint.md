# Source workflow sprint — 2026-11-06

All six bounded checkpoints are implemented and locally tested in **drafts**
[#74](https://github.com/egohygiene/mindgarden/pull/74) →
[#75](https://github.com/egohygiene/mindgarden/pull/75) →
[#76](https://github.com/egohygiene/mindgarden/pull/76) →
[#77](https://github.com/egohygiene/mindgarden/pull/77) →
[#78](https://github.com/egohygiene/mindgarden/pull/78) →
[#79](https://github.com/egohygiene/mindgarden/pull/79).

Main remains `30a29668a02740a91e77aec22f670a8270ccddf4`. The reproducible combined
checkout is `feature/16-rendered-garden-references`, tested functional source
`b88cc97c62cb855a029d30f00f23a9042166e1ac`. No new draft is merged or fully
accepted; all 38 parent issues remain open. ADR-0007–0022 remain proposed with
null approval. Only synthetic gardens, archives and provider fixtures were used.

## Dependency corrections and scope

The confirmed order is #11 → #13 → #15 → #14 → #12 → #16. These follow-ups build
on merged services; they do not require closure of each preceding whole parent.
#14 uses existing #12 retrieval without waiting for its performance follow-up.
#15 uses the authored #13 contract without requiring optional model extraction.
#16 reuses publication/federation contracts; real consumer proofs remain separate.
Retention and sensitivity from #46/#29/#31 continue to apply.

Modular gardens are a supported design use case: explicit adapters, publisher
identity and pinned public data. The package reference grants no execution or
write authority. A remote installer, marketplace, automatic updates, dependency
resolution and project lockfiles remain a separate bounded task.

| Issue | Completed checkpoint | Remaining parent scope | Draft, branch/base and functional commits | Verification | Exact next action |
| --- | --- | --- | --- | --- | --- |
| #11 | Versioned adapter declarations, limits, reusable conformance harness, immutable observations and reference extension | Mindcap #35 wire contract, real producer handoff and wider corpus | #74, `milestone/next-six-checkpoints` / main; `65b15fb`, discovery fix `33fe7cf` | 237 initial full tests; 18 targeted on both Pythons; CI passed | Review #74; retain upstream handoff gap |
| #13 | Merge authors/qualifications and attribution lineage, exact relationships, selected claim evidence and authored redactions | Optional extraction producers, resume/evaluation and wider media/consumer proofs | #75, `feature/13-curation-conformance` / #74; `05e6cd2` | 18 targeted on both Pythons; 24 compatibility; CI passed | Review #75; preserve separate human authority |
| #15 | V1.2.1 minimal reader, v3.2 profiles, independent selected attachment catalogs/bytes and opaque JSON assets | V2.0.1 reader, multipart/collections and real producer pilots | #76, `feature/15-archive-selective-assets` / #75; `ec63d69`, golden correction `3fe5689` | 20 targeted on both Pythons; corrected proof suites 3 each; CI passed | Review #76; implement v2.0.1 against inspected baseline/patch in a later checkpoint |
| #14 | Append-only private moves/merge retirement, exact aliases, one retrievable home and rollback | Public/policy-changing and attached graph transfers; wider platform/owner acceptance | #77, `feature/14-private-routing-transitions` / #76; `1a43002`, propagated correction `a6aa934` | 24 targeted on 3.12; 19 on 3.13; CI passed | Review #77 and proposed ADR-0022 |
| #12 | Outbound links, eight-projection golden/schema matrix, selected redaction provenance and bounded fitting | Wider relationship/consumer matrix and larger measured envelopes; optional stores | #78, `feature/12-projection-conformance` / #77; `83fe3aa`, propagated correction `fef556e` | 23 targeted on 3.12; 7 on 3.13; 1024-note benchmark; CI passed | Review #78; retain measured bounds for future query-store decisions |
| #16 | Pinned rendered-route adapter, portable data-only garden references and explicit catalog refresh | Private federation, authentication/signatures, remote acquisition, full installation and Akashic/Aether pilots | #79, `feature/16-rendered-garden-references` / #78; `e3514d6`, combined `b88cc97` | 40 federation/portal/contracts on 3.12; 4 on 3.13; actual prior Quartz artifact; combined 260 on both; CI passed | Review #79; retain publisher ownership and separate session authority |

## Combined verification

Exact commands were run on the combined source above. All tests passed without
skips; external CI results below are separate from local results.

| Command/check | Result |
| --- | --- |
| `.venv/bin/python -m build --sdist --wheel --outdir .cache/dist` | Fresh source/wheel built; no runtime dependencies |
| `.venv/bin/python -m unittest discover --start-directory tests --verbose` | 260 passed, Python 3.12.14, 165.904 seconds |
| `.cache/python313/bin/python -m unittest discover --start-directory tests --verbose` | 260 passed, Python 3.13.5, 154.450 seconds |
| Both interpreters: `-m compileall -q src scripts tests examples` | Passed |
| `python3 .cache/six_owner_checks.py` | Proposed/null ADRs, pinned Hygiene schema/policy/set/index, pinned Aether continuity, 12 headings/limits and 38 unique coverage rows passed |
| Changed Markdown relative links; `git diff --check` | Passed |
| `node --version` | v24.19.0 |
| Clean `git archive b88cc97` source, `python -S`, private/compaction/reference demos with `--require-source` | All complete reports equal committed goldens |
| Fresh wheel-only venv, `python -I`, same three demos with `--require-installed` | All reports equal clean-source outputs and committed goldens |
| Clean source: `python -S -m unittest tests.test_projection_corpus.ProjectionCorpusTests.test_projection_golden_schema_matrix_and_exact_claim_evidence -q` | Eight projections rebuilt; 1 matrix test passed |
| Installed version/validate/verify/publish/library v0 smoke | Passed: 3 notes, 1 context profile, 2 public projected notes |
| Wheel/source inventory check | New modules/contracts, extension, synthetic historical fixture and proof scripts packaged |

The 1024-note [projection report](projection-conformance.md) records six identical
pre/post-change artifact hashes, observed 8–17 second operations and 92,852,224-byte
peak process RSS. Its measured reference envelope is <=60 seconds per projection
and <=256 MiB; the 4096 input bound is not a measured performance claim.

## CI and correction history

All six tested implementation heads have successful **automatic** Test runs on
both supported Python jobs; no workflow was manually dispatched.

| Draft | Tested head | Successful Test run |
| --- | --- | --- |
| #74 | `33fe7cf35f82ba0e93e3e707540498cded689abd` | [42172135507](https://github.com/egohygiene/mindgarden/actions/runs/42172135507) |
| #75 | `046a8ad9fa9e1295404bed61fe1eac1fc2cdb0d2` | [42172295516](https://github.com/egohygiene/mindgarden/actions/runs/42172295516) |
| #76 | `3fe5689eca924387e4a7138dea3221f36d5603a9` | [42176087142](https://github.com/egohygiene/mindgarden/actions/runs/42176087142) |
| #77 | `a6aa934f88b13dcca93fac404c79887e16ed1b1b` | [42176123517](https://github.com/egohygiene/mindgarden/actions/runs/42176123517) |
| #78 | `fef556e856dc51a8697bc1bc76c4e2b65981de7f` | [42176128594](https://github.com/egohygiene/mindgarden/actions/runs/42176128594) |
| #79 | `b88cc97c62cb855a029d30f00f23a9042166e1ac` | [42176129395](https://github.com/egohygiene/mindgarden/actions/runs/42176129395) |

The final handoff is documentation-only over these tested inputs. Its new CI
status must be observed separately, not inferred from the implementation run.

The first #11 Python 3.13 local discovery failed because the new test lacked the
repository-standard source path setup; `33fe7cf` fixed it. The initial #76–#79
full runs failed two stale golden reports after the adapter 1.1.0 metadata change.
[The reconciliation](archive-version-golden-note.md) records exactly three changed
hash fields, unchanged source/evidence/vault facts, independent complete-report
assertions, and normal propagation from `3fe5689` through the stack. Earlier demo
invocations proved their internal checks, not the stale golden comparisons. These
failures are superseded by the successful receipts above, never called passing.

## External contracts and retained acceptance

Mindcap #35 is open with no comments. At
`ce5f709990e82f6e8bd14fe128fa2608c6a1d05b`, its core models define runtime
CaptureEnvelope/StoredBundle objects; inspected contracts define interaction
interfaces, not the required provider-neutral bookmark snapshot/delta wire
contract. The synthetic extension claims only `example.reference-capture/1`.

Archive v1.2.1, v2.0.0 plus the v2.0.1 delivery patch, v3.2.2 and v3.2.3 were read
through authorized Drive tools. Full specification text/private locations remain
outside this public checkout. Tested interpretation is v1.2.1 minimal single-unit
and v3.2.2/v3.2.3 full-source/summary-journey. A v2.0.1 reader is not implemented;
source availability is no longer its blocker.

Akashic #176 and Aether #69 are open with no comments. Their publisher-specific
projection and broader session/runtime acceptance require owner proofs. Generic
synthetic routes or package references do not claim those integrations. The
rendered adapter separately verified the prior actual pinned offline Quartz
artifact: 60 files, 3 routes, exact manifest pin recorded in
[federation evidence](federation.md).

The [private workflow evidence](private-garden-evidence.md) links the continued
archive → reviewed prompt → exact search citation → bounded context → relocated
vault → clean rebuild proof to [#20](https://github.com/egohygiene/mindgarden/issues/20).
PR #79 also references #20. This does not complete #20's broader consumer,
publication and release acceptance, or the full source-vault parent scope.

## Recovery and next action

Checkout `feature/16-rendered-garden-references` to reproduce the combined work.
Review #74 → #79 in order, preserving the explicit stack until the maintainer
requests merges. All meaningful progress is pushed; no history was force-rewritten.
Keep proposed decisions separate from accepted decisions and parent completion.
Use the remaining-scope column to choose the next bounded follow-up after review.
