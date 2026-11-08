# Broader product checkpoints

This batch covers #41, #43, #44, #32, #37, #49, #48 and #47. Every parent remains
open until its complete acceptance criteria are evidenced. The combined checkout
extends #93 → #94 → #95 → #96 → #97 → #98 → #99 → #100 → #101 →
#102 → #103 → #104. Release #19 and additional release work are deferred.
The six deferred proposals #86–#91 remain outside this batch.

## Refreshed dependencies

These are bounded dependency corrections proposed for review, not accepted ADRs.

| Item | Available contract / correction | Gate and exact next action |
| --- | --- | --- |
| #41 | Hygiene #15 is actually human-ratified: policy v1.2.0 and its ratification record are available; Holon #6 is delivered. Existing ADR-0007–0024 are proposed, not missing | Relay #5/#27/#33 and Pace #5 retain operational/adoption acceptance. Do not start historical backfill or rewrite legacy DECISIONS.md. Recheck those owners before the full reachable-history migration |
| #43 | Relay #30, Holon #22 and Observatory #7 are delivered. Pinned Relay `b4a88db20bc26f9ddefbee174baa8162cbe94ff2` exposes `collect-adrs` and a read-only artifact workflow | A preview of current canonical proposals can precede historical backfill. It cannot claim complete history or publication; retain native validation findings |
| #44 | A metadata projection can consume the existing public normalized decision read model without migrating ADRs or duplicating bodies in `.garden` | Preserve proposed/accepted/implemented distinctions; full narrative extraction and cross-garden/UI integration remain later |
| #32 | #12/#16/#31 already provide authorized input and reference ranking. An optional SQLite conformance candidate is independent of confidential runtime and full framework adoption | ADR-0016 remains proposed. Keep the reference default; measure an opt-in adapter without selecting it as the permanent product store |
| #37 | Existing sources, reviewed knowledge and claims can seed dependency fingerprints now | Do not invent a competing claim model; observation semantics, Mindcap #33 and a real private pilot retain their owning gates |
| #49 | #46 already distinguishes canonical knowledge, archival retention and context retention | Implement a disposable, reviewed memory projection over that boundary; no source deletion or new model dependency |
| #48 | Mindcap #35 is open; no delivered provider-neutral bundle/delta contract. Akashic #175 is open and has no delivered sanitized candidate-packet schema | The tested normalized v0.1 metadata subset can advance local cleanup. Do not claim source-bundle/raw capture verification or emit an invented Akashic packet; report unavailable handoffs |
| #47 | Shared Python application services exist; Realm #20/#34, Relay #40 and Aether #69 remain open | Accepted framework/runtime ADRs are absent. Prepare a concrete service/parity proposal; no implicit framework selection, HTTP server or Compose architecture adoption |

Hygiene's ratification is evidence of its policy approval, not approval of
Mindgarden's proposed ADRs. An open owner issue is not by itself proof that every
contract is unavailable; the table separates delivered interfaces from their
remaining integration acceptance.

## Stack and verification

