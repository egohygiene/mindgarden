# Merged implementation and acceptance reconciliation

The maintainer selected steps 1–3: merge #148–#154 in order, reconcile the full
#16/#32/#90 requirements, then finish #15 importer acceptance. Step 4, #17 garden
browsing, waits for a sync. Local Mac/Drive setup, actual private/model/Empathy
proof, releases and proposed ADR disposition stay separate.

## Merged stack

Main is `5cf24a29002f8e4f0a464b42819ec21ede33af2a`. All seven exact PR heads
had passing automatic Test/preparation runs and no review comments, submissions
or threads to resolve. Each merge preserved its tested tree; final main is
byte-equivalent to the combined `c7eaa51` checkout. The
[merge receipt](evidence/pipeline-stack-merge.json) records all heads, CI runs,
original bases, merge commits and tree comparisons. No workflow was dispatched
manually. Earlier draft/pending-CI observations are historical.

The reconciliation branch is `test/16-32-90-15-acceptance`, directly on merged
main. Its changes add acceptance fixtures/tests and documentation; application
code, contracts and canonical formats are unchanged. New evidence and its review
state are separate from already merged implementation.

## #16 — all 13 federation criteria

| Listed requirement | Implementation and executable proof |
| --- | --- |
| Versioned stable garden descriptor | `contracts/v1/federation-descriptor.schema.json`, `domain/federation.py`, `tests/test_federation.py` |
| Reviewed-public indexes, graph and counts | Public selection/inheritance before bodies; private canaries in `tests/test_federation.py` |
| Immutable revisions or artifacts | Descriptor/content checksums and exact rendered revision pins; stale/corrupt negatives |
| Deterministic multi-descriptor catalog | Ordered multi-garden fixtures and clean/relocated rebuilds in `tests/test_federation.py` |
| Duplicate/stale/incompatible/unavailable/conflicting homes | Catalog quarantine and fixed diagnostics in federation/rendered tests |
| Canonical links, no copied note bodies | Catalog assertions and exact rendered-route membership |
| Unadvertised private/internal local federation | `tests/test_local_federation.py`, selected healthy peers and local policy cases |
| Agent instruction boundary and provenance | Data-only entrypoints/bundles with exact source references |
| Progressive catalog → scope → bounded retrieval → context | `tests/test_public_bundle_context.py`, supplied verified inputs and current session authority |
| Item scope, revision, inclusion reason and budgets | JSON/Markdown context checks, denied counts, byte/item limits |
| Independent Aether tool/session authority | Catalog/producer assertions grant no read/write/tool authority; live revocation/expiration cases |
| Multi-garden aggregation, isolation and incremental refresh | Federation/rendered fixtures, unavailable peers, explicit refreshed pins and old-only metadata canary |
| Framework-independent contract | Ordinary schemas/services, data-only rendered inputs; no framework/server requirement |

The #151 old-only metadata fix is merged. The required artifacts (`garden.json`,
knowledge index, synapse graph, stable/source URLs, `llms.txt`, compatibility,
revision/checksum/freshness metadata) are exercised by the federation fixtures.
Checksum binding is explicitly permitted; signatures, remote acquisition, hosting
and optional sitemap/feed are not added closure gates. Actual Akashic #176 and
Aether #69 pilots remain with their owners. Closure does not approve ADR-0011.

## #32 — complete local baseline contract

| Listed requirement | Implementation and executable proof |
| --- | --- |
| Versioned replaceable port | `domain/query_store.py` Protocol/capabilities and injected conforming factory test |
| Canonical/generated ownership | Canonical files/vault stay outside the owned cache; reset/recovery fingerprint assertions |
| Deterministic pinned rebuild | Exact authorized index, scope/input pins and repeatable logical backup |
| Bounded lexical/typed/backlink/provenance queries | `tests/test_query_store.py`: reference ranking/reason/evidence parity and filtered typed view |
| Scope and effective sensitivity | Current authority before cache access, current filtered index, final live/budget checks |
| Owned-only reset | Quarantined verified inventory; unknown files, symlinks and corrupt bytes retained |
| Backup/restore and schema migration | Portable logical backup plus known database-v1 → v2 copy/verify migration, exact replay and immutable old cache |
| Corrupt/stale/incompatible/unavailable states | Both query-store modules cover fixed diagnostics and unavailable SQLite/FTS capability |
| No required vectors/service/model | Reference engine remains default; optional ordinary SQLite uses stdlib and offline tests |
| Honest runtime/memory baseline | `scripts/query_store_benchmark.py`, committed 256-note observations, explicit tracemalloc/audit overhead and no scaling claim |

The full adapter body also requires incremental refresh, not just its shorter
checkbox list. Merged #153 covers digest-bound add/change/remove of rows, FTS and
typed edges, fresh authority, exact reference audit, interrupted publication and
retention when rollback itself fails. `tests/test_query_store_evolution.py` also
proves migration/restore/reset and unsupported versions. Input projection
versions/digests, claims/review/provenance/scope, explanation and portable output
are inherited from the authorized index. Runtime supplies the cache location;
paths never become portable references. Encryption/vectors are explicitly
unsupported capabilities, not silently simulated by an ordinary directory.

Permanent high-scale store adoption, bigger/native/confidential workloads and
accepted ADR-0016 disposition are later work, not unmet baseline requirements.

## #90 — all ten synthetic journey criteria

