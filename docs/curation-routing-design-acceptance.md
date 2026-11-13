# Curation, routing and design acceptance — 2026-11-13

The maintainer authorized merging #142 → #143 and selected #13 → #14 → #38
next. Live issue bodies and comments, their actual implementations and proposed
ADRs were read before extending the engine. This audit retains all twelve #13
criteria **and its seven later extraction requirements**, all ten #14 criteria
and all seven #38 criteria. It does not substitute a smaller checklist.

## Merge receipt and current disposition

| PR | Exact qualified candidate head | Merge commit | Passing automatic Test / preparation |
| --- | --- | --- | --- |
| [#142](https://github.com/egohygiene/mindgarden/pull/142) | `eecb69b158abb4617938eb40b095cbc00c014088` | `0fbf153916a00c668af6c6bc85d06d06dd6bd416` | 43370663295 / 43370663318 |
| [#143](https://github.com/egohygiene/mindgarden/pull/143) | `846cd765bafee4804941dba19ea623b1fbf4e105` | `6c9954bfa8ac65c94aa1db87c679a66227f736d8` | 43374246462 / 43374246517 |

Both were merged in order with expected-head checks after refreshing discussions,
reviews and review threads (all empty). #143 was retargeted to main after #142.
`git diff --exit-code 846cd765bafee4804941dba19ea623b1fbf4e105 origin/main`
passed. That proves tree equality; the earlier
[mock qualification](evidence/mock-garden-qualification.json) supplies runtime
evidence. No workflow was manually dispatched and no history was rewritten.

| Issue | Disposition | Exact next action |
| --- | --- | --- |
| #13 | Partial: existing authored/recorded extraction workflow; this draft fixes discarded-candidate history in composed routing | Review the fix, then run the existing synthetic-only Ollama evaluation with an explicitly selected available local model; no live model accuracy is claimed |
| #14 | Partial: explained routing, reviewed private lifecycle/reference repair and local recovery; this draft retains history-only decisions and proves renamed physical mounts | Review the local fix; public/policy-changing transitions still need the policy/decision gate and their own recovery proof |
| #38 | Completed and closed against its seven listed criteria on already merged main | Future consumers/accessibility belong to #17/#47; ADR-0014 disposition belongs to #42 |

There are **34 open issues / 44 tracked rows / ten closed rows**. Only #38 was
closed by this acceptance audit. The new code remains a reviewable draft; #13 and
#14 remain open. [The coverage ledger](open-issue-coverage.md) preserves all rows.

## Dependency corrections and boundaries

- Multi-target proposals compose the existing `curation-plan/v1` inside
  `routing-plan/v1`. Curation owns selection, transformations, evidence and review;
  routing owns destinations, one canonical home, references and group recovery.
  A competing multi-garden curation schema is unnecessary. The corrected private
  history path is a missing integration between those existing contracts.
- #14 consumes #13's implemented authored-plan contract. It does not require live
  model accuracy or closure of the whole extraction parent before testing routing.
- The local Ollama wire helper, recorded producer, resume protocol and complete
  synthetic archive/bookmark/page proof already exist. Offline tests are not a
  substitute for #13's actual local-model evaluation. `ollama` is not on PATH and
  no operator-selected installed model is supplied here. No model is downloaded,
  no hosted service is called and no private evidence is sent to a provider.
- Initial public placement has explicit review and publication gates. Existing
  lifecycle operations deliberately require matching ordinary personal policies.
  The broader public/policy-changing transfer follow-up remains owned by #14,
  proposed ADR-0022 and the #29/#42 policy/decision process. Passing private
  recovery tests supplies neither declassification authority nor wider filesystem
  durability assurance.
- #38's former ledger gates (human design disposition, more consumers and full
  accessibility) exceeded its actual design-source criteria and explicit non-goals.
  Closure corrects that ledger, without accepting ADR-0014 or claiming full WCAG.
  All 24 ADRs retain proposed status and null approval.

## New bounded implementation

Previously `route` marked output-less candidates `history-only` and skipped
curation. With only exclusions/deferrals it produced no persisted record. In a
mixed request their exact rationale/evidence could be lost when only the routed
outputs were retained.

The router now invokes the existing curation service for each such candidate and
stages its ordinary `curation-receipt/v1` in the explicitly catalogued **personal
controller** from the embedded proposal. The routing receipt also retains the
history-only decision and inherits the disposition's scope. Preferred public
destinations do not receive discarded metadata. Missing, public or organization
controllers fail with `ROUTE_HISTORY_PRIVATE`; undeclared receipt capabilities
and invalid source selectors fail before writes. A missing fallback never becomes
an implicit public destination.

This shares the same digest, target fingerprints, exact source checks and
recoverable group cutover as kept outputs. Repeating an identical request is a
no-op; changed reasons/evidence invalidate the reviewed digest. Originals, vault
objects and existing records are retained. No new schema, dependency, provider,
execution permission or publication authority is introduced.

[Five committed authored cases](../tests/fixtures/curation/disposition-cases.json)
cover scratch, duplicate, corrupted, low-information and unsafe material. Each
selects an exact line/hash. Corrupted here means unusable captured text; actual
hash corruption still fails integrity checks. No semantic classifier is claimed.
The mixed public/private test injects failure at the second destination, proves
all-original rollback, retries, and checks public bytes for private canaries and
discarded identities. The renamed-mount test moves an already routed private
garden, changes only local bindings and retains the exact logical home, evidence,
search result, source objects and idempotent lifecycle replay.

## #13 original acceptance map

| Listed criterion, in issue order | Evidence and remaining scope |
| --- | --- |
| 1. Versioned plan/decisions | `contracts/v1/curation-plan.schema.json`; schema and CLI tests |
| 2. Exact spans/hashes | Curation source selectors and represented revisions; stale selector/hash negatives |
| 3. Discard reasons, no public sensitive metadata | Existing private curation receipts; **draft integration fix** for routing history; mixed public canary test |
| 4. Five explicit disposition categories | New authored fixture and routing-disposition tests; classification is supplied, never inferred |
| 5. Valuable diagrams independently selected | `tests.test_archive_diagrams`, `tests.test_mixed_curation`; binary/caption retained, scratch remains unselected |
| 6. Multiple gardens, no raw archive copies | Embedded curation/routing composition; three-garden routing fixture and separately reviewed mixed-media move |
| 7. Private fallback | Routing ambiguity/sensitivity policy and absent-fallback negative fixtures |
| 8. Agent notes unreviewed | Curation and extraction tests; applying proposals supplies no human review |
| 9. Plan validation/preview | `gardenize --plan`; authored proposal, exact evidence, target and capability checks |
| 10. Reviewed digest, atomic non-overwrite apply | Curation stale/conflict fixtures and shared staged validation/cutover; routed group failure/recovery tests |
| 11. Archive instructions are data | Archive trust labels; source instructions never select handlers; synthetic pipeline blocks network/process execution |
| 12. Keep/discard/merge/redact/multi-route/fallback/conflicts | Committed authored plans and transformation, mixed-media, routing and complete pipeline golden fixtures |

## #13 later extraction requirements

| Listed requirement | Evidence and remaining scope |
| --- | --- |
| 1. Optional separately versioned producer | `extraction-request/v1`, `extraction-output/v1`, `ExtractionProducer`; recorded adapter and existing CLI |
| 2. Subject/predicate/object/context mapping | [Mapping](extraction-producers.md); existing IDs/claims/synapses only; ambiguous/unknown output remains unresolved |
| 3. Exact evidence and producer revisions | Exact unit locators/input hashes, available message/speaker/time metadata and extractor/model/prompt/schema revisions in private batch/curation rationale |
| 4. Attribution, uncertainty, negation, time, conflicts and reviewed alias merges | Extraction qualification tests, mixed/quoted assistant fixtures; no automatic name-based merge; authored merges retain exact inputs/rationale/review |
| 5. Validated, distinct empty/failed/partial/unsupported/invalid states | `tests.test_extraction`; recoverable work and sanitized fixed-code diagnostics |
| 6. Bounded digests/checkpoints/resume | Interrupted/resumed batch fixture; zero replay of completed unchanged units; accepted-plan apply is deterministic, model reruns are not assumed identical |
| 7. Actual local Ollama evaluation | Pure official-API wire helper, schema tests and synthetic dry-run exist; **live model evaluation remains unavailable and unmeasured** |

The issue's first bounded archive + bookmarks + captured page proof is already
executable in `scripts/pipeline_completion_demo.py`. Its committed golden includes
eight proposals, ambiguity, attributed assistant suggestion, contradiction,
interruption/resume, separate human review, canonical typed graph/search, exact
message evidence, bounded context and vault relocation/restore/clean rebuild.
The same proof is rerun in the focused acceptance selection. It is not evidence
of model accuracy or a real consumer's approval. See the
[existing full proof](pipeline-completion-proof.md).

## #14 acceptance map

| Listed criterion, in issue order | Evidence and remaining scope |
| --- | --- |
| 1. Catalog/routing schemas | `garden-catalog/v1`, `routing-plan/v1`, lifecycle v1/v2 and independent reference-repair contracts |
| 2. Evidence/confidence/policy/rejections | Authored curation evidence plus explained route preview; three-garden fixture |
| 3. Reviewed digest/all target contracts | Source/config/target checks, read/write capability validation and non-overwrite negatives |
| 4. Missing fallback unresolved | Existing `route --check` fixture returns contract failure, with no inferred public destination |
| 5. Explicit public review/allowlists | Public source review, human publication review and target allowlists; private source/rejected metadata leak negatives |
| 6. Independent units from one source | Three candidates resolve to private, repository and organization homes; duplicate request replay is deterministic |
| 7. Stable garden/artifact references | Canonical exact IDs/revisions; cross-garden reference records and renamed physical-mount proof |
| 8. Duplicate/move/rename/split/merge/supersede | Supported private lifecycle, lineage, alias/history and repair tests; **broader public/policy-changing transfers remain open** |
| 9. Atomic failure/recovery | Group cutover, partial failure, retained backups on failed rollback, explicit recovery, retry and two-owner repair tests; local single-writer proof only |
| 10. Synthetic repo/org/private fixtures | Existing four-kind fixture; no real private repository or account needed |

## #38 complete acceptance map

| Listed criterion, in issue order | Merged evidence |
| --- | --- |
| 1. Purpose/scope/consumers | `design/README.md` explains independent source and optional consumers |
| 2. Valid JSON tokens | `design/tokens/mindgarden.tokens.json` |
| 3. Schema validates tokens | `design/schemas/design-tokens.schema.json`; schema/contrast tests |
| 4. Botanical/cybernetic style | `design/references/mindgarden-visual-style.md` |
| 5. Banner and architecture prompt references | `design/prompts/image-generation-style.md`, `design/prompts/diagram-generation-style.md` |
| 6. Optional documentation link | Root README links the design source without requiring design tooling |
| 7. No generated binary required | The unchanged loader/exports read only token/schema JSON; this draft adds a temporary two-file conformance case |

The complete source already exists at merged main `6c9954b`. New proof tests do
not supply a missing runtime feature. Closing #38 does not ratify its proposed
ADR, require another consumer or claim a full accessible private application.

## Verification and recovery handoff

Baseline: 72 focused cases passed on Python 3.12.14 (92.560s) and 3.13.5
(88.768s), zero skips. First new selection: one test expected the later
`CAPABILITY_UNDECLARED` diagnostic while its catalog was stale, so the earlier
`ROUTE_CATALOG` guard correctly failed it. The fixture now updates both explicit
contracts before checking the undeclared capability. Corrected selection: all
15 cases pass on both Pythons (13.382s / 12.790s), zero skips.

The complete focused selection passes **84 tests per Python, zero skips**:
3.12.14 in 139.909s; 3.13.5 in 136.288s. It includes the existing complete offline
pipeline golden after relocation, restore and clean rebuild. Exact commands:

```sh
/workspace/mindgarden/.venv/bin/python -m unittest tests.test_curation tests.test_curation_transformations tests.test_mixed_curation tests.test_routing tests.test_routing_dispositions tests.test_routing_lifecycle tests.test_routing_transfers tests.test_routing_incoming tests.test_reference_repairs tests.test_assets tests.test_design tests.test_extraction tests.test_ollama_extraction tests.test_archive_diagrams tests.test_pipeline_completion --quiet
/workspace/mindgarden/.cache/python313/bin/python -m unittest tests.test_curation tests.test_curation_transformations tests.test_mixed_curation tests.test_routing tests.test_routing_dispositions tests.test_routing_lifecycle tests.test_routing_transfers tests.test_routing_incoming tests.test_reference_repairs tests.test_assets tests.test_design tests.test_extraction tests.test_ollama_extraction tests.test_archive_diagrams tests.test_pipeline_completion --quiet
```

The new history-only test was also run against the original merged routing module
in an isolated Python namespace: it fails because there are no private history
changes, reproducing the gap without changing the checked-out file. Scoped Ruff
and formatting for the new test, `compileall -q src tests`, pinned owner checks
and `git diff --check` pass. The Ollama dry run uses the deliberately fictional
`synthetic-wire-probe-not-installed` identifier and records `accuracy: unmeasured`.
It makes no provider call and selects no real model.

The final artifact/checkpoint receipt records subsequent packaging and exact-head
CI observations separately. Full local/`act`, manual accessibility,
actual private pilot, actual model quality, public/policy-changing transitions and
release work are separate and remain unperformed. No real source/credential is
read and no proposed ADR is accepted by this draft.

Next: review the draft fix and acceptance mapping; use the recorded exact combined
checkout. Then continue independent #37 → #46 → #90 synthetic freshness/mapping
work after the selected batch is synced. The mock garden and its unapplied
correction remain reusable data; this checkpoint does not import that correction.