| Issue | Checkpoint | Verification | Remaining parent scope / next action |
| --- | --- | --- | --- |
| #41 | Gate reconciliation in [#97](https://github.com/egohygiene/mindgarden/pull/97), `feature/43-decisions-contract-checkpoint`; `6ba1c2d` | Live owner/policy/ratification evidence inspected; legacy bytes and proposed approvals preserved | Blocked: shared operational/adoption readiness, then human-reviewed historical migration |
| #43 | Shared read-only preview caller in [#97](https://github.com/egohygiene/mindgarden/pull/97) | Engine Test 42308317027 passes; Decisions preview 42308318062 fails native source validation and preserves its sanitized report | Diagnose the exact native findings with the pinned runtime; qualify current corpus, then local/browser/artifact/composed-route proof; no deployed view claimed |
| #44 | [Public ADR adapter](adr-projections.md), [#98](https://github.com/egohygiene/mindgarden/pull/98), `feature/44-adr-projections`; `6666038` | Six focused cases and final full suites; exact source/revision, lifecycle/private/lineage/budget fixtures | Full narrative, inherited/private federation and UI integration remain; no canonical body copy |
| #32 | [Optional SQLite](query-stores.md), [#99](https://github.com/egohygiene/mindgarden/pull/99) plus [#104](https://github.com/egohygiene/mindgarden/pull/104), `fix/32-optional-sqlite-boundary`; `2d3e589` / `e100aae` | Ten cases including missing optional module/factory extension; 256-note measured parity; full final suites | Incremental updates, broader workloads/resources/platform/confidential assurance and permanent store disposition remain |
| #37 | [Dependency builds](dependency-builds.md), [#100](https://github.com/egohygiene/mindgarden/pull/100), `feature/37-projection-dependency-builds`; `4cd33ba` | Seven cases, authored request and lost-event golden: two affected views stale, unrelated bytes unchanged | Broader canonical observations/validity, targeted execution/events, Mindcap capture and approved private pilot remain |
| #49 | [Reviewed memory](assistant-memory.md), [#101](https://github.com/egohygiene/mindgarden/pull/101), `feature/49-reviewed-memory-snippets`; `fcef8ef` | Eight cases; 11,416 source-body → 187 snippet-body bytes; full cited bundle 20,699/32,768 bytes | Richer interactive review, provider tokenizers/adapters and automatic consumer refresh/revocation remain |
| #48 | [Private cleanup](bookmark-cleanup.md), [#102](https://github.com/egohygiene/mindgarden/pull/102), `feature/48-private-bookmark-cleanup`; `4816868` | Seven cases; resume equals full review, exact normalized input retained and summaries redacted | Mindcap bundle/delta/raw capture verification, canonical URL/freshness and accepted Akashic packet remain unavailable |
| #47 | [Shared-service/parity proposal](shared-service-slice-proposal.md), [#103](https://github.com/egohygiene/mindgarden/pull/103), `proposal/47-shared-service-slice`; `2867d10` | Current callables, transport/review/lifecycle/accessibility and two-consumer acceptance mapped; no server implemented | Blocked: review/dispose framework/auth/runtime ADRs, then one accepted transport slice and Realm-owned clean-start proof |

## Decisions preview and source ownership

The preview caller only enables Relay's existing public contract. It has read-only
permissions, no secrets, no Pages/OIDC authority, no consumer scripts and a separate
owned output/work directory. Relay generates an artifact; this repository does not
add a second renderer or Pages deployment. The route is
`intelligence/decisions/`; any friendly `/decisions/` alias belongs to a later,
reviewed single-site composition. No alias or live site is claimed here.

