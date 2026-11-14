# Remaining implementation and acceptance audit

The maintainer parked local setup and authorized independent repository work.
This audit refreshed main `270ced6`, all 34 open issues, the selected issue
comments, PR #148 and the relevant external owner issues. Implementation,
tests, merged state, human decisions and actual consumer proof remain distinct.

## Findings delivered in this stack

| Finding | Existing owner | Result |
| --- | --- | --- |
| No concise packet dependency comparison | #37/#90 | [Draft #149](https://github.com/egohygiene/mindgarden/pull/149) adds exact selected-input currentness, preserved history and action/reason diagnostics. |
| Renewed authority makes unchanged packet verification conflict | #90/#31 | #149 adds a read-only verifier that checks current authorized bytes without reusing the historical marker's authority or rewriting output. |
| Captured CSV cannot select the reviewed mapping adapter per file | #87/#90 | [Draft #150](https://github.com/egohygiene/mindgarden/pull/150) supplies explicit reviewed provider-ID associations, full mapping provenance and exact overlap occurrences. |
| Previous catalog can advertise unselected historical identities or poison current ambiguity checks | #16/#31 | The audit child filters comparison metadata to current verified gardens. A valid synthetic old-only canary is observationally absent; unavailable inputs retain generic diagnostics and no old refresh IDs. |
| Continuation-state ingestion has code but lacks its own authority-boundary proof | #15 | New full/compact v3.2.2/v3.2.3 fixtures preserve exact continuation bytes as unreviewed summary-derived source data. Instructions cannot run tools or create knowledge; missing/corrupt bytes fail before writes. |

No duplicate setup or implementation issue is needed for these existing owners.
All code remains on reviewable drafts; no broad parent is closed by this audit.

## #16 — engine criteria and actual integrations

The 13 listed criteria have concrete implementation/test evidence, with the
historical-metadata finding requiring this new draft fix before acceptance:

| Listed criterion | Source and synthetic evidence |
| --- | --- |
| Versioned descriptor and stable identity | `contracts/v1/federation-descriptor.schema.json`, `domain/federation.py`, `tests/test_federation.py` |
| Reviewed-public indexes, graphs and counts | Public selection/inheritance before body access; private-content noninterference cases in `tests/test_federation.py` |
| Immutable represented revisions | Descriptor, artifact checksum and rendered manifest pins; stale/corrupt inputs rejected |
| Deterministic multiple-descriptor catalog | Multi-garden fixtures, order independence and clean/relocated rebuilds |
| Duplicate, stale, incompatible, unavailable and conflicting-home diagnostics | `tests/test_federation.py`, `tests/test_rendered_federation.py` |
| Canonical links without copied note bodies | Catalog assertions and exact rendered-route membership checks |
| Private/internal local federation | `tests/test_local_federation.py`; no private identity in public descriptors |
| Agent instruction boundary and provenance | Data-only entrypoint/bundle assertions and exact source references |
| Catalog → selection → bounded context | `tests/test_public_bundle_context.py`; current authority gates supplied bundle reads |
| Scope, revision, inclusion reason and budgets | JSON/Markdown context schema checks and item/byte/denial adversaries |
| Aether authority remains independent | Source/tool permissions are not granted by catalogs or producer assertions |
| Multi-garden aggregation, isolation and refresh | Healthy-peer selection, unavailable/stale peer handling and explicit rendered-pin refresh |
| Framework-independent public contract | Ordinary schemas/services and data-only rendered inputs; no required framework/server |

The four existing federation modules passed 40 tests per Python (3.12 86.294s;
3.13 82.385s) before this audit's new canary. That new negative test exposed an
actual defect and failed against the prior implementation (2.883s); final
corrected qualification is recorded in the stack receipt. Older success is not
represented as proving the new case.

After the fix is merged and its acceptance evidence reviewed, #16 is a strong
closure candidate against those listed engine criteria. Akashic #176's actual
producer fixture and Aether's real runtime integration remain separately owned,
unperformed integrations. Checksum binding is explicitly supported by the issue;
signatures, remote fetching and mandatory hosting are not invented closure gates.
This does not accept proposed ADR-0011 or make producer approval assertions true.

## Other audited parents

