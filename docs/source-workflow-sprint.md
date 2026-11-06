# Source workflow sprint — 2026-11-06

Main baseline: `30a29668a02740a91e77aec22f670a8270ccddf4`. Previous
#68–#73 are merged and tested; all 38 parent issues remain open. New contracts
implement proposed ADRs, without ratifying them. This sprint uses synthetic data.

## Dependency corrections and scope

The maintainer's confirmed order is #11 → #13 → #15 → #14 → #12 → #16.
These are bounded follow-ups over existing merged services, not prerequisites
that require each whole parent issue to close. #14 uses existing #12 retrieval;
it does not wait for the later performance checkpoint. #15 consumes the authored
#13 plan contract; optional model extraction is independent. #16 uses existing
publication and federation contracts; real consumer acceptance remains separate.
Retention/sensitivity rules from #46/#29/#31 apply throughout.

Modular gardens are a supported design use case: explicit data adapters, stable
publisher identities and pinned public selections. A remote installer, package
execution, marketplace, automatic updates and project lockfiles are deferred to
a separate bounded task. No cloud or model service becomes mandatory.

| Issue | Bounded checkpoint | Remaining parent scope | Draft / source | Verification | Exact next action |
| --- | --- | --- | --- | --- | --- |
| #11 | Versioned declarations, output limits, fixture conformance, immutable observations, reference extension | Mindcap #35 provider-neutral wire contract and real consumer proof | #74, `milestone/next-six-checkpoints`; `65b15fb` | 237 Python 3.12 tests; 18 targeted on 3.13; offline proof/build/distribution passed | Review #74; continue #13 |
| #13 | Merge authors/qualifications, exact relationships, selected claim evidence and authored redactions | Optional extraction producers/model evaluations, real review | #75, `feature/13-curation-conformance` over #74; `05e6cd2` | 18 tests on both Pythons; 24 compatibility tests | Review #75; continue #15 |
| #15 | V1.2.1 minimal reader, selected attachments/catalogs, opaque JSON evidence | V2.0.1 reader, multipart/collections, real producer pilot | #76, `feature/15-archive-selective-assets` over #75; `ec63d69` | 20 tests on both Pythons; offline golden proof | Review #76; continue #14 |
| #14 | Append-only private moves/merge retirement, exact aliases and recovery | Public/policy-changing and attached graph transfers; full owner/platform acceptance | #77, `feature/14-private-routing-transitions` over #76; `1a43002` | 24 tests on 3.12; 19 on 3.13; offline proof | Review #77 / proposed ADR-0022; continue #12 |
| #12 | Projection coverage and measured larger synthetic corpus | Broader consumer corpus and optional query stores | Pending, stacked on #14 | Pending | Profile current deterministic projections |
| #16 | Rendered routes and pinned modular public garden references | Live remote refresh, signatures/private federation and consumer pilots | Pending, stacked on #12 | Pending | Reuse descriptor verification and site manifests |

## External contracts inspected

Mindcap #35 remains open with no comments. At
`ce5f709990e82f6e8bd14fe128fa2608c6a1d05b`, `core/models.py` defines
CaptureEnvelope/StoredBundle runtime objects, not a versioned provider-neutral
CapturedSourceBundle wire contract with bookmark snapshot/delta semantics.
`contracts/protocols.py` defines presentation event/interaction interfaces.
The synthetic reference extension therefore claims only its local example
contract. It neither fetches URLs nor infers page content from bookmarks.

Archive v3.2.3, v3.2.2 and the older v1.2.1/v2.0.1 specifications were located
through the authorized Drive connector. Specification content and private file
locations stay outside this public checkout. Compatibility claims depend on
structural verification and committed synthetic fixtures, not mere availability.

## #11 verification

`python -m build --sdist --wheel --outdir .cache/dist` passed. Python 3.12
full discovery passed 237 tests (131.975 s); Python 3.13 targeted source/adapter/
contract suite passed 18. Offline private-garden demo with `--require-source`
matched its golden evidence; distribution suite passed 2. Compileall, diff and
pinned owner/continuity/38-row ledger checks passed. The initial optional
`--no-isolation` build lacked setuptools; the standard isolated build succeeded.
No new CI result or parent completion is inferred.

## Recovery

Each checkpoint records its functional commit, PR/base, exact commands/results,
blockers and next action here and in CONTINUITY.md. Dependent drafts stay stacked;
the last branch is the reproducible combined checkout. Do not close parent issues
or merge new drafts automatically. Link usable private workflow proof to #20
without claiming its publication/consumer acceptance criteria are complete.

## #13 verification and #11 discovery correction

Curation/transformation/contracts: 18 passed on Python 3.12 and 3.13. Routing,
archive and compaction compatibility: 24 passed. Compile/diff and owner checks
passed. The first #11 Python 3.13 full run failed to import the new test module
without an installed engine. `33fe7cf` adds the repository-standard source path
setup; standalone discovery then passed all 6 cases. Final combined full checks
will supersede that failed attempt; it is not recorded as passing.

## #15 verification

Archive selection/current archive/source adapter suites passed 20 tests on each
supported Python. `private_garden_demo.py --require-source` matched the offline
golden proof after the versioned adapter change. Compile/diff and owner checks
passed. Historical specifications are available; v2.0.1 reader implementation,
not source availability, is the remaining compatibility gap.

## #14 verification

Routing/lifecycle/curation/contracts: 24 passed on Python 3.12; lifecycle/scoped
retrieval: 19 passed on Python 3.13. Additional lifecycle/scoped/contracts: 24
passed on 3.12. Offline golden proof, compile/diff and pinned owner checks passed.
The transition design is proposed in ADR-0022, not accepted by these tests.
