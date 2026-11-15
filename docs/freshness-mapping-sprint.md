# Context freshness, summary refresh and reviewed CSV mapping

**Merged receipt:** The maintainer authorized #144 → #145 → #146 → #147. All four merged in order at main `270ced6a5d6ea0d4c07298fdcfebcae2363b7c8a`, with passing exact-head Test/preparation and the exact qualified #147 tree. [The receipt](evidence/freshness-mapping-stack-merge.json) supersedes earlier draft/pending observations below. [Remaining work and the local setup path](remaining-work-and-local-setup.md) are proposed for the next sync; no parent closure or ADR acceptance follows from these merges.

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

Draft [#145](https://github.com/egohygiene/mindgarden/pull/145) pins qualified functional `eb4280a6f9cabfd7b85f4e400bafd53a1f09e704` on #144. Initial owner checks lacked the new worktree's ignored inventory files; restoring the two existing pinned inventories makes all owner/bounds/44-row/native-child checks pass. The follow-up handoff changes documentation only.

## Checkpoint 2 — multi-source refresh

Branch `feature/46-multisource-refresh` stacks on #145 (`dcf6943`). The existing
`compaction preview` now accepts `--previous-manifest`, compares current authorized
node revisions and explains selected downstream staleness. Historical-only IDs
are omitted; full response bytes obey retention and session limits. Live validity
checks close the old-plan-date gap for facts incorrectly still marked current.

The committed quality case reuses the fictional business/correction/conversation/
career sources. Four nodes become stale, five remain current and old vault objects
remain present. Exact citation coverage is three sources; selected text is smaller
than source selections, while attribution, uncertainty and the unresolved agreement
remain explicit. Existing private proof TTL/revocation is exercised separately.
No actual model accuracy or real private pilot is claimed.

**43 cases pass per Python**, zero skips (3.12.14 105.284s / 3.13.5 102.118s):
`tests.test_compaction_refresh`, `tests.test_compaction`,
`tests.test_source_compaction`, `tests.test_context_dependencies`,
`tests.test_dependency_builds`, `tests.test_selected_builds`. New-fixture lint and
format pass. Initial old-only canary used an invalid uppercase identifier; it was
corrected to the existing identifier contract, without weakening validation.

Draft [#146](https://github.com/egohygiene/mindgarden/pull/146) pins qualified functional `e7e7fa2` on #145. The next handoff changes documentation only; hosted CI remains distinct.

## Checkpoint 3 — reviewed CSV mappings

Branch `feature/90-reviewed-csv-mapping` stacks on corrected #146 (`ac0e4ad`). A separate
`mapped-ledger-csv` adapter consumes reviewed `ledger-csv-mapping/v1` with the
explicit `mapping-v1` input profile. Signed ISO dates and debit/credit padded US
dates map to the existing ledger, with exact raw UTF-8 spans, canonical mapping
revision/provenance and supplied-file apply guards. Transaction identity, content
identity and normalized configuration identity remain distinct. Strict CSV/v0
behavior is preserved; unknown layouts and ambiguous values fail closed.

Two layouts plus overlap yield eight packet transactions and the independently
expected 2259.76 movement. Seven final mapping cases pass per Python, including
restoring/rebinding a clean vault and producing byte-identical packet files after
the old vault and mapping filenames are moved aside and retained. The broader
40-case adapter/packet/schema/v0 selection also passes (85.007s / 83.178s); after
adding the restore assertion, the seven final mapping cases pass again (12.566s /
12.104s). New-code lint/format passes after removing one unused test import.

[Mapping format, supported cases and exact CLI](csv-ledger-mappings.md). No real
records, credential/model calls, authority changes, source deletion or full parent
closure. Combined artifact checks and final CI observations follow separately.

## Combined qualification and review handoff

Review order is [#144](https://github.com/egohygiene/mindgarden/pull/144) →
[#145](https://github.com/egohygiene/mindgarden/pull/145) →
[#146](https://github.com/egohygiene/mindgarden/pull/146) →
[#147](https://github.com/egohygiene/mindgarden/pull/147). All remain drafts.
The reproducible combined branch is `feature/90-reviewed-csv-mapping`. Qualified
runtime/fixture/schema source is **`b7b279aab1ec3c38b77b7f3885374f5ca64f27fc`**;
following evidence/handoff changes are documentation only. Main is unchanged.

The combined 13-module selection passes **102 tests per Python, zero skips**:
3.12.14 in 237.252s; 3.13.5 in 234.681s. Command (use either supported interpreter):

```sh
python -m unittest tests.test_context_dependencies tests.test_dependency_builds tests.test_selected_builds tests.test_v1_retrieval tests.test_scoped_retrieval tests.test_v1_contracts tests.test_compaction_refresh tests.test_compaction tests.test_source_compaction tests.test_mapped_ledger tests.test_consultation tests.test_source_adapters tests.test_package --quiet
```

Both source and wheel build successfully with `python -m build --no-isolation
--sdist --wheel --outdir .cache/dist` using the prepared build environment. The
wheel remains dependency-free. Two distribution cases additionally pass per
Python (0.112s / 0.105s), covering new schema/module and all CSV/quality fixtures.

The **17 new boundary tests** pass independently from clean Git (74.145s), an
isolated installed wheel with no runtime dependencies (75.018s) and unpacked
source archive (74.651s), zero skips. These are `tests.test_context_dependencies`,
`tests.test_compaction_refresh` and `tests.test_mapped_ledger`. The driver imports
the selected package before helpers and verifies every loaded Mindgarden module
stays under its source/install root; source fallback cannot conceal wheel gaps.
The mapping packet includes the clean-vault restore proof in every artifact mode.

[The machine-readable receipt](evidence/freshness-mapping-qualification.json)
pins source/stack identities, artifact hashes, commands, results and CI. Scoped
lint/format, compilation, all 184 local targets across 16 Markdown files, pinned owner contracts and
unchanged-runtime comparison complete the handoff. An abbreviated candidate
revision in #146's first handoff failed the continuity schema; corrected metadata
commit `ac0e4ad` records its full qualified SHA and the child was fast-forwarded.
No runtime changed during that repair. An optional tool-version probe found no
separately installed wheel distribution; the successful build uses setuptools'
wheel generator, rather than claiming an unavailable tool version.

Exact-head automatic Test/preparation for #144 and #145 pass. The #146/#147
observations are recorded separately as they complete, and the later #147
handoff head has its own CI. No workflow was manually dispatched. Earlier
canceled or incomplete heads are not passing evidence.

**Next action:** review the stack in order and sync this batch. The next proposed
independent checkpoint is explicit reviewed source-correction → preparation-packet
freshness; broader #37/#46/#90 criteria, the actual private pilot and normative
policy/runtime gates remain open. #32 is optional. No further batch, real account
or private source is started by this handoff.
