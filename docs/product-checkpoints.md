# Broader product checkpoints

This batch covers #41, #43, #44, #32, #37, #49, #48 and #47. Every parent remains
open until its complete acceptance criteria are evidenced. The combined checkout
extends #93 → #94 → #95 → #96; release #19 and additional release work are deferred.
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
| #48 | Mindcap #35 is open; no delivered provider-neutral bundle/delta contract. Akashic #175 is open and has no delivered sanitized candidate-packet schema | Local authored metadata cleanup can advance through an explicit provisional fixture profile. Do not claim Mindcap compatibility or emit an invented Akashic packet; report unavailable handoffs |
| #47 | Shared Python application services exist; Realm #20/#34, Relay #40 and Aether #69 remain open | Accepted framework/runtime ADRs are absent. Prepare a concrete service/parity proposal; no implicit framework selection, HTTP server or Compose architecture adoption |

Hygiene's ratification is evidence of its policy approval, not approval of
Mindgarden's proposed ADRs. An open owner issue is not by itself proof that every
contract is unavailable; the table separates delivered interfaces from their
remaining integration acceptance.

## Stack and verification

| Issue | Checkpoint | Verification | Remaining parent scope / next action |
| --- | --- | --- | --- |
| #41 | Scheduling-gate reconciliation; no backfill | Read live owner issues, policy and ratification evidence; preserve legacy bytes and all proposed approvals | Shared operational readiness, then human-reviewed historical migration |
| #43 | Read-only shared Relay preview caller | Pinned reusable-workflow input contract inspected; YAML parsed locally | Hosted preview failed native source validation in run 42308318062; sanitized failure report retained. Local renderer/browser checks, composed route and deployment remain unverified |
| #44 | [Public metadata projection](adr-projections.md), `feature/44-adr-projections`; functional `6666038` plus CLI test | Six focused tests; schema/compatibility checks | Narrative extraction, inherited/private federation and UI integration remain; canonical bodies are not copied |
| #32 | [Opt-in SQLite](query-stores.md), `feature/32-sqlite-query-store` | Eight tests per Python; 256-note exact parity and measured costs | Incremental updates, broader performance/platform/confidential assurance and permanent adoption remain |
| #37 | [Dependency builds](dependency-builds.md), `feature/37-projection-dependency-builds`; functional `4cd33ba` | Seven focused cases; committed authored request and lost-event reconciliation golden | Canonical observation integration, background targeted execution, Mindcap capture and private pilot remain |
| #49 | [Reviewed memory](assistant-memory.md), `feature/49-reviewed-memory-snippets`; functional `fcef8ef` | Eight cases per Python; 11,416 source-body bytes → 187 snippet-body bytes; 20,699-byte cited bundle | Richer interactive review, provider tokenizers/adapters and automated consumer refresh remain |
| #48 | [Private cleanup/export](bookmark-cleanup.md), `feature/48-private-bookmark-cleanup`; functional `4816868` | Seven cases per Python; resume equals full review, originals preserved and CLI summaries redacted | Mindcap bundle/delta, raw capture verification, canonical URL/freshness and accepted Akashic packet remain unavailable |
| #47 | [Concrete shared-service/parity proposal](shared-service-slice-proposal.md); accepted-ADR gate remains closed | Current callables, transport/review boundaries, two-consumer and lifecycle acceptance mapped | Review/dispose framework/auth/runtime ADRs; then one accepted transport slice and Realm-owned clean-start proof |

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