For local reproduction, acquire the exact Relay revision and its locked trusted
Hygiene/EgoLint/Observatory inputs, then follow its
[public ADR collector/build guide](https://github.com/egohygiene/relay/blob/b4a88db20bc26f9ddefbee174baa8162cbe94ff2/docs/repository-adr-collector.md).
The native collector needs the pinned Rust toolchain and prepared Python runtime.
Rust is unavailable in this workspace; no local collector or accessibility pass
is claimed. GitHub preview results must be inspected separately from local checks.
Do not substitute an agent-authored snapshot to bypass a native validation error.

ADR impact: this checkpoint applies existing owner boundaries and preserves all
proposed statuses. ADR not required for a read-only consumer workflow declaration;
no new decision authority, renderer, hosting or product framework is selected.

## Combined local verification

At source `4816868` with documentation-only follow-up `0319170`, both full suites
pass with no skips: 358 tests on Python 3.12.14 (273.225 s) and 3.13.5 (258.766 s).
Commands: `.venv/bin/python -m unittest discover --start-directory tests --verbose`
and `.cache/python313/bin/python -m unittest discover --start-directory tests
--verbose`. The local-network permission is needed for the existing loopback
preview test; no external model or Google integration is used. Hosted CI remains
separate. Shared Decisions preview run 42308318062 fails native source validation
and retains its sanitized report; that finding is not replaced by passing engine
tests. Final compatibility follow-ups are recorded separately below.

## Final compatibility receipt and regroup

Functional combined source: `e100aaea9f9a9a1c744b9a5607065d1b3bb6ae53`.
Draft #104 contains the optional-extension fix, replaceable factory qualification
and formatting of only the new modules/fixtures with Ruff 0.11.13. Later receipt
edits are documentation only. All 44 parent/deferred issues remain open.

| Exact command / probe | Result |
| --- | --- |
| `.venv/bin/python -m unittest discover --start-directory tests --verbose` | 360 passed, no skips; Python 3.12.14; 278.834 s |
| `.cache/python313/bin/python -m unittest discover --start-directory tests --verbose` | 360 passed, no skips; Python 3.13.5; 267.789 s |
| `.cache/python313/bin/python -W error::ResourceWarning -m unittest tests.test_query_store -q` | 10 passed; 4.048 s; missing SQLite preserves ordinary CLI; no connection leaks |
| `.venv/bin/python -m build --sdist --wheel --outdir .cache/product-final-dist` | Fresh distributions built, no runtime dependencies |
| Clean `git archive` source; `python -S scripts/release_journey_demo.py --workspace <new-synthetic-root> --require-source --report <report>`; compare committed golden | Exact match; archive→review→routing→public-only projection/federation→vault restore/relocation without model/Google calls |
| Clean wheel environment; `python -I scripts/release_journey_demo.py --workspace <new-synthetic-root> --require-installed --report <report>`; compare golden | Exact match; no source fallback |
| Installed `python -I scripts/provider_switch_demo.py --workspace <new-synthetic-root> --require-installed --report <report>`; compare golden | Exact provider recovery match |
| Installed CLI `memory` preview/apply, `build-projections` preview/apply/reconciliation, `query-store` plan/build/search/audit against authored fixtures | Pass; loaded modules confirmed inside interpreter prefix; exact memory metrics and affected-output states |
| `python3 .cache/context_phase_owner_checks.py`, compilation, focused `ruff check --select F,E9`, `git diff --check` | Pass; pinned schema/approval invariants and 44 unique ledger rows |

Fresh distribution SHA-256: sdist
`c3e968544c1628aca7176e0528810866dcbae4225c977d721249cdc7791540b2`;
wheel `a7a6de5e14409e4cf1eb4ad9a281cb8601bf20834628a6ace877a10455c95417`.
These are development compatibility artifacts, not a published release or a
claim of reproducible release-bundle acceptance.

At the final hosted refresh, engine Test runs for #96–#102 pass. #103 was still
running; final #104 is checked separately. Shared Decisions preview
[42308318062](https://github.com/egohygiene/mindgarden/actions/runs/42308318062)
fails at `collection-validation-normalization: source-validation`; its failure
report was retained. Local engine success does not satisfy that gate. The exact
native cause must be inspected through the pinned owner runtime; it is not
inferred from a closed delivery issue or replaced by an authored snapshot.

Reproduce all functional changes with `git fetch origin` followed by
`git switch --detach e100aaea9f9a9a1c744b9a5607065d1b3bb6ae53`; use the current
`fix/32-optional-sqlite-boundary` tip for the final receipt. Review/merge only after
the maintainer sync, in the explicit stack order above. No PR is automatically
merged. The exact next action is **regroup and review the bounded stack**, resolve
native preview/architecture gates, and select the next authorized ready work.
The #20 real-pilot inputs and consumer cutover remain open; #19 and additional
release work and #86–#91 remain deferred. No real archive, Drive, model, private
consumer, package publication or Pages deployment was used or modified.

## Repeatable source and installed product probe

The final receipt adds a portable verification script; engine code remains the
qualified `e100aae` source. From the current combined checkout, run:

```bash
.venv/bin/python -S scripts/product_checkpoint_demo.py --require-source
.cache/product-final-wheel/bin/python -I scripts/product_checkpoint_demo.py --require-installed
```

The installed command requires a fresh environment containing the built wheel;
the engine loads from that interpreter's prefix, while explicitly supplied
synthetic fixtures come from this checkout. Both runs match
[`expected-proof.json`](../tests/fixtures/product-checkpoint/expected-proof.json).
The script creates and cleans only its own temporary synthetic gardens. It accepts
no real session/archive/workspace input, uses the declared synthetic 2026-11-06
review clock, blocks sockets in parent/CLI processes, and verifies memory export,
SQLite build/search/audit, dependency reconciliation and private bookmark export.
It needs FTS5 for its explicitly optional-store proof. No accepted Akashic packet
is claimed; unavailable handoff is part of the golden.

The separate installed archive/routing/federation/relocation journey also matches
its golden with `sys.modules["sqlite3"] = None` before loading the CLI. The ordinary
workflow therefore works without the optional database extension, as well as
without model/Google calls. This is an in-process disabled-capability proof,
not operating-system isolation certification.
