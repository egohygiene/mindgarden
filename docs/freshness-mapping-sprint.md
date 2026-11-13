# Context freshness, summary refresh and reviewed CSV mapping

The maintainer selected #37 → #46 → #90 on 2026-11-13 by asking to continue the
recorded next batch. All checkpoints use synthetic sources and existing Python
application services. Parent acceptance, private pilots, normative policy,
proposed ADRs, release work and deferred #88/#91 retain their existing gates.

## Stack and dependencies

Main remains `6c9954b`. Draft #144 at `3c61db4` has passing automatic Test
43500532675 and preparation 43500532550, no review comments. It remains unmerged.
This batch preserves its exact tree as integration ancestry; the context adapter
does not require the routing-history fix as a semantic prerequisite.

| Order | Bounded checkpoint | Required existing contract | Parent scope retained |
| --- | --- | --- | --- |
| 1 / #37 | Build actual Markdown/JSON context packs from explicit reviewed record dependencies; reconcile a missed update and rebuild selected affected outputs | Existing dependency request/manifest, context profile/service and scoped generated bundles | Broader observation integration, domain consumers and approved private pilot |
| 2 / #46 | Refresh a multi-source authored hierarchy with corrections/contradictions and measurable fixture quality; identify affected summaries/context without deleting originals | Existing compaction/retention manifests, exact evidence, curation and expiry services; #37 is integration ancestry, not raw-source authority | Semantic model quality, large corpora, destructive retention and approved private pilot |
| 3 / #90 | Review mappings for two supplied synthetic CSV layouts, preserve original spans/config revisions and feed the existing preparation packet | Existing source adapters, normalized ledger and reviewed packet; independent of refresh for normalization correctness | Arbitrary formats, richer accounting/reconciliation, real inputs and pilot |

No database, model, provider, daemon or competing garden model is selected.
Provider capture stays separate from normalization. Mappings are explicit human
configuration; source content never chooses executable handlers.

## Checkpoint 1 — actual context consumers

The existing `dependency-build-request/v1` now accepts the explicit
`context-pack/v1` renderer with `context_profile`, `context_format` and output
contract `mindgarden.context/v1`. Old record-view requests remain unchanged.
Schema validation rejects missing or mismatched profile/format/output contracts.

The adapter calls the existing bounded context service with an explicit record
selection. That service still authorizes and reviews records before selection;
it cannot receive an injected index. Profile include/exclude selectors must stay
inside the declared authorized selection. Lexical ranking is bounded to that
selection, so unrelated records cannot silently enter an already reviewed build.

In this explicit mode, context inputs record exact selected artifact references
and indexed-record checksums, including review/provenance/qualifications.
Whole-garden/session revisions remain live apply guards, rather than contaminating
an unrelated context's fingerprint. Ordinary context commands retain their
previous format and broad lexical-search behavior.

Use the existing `build-projections` preview, reconciliation, repeated
`--select-output` and digest-bound `--apply`. A new immutable bundle is written;
old outputs and originals remain intact. Budgets, sensitivity, expiry and
revocation remain enforced. The synthetic missed-event case changes the
deployment claim: its agent context and professional view become stale while the
unrelated context stays byte-identical. Selected execution invokes only the
chosen context renderer, with the same bytes as its complete-build entry.

Branch: `feature/37-consumer-freshness`, on #144. Exact tests, PRs and commits are
recorded as checkpoints qualify. Initial five consumer cases pass. An initial
broader command named nonexistent `tests.test_scope`; that invocation is not
reported as passing. The corrected suite uses `tests.test_scoped_retrieval`.

## Resume and remaining work

Read CONTINUITY.md and refresh live PR state before continuing. Preserve explicit
stack ancestry and the final combined checkout. Push each checkpoint to a draft
PR and retain all 44 coverage rows. Local evidence and exact-head hosted CI are
separate. No real account, archive, credential or model is accessed by this batch.

Checkpoint 1 qualification: **41 tests per Python**, zero skips (3.12.14 51.052s / 3.13.5 48.656s): `tests.test_context_dependencies`, `tests.test_dependency_builds`, `tests.test_selected_builds`, `tests.test_v1_retrieval`, `tests.test_scoped_retrieval`, `tests.test_v1_contracts`. New-test Ruff/format and whitespace pass. No complete-parent or private-pilot claim.
