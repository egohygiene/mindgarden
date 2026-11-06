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
| #13 | Authored transformation/attribution negatives and remaining dispositions | Optional extraction producers/model evaluations, real review | Pending, stacked on #11 | Pending | Inspect existing curation contracts |
| #15 | Verify historical specs; selective attachment normalization | Untested profiles, multipart/collections, real archive pilot | Pending, stacked on #13 | Pending | Read exact v1.2.1/v2.0.1 and current specifications |
| #14 | Non-destructive existing-knowledge lifecycle and recovery | Full multi-consumer workflow and owner acceptance | Pending, stacked on #15 | Pending | Reuse routing/transaction services |
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