| Issue | Implemented evidence | Exact remaining action |
| --- | --- | --- |
| #15 archive ingestion | Named v1.2.1, v2.0.0–2.0.2 and v3.2.2/v3.2.3 profiles; primary/fallback content equality, exact spans, legacy/selected diagrams, hostile ZIPs and authored curation; new continuation-state proof | Complete the explicit delivery/runtime-identifier privacy and known-bootstrap acceptance mapping against authoritative contracts. Unknown future formats remain compatibility gaps. Actual private legacy/Empathy proof is #20, not an extra synthetic importer requirement. |
| #32 optional query stores | Versioned protocol, SQLite lexical/typed parity, live scope, owned recovery, corruption/stale/unavailable states and measured small synthetic baseline | The **full original issue body** includes incremental refresh and migration. The current port declares those unsupported. Implement/test or explicitly disposition those requirements; do not dismiss them because a checkbox summary is shorter. Permanent database adoption is optional. |
| #43 Decisions publication | Pinned shared Decisions preview, source links, private-data filtering, source-validation correction and browser/portal evidence | Actual canonical collection/adoption and full route/consumer acceptance remain tied to #41/#42 and Relay's shared pipeline. Reuse that pipeline; do not build another renderer or ratify historical decisions. |
| #44 ADR knowledge relationships | Deterministic public metadata, exact canonical ownership/revision, lifecycle/history, labeled inference and bounded context | Complete typed non-decision/cross-garden relationships and actual Relay/Observatory consumer composition against the supported owner contracts. Keep canonical ADR bodies separate; private/inherited authority is not granted by caller JSON. |

Issue text and executable behavior both matter. A missing schema, owner decision
or real integration stays explicit. Passing a synthetic fixture cannot establish
private pilot approval, hosted-model permission, confidential runtime or factual
model accuracy. Conversely, optional larger formats, dashboards and permanent
stores must not silently become requirements of every existing bounded issue.

## Proposed next independent sprint

1. Review/merge #148 → #149 → #150 → the audit child in order. Preserve the
   combined child checkout and run only checks justified by conflicts/new changes.
2. Reconcile #16 and #90's complete listed criteria against the merged receipts;
   close genuinely met scope and assign concrete remaining work without adding
   private-pilot or optional renderer gates to the synthetic issue.
3. Finish #15's delivery/bootstrap privacy/conformance evidence with synthetic
   fixtures for the actual available versions. Do not invent unavailable formats.
4. Implement one bounded #32 incremental owned-cache/update-and-recovery slice,
   with reference parity, fresh authority and an explicit migration/rebuild path.
5. Extend #44's supported public relationship/read-model composition where owner
   contracts are available. Keep #41/#42 human decisions, #43 shared-system
   adoption and #20's approved real consumer proof distinct.

The latest owner refresh still has Hygiene #39, Realm #28/#29/#30, Relay
#5/#27/#33, Pace #5, Akashic #175/#176 and Empathy #65 open. Open issue status
does not imply zero implementation; only actually available artifacts and
authority support a compatibility claim. Missing confidential/consumer contracts
are not replaced by local mock assertions. #19/#27 and #88/#91 remain parked.

Mac setup, real account content and credentials remain parked. This audit adds
no services, release, deployment, model calls, source cleanup or ADR ratification.
Exact local/CI observations and final artifacts are in the qualification receipt
and [continuity checkpoint](../CONTINUITY.md).

## Decision-status count correction

The current source has 18 indexed ADR files, all proposed with null approval,
and six inline legacy decisions retaining their original Accepted labels in
`DECISIONS.md`. Earlier handoff wording that called all 24 proposals was
inaccurate. This audit changes no status or approval; #41 still owns historical
authority mapping, and #42 still owns human disposition of consequential proposals.

## Final verification

Combined source `b35b597` passes 184 targeted cases on each supported Python, zero skips; all three clean artifact forms pass eight boundaries and three complete golden proofs each. Functional #149/#150/#151 Test/preparation are green. The [qualification receipt](evidence/repository-audit-qualification.json) preserves exact commands, hashes, runner sources, staged failures/corrections and limitations. This is tested draft implementation, not merged/full parent acceptance.


## Subsequent authorized follow-through

The next [integration sprint](pipeline-integration-sprint.md) now implements #15 delivery privacy and bounded #32 refresh/migration on drafts. Its current evidence supersedes the unsupported-capability snapshot above; original requirements remain intact. The live Relay #115 refresh also verifies the canonical ADR collector/build checkpoint is **closed/delivered**, with immutable Identity evidence. Relay #27/#33 and actual Mindgarden historical/consumer acceptance remain distinct. Do not carry the earlier broad unavailable-collector assumption into #44.