| Listed requirement | Implementation and executable proof |
| --- | --- |
| Portable exact ledger and original/configuration provenance | `ledger-csv`/reviewed mappings, exact decimal strings, ISO calendar dates, stable IDs, UTF-8 spans, immutable captures and adapter/mapping revisions |
| Overlap/duplicate/transfer/refund/missing/ambiguous handling | `tests/test_consultation.py`, CSV mapping and Drive normalization proofs: eight unique transactions from nine original occurrences, explicit pair/classification/revision choices |
| Coverage and movement limitations | Declared interval gaps/missing account retained; packet explicitly disclaims balances/assets/liabilities/completeness |
| Deterministic totals, category/time comparison and chart data | New `tests/test_consultation_periods.py`: independently authored January/February USD and February EUR rows; USD movement difference 10.14, no conversion; reproducible chart-ready series |
| Facts/classifications/hypotheses/questions and provenance | Exact rows, separately reviewed classifications, retained unresolved items and authored questions; reviewed knowledge preserves qualifications; calculation/request/configuration digests |
| Bounded Markdown/JSON packet and selected attachments | Shared `plan_packet`, overview/tables/questions/evidence, explicit normalized attachments, complete-bundle byte/row limits |
| Explicit review and denied content exclusion | Human-only review; exact source grants before bodies; scope/bundle canaries; unrelated synthetic garden content absent |
| Correction/missing-evidence invalidation and old history | Merged #149 and `tests/test_packet_freshness.py`; current/stale reasons, renewed authority, missing/corrupt/revoked failure, untouched historical packets |
| Model-disabled and optional assistant interface | Authored questions/calculations; `consultation_demo.py` and bounded research/Codex service fixtures without real model calls |
| Restore/relocate and clean reproducible output | Complete consultation and mapped Drive demo goldens rebuild exact packet/index/context/evidence through existing vault services |

The multi-period CSV and expected totals are authored synthetic inputs, not
regenerated expected answers from the calculator. `sources` selects all reviewed
calculation/evidence inputs. `selection` chooses displayed transaction rows and
does not remove a contributor from totals. Excluding a contribution requires an
explicit source-list/classification change; the new negative case proves that
behavior and the resulting evidence exclusion. No exchange rate is inferred.

Broader accounting formats, balances/assets, actual raw-PDF attachments, chart/UI
renderers and the approved real private pilot remain separately owned follow-ups.
None is an additional gate in this explicitly synthetic issue.

## #15 — importer and downstream evidence acceptance

| Original requirement | Executable evidence |
| --- | --- |
| Deterministic v2.0.1 primary package | `tests/test_archive_v2.py`, exact inventory/normalized evidence |
| Transient primary/fallback identical content | Archive v2/conversation tests; final package independently checked |
| Delivery provenance without runtime/session identifiers | Merged #152, `tests/test_archive_delivery.py`, raw private original retained, fixed withheld metadata |
| Deterministic v1.2.1 | `tests/test_archive_selection.py`, explicit legacy namespace/snapshot limitations |
| Legacy knowledge-only without bootstrap | Legacy selection/curation fixtures, no continuation invented |
| Scratch exclusion and selected diagrams/captions | `tests/test_archive_diagrams.py`, whole immutable ZIP plus independent normalization selection |
| Repeated/overlapping stable identity/hash | Archive v2/conversation tests and new attribution overlap case |
| Missing/extra/malformed/corrupt/oversized/encrypted/traversal/checksum rejection | Archive/selection ZIP adversaries, before vault writes |
| Private defaults prevent raw public content | Private source/publication-excluded assertions and source trust boundary |
| Speaker/order/available time/span/assets | Preservation metadata and exact message/asset/UTF-8 selectors |
| Normalized evidence only to curation | Existing archive → authored review → exact search/context; producer cannot self-approve |
| Synthetic fixtures | All archive members and authored cases invented; no private archive/specification body committed |
| Independent compatibility documentation | [Named versions and gaps](conversation-archive-compatibility.md) |

The September 30 graph-extraction additions now have a direct
`tests/test_archive_attribution.py` proof:

1. Exact message content locator/checksum, original ZIP member/JSON pointer/hash,
   source identity, speaker, observed/unknown time, native ID, parent and branch
   survive normalization into source evidence and extraction.
2. Authored producer outputs label the user decision, assistant suggestion,
   quotation, open question and later correction. They remain unreviewed proposals.
   A separately authored human review retains both conflicting decisions with
   reciprocal typed links and distinct exact evidence; approved search finds both.
3. Repeated and overlapping captures reuse unchanged evidence. The same message
   ID/quoted text and ambiguous “Alex” in another conversation cannot silently
   become a shared entity. Candidate IDs and citations stay separate.

`attribution-cases.json` is an acceptance recipe, not a new upstream archive
format. The test builds the already tested v2.0.2 envelope/preservation controls
and supplies recorded interpretations. It proves plumbing and review authority,
not semantic model accuracy or an actual Ollama run. The latter remains in #13.

Tested importer profiles remain v1.2.1, v2.0.0–2.0.2 source preservation and
v3.2.2/v3.2.3 full/compact continuation profiles. Collections/multipart, unspecified
aggregate wire schemas, full producer conformance, actual private archives and
Empathy acceptance are explicit compatibility/integration gaps. They do not
silently expand this named importer contract or close #20.

## Verification and exact next action

The initial four new acceptance cases pass on Python 3.12 in 32.308 seconds,
zero skips. Focused verification on both supported Pythons, packaging/data-only
checks, source comparison and live issue reconciliation follow before disposition.
The [qualification receipt](evidence/acceptance-reconciliation.json) records
source-specific commands, corrected fixture assumptions, CI and limitations.

After this checkpoint, sync with the maintainer before #17. Keep #13's actual
selected-model evaluation, #20's real private/Empathy acceptance and #41/#42's
human/shared-system decisions separate. Do not start setup, publishing or a
deferred package implementation from this handoff.
