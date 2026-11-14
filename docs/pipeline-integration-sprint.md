# Archive, query-cache and decision integration checkpoints

The maintainer authorized the next independent batch after parking local Mac
setup. Main is `270ced6`; the existing draft stack #148 → #149 → #150 → #151 is
unmerged. New work stacks on its exact `ecaca37` combined checkout. No merge,
release, provider connection, private pilot or ADR disposition is implied.

| Order | Owner | Bounded checkpoint | Remaining parent scope |
| --- | --- | --- | --- |
| 1 | #15 | Private delivery projection, exact packaging/content separation and known continuation evidence | Untested profiles, real producer/consumer integration and independent semantic curation remain explicit. |
| 2 | #32 | Reviewed incremental owned-cache refresh and supported cache migration/recovery | Permanent store choice, confidential runtime and broader performance are independent. |
| 3 | #44 | Supported typed public relationships and machine-readable composition | Historical authority, human ADR disposition and actual owner/consumer acceptance remain independent. |

Existing #11/#13 contracts support archive normalization without a model call.
Existing #12/#31 services supply live authorized indexes to optional query stores;
the database remains generated. Public ADR work can use supported shared owner
contracts without accepting #41/#42's historical or consequential decisions. Read
actual upstream inputs before extending any read-model wire format. An unavailable
contract is a recorded compatibility gap, not permission to invent it.

## Archive delivery checkpoint

Branch `feature/15-delivery-privacy` is based on #151. The reread authoritative
v2.0.0 baseline, v2.0.1 §6.2 delivery patch and v2.0.2 §6.2 require descriptive
capability labels rather than private runtime paths, session IDs, tool names or
credentials. The previous adapter copied arbitrary delivery extensions and free
text into portable capture metadata. Adapter 1.2.1 now projects only recognized
delivery facts. Unknown labels become `withheld`; fixed `metadata_withheld` codes
explain the omission without echoing values or extension keys. Free-text delivery
limitations stay in the original, with a fixed limitation in the projection.

This vocabulary is an adapter privacy policy, **not** an invented exhaustive
upstream enum. Unknown descriptive labels do not invalidate intact source content.
At most 64 attempts are accepted; malformed observations fail with fixed diagnostics
before writes. Known outcomes/creation booleans retain their independent meaning;
a successful fallback does not imply incomplete content or successful producer
validation. This is neither a general source-text sanitizer nor a certificate that
a producer complied with its full archive specification.

The immutable private ZIP retains the complete original metadata. Evidence IDs,
bytes, speakers and exact selectors do not depend on runtime labels. Both tested
v3 profiles reuse the delivery projection without claiming any new upstream format.
Known v2 continuation files and v3 full/compact continuation files remain unreviewed
summary-derived evidence, never executable instructions or knowledge approval.

Synthetic fixtures prove retained raw bytes, absent runtime canaries in records and
plan output, unchanged normalized evidence, primary/fallback parity, bounded and
malformed delivery, no execution/network use and exact continuation attribution.
The original bootstrap/legacy/selective-asset tests remain. Collections, multipart,
unknown future bootstrap formats and producer editorial accuracy are not claimed.

Verification and PR/commit observations are recorded at each checkpoint below and
in [CONTINUITY.md](../CONTINUITY.md). All broad parents remain open pending review.

### Archive verification

- Python 3.12.14 and 3.13.5: `python -m unittest tests.test_archive_delivery tests.test_archive_continuation tests.test_archive_v2 tests.test_conversation_archives tests.test_archive_selection tests.test_archive_diagrams --verbose` — **29 passed per Python**, zero skips (11.576s / 11.899s).
- Both Pythons with this checkout's explicit `PYTHONPATH=src`: `python -m unittest tests.test_private_garden_workflow tests.test_mixed_vault_workflow tests.test_release_journey tests.test_v1_contracts --verbose` — **10 passed per Python**, zero skips (48.760s / 46.644s). Whole archive/review/retrieval/context, mixed-source restore/relocation and separate public journey match exact goldens.
- New delivery module/test Ruff check passes; three selected formatted files pass; adapter compilation and `git diff --check` pass. Existing broadly unformatted files are not claimed clean.
- Golden regeneration was limited to the documented metadata hashes. A first helper invocation used the old editable engine and changed no hashes; the corrected invocation selected this exact source with `PYTHONPATH=src` and `-S`. An initial test called a nonexistent preview helper; corrected to `document()`. An initial workflow selection named a nonexistent module and disabled schema dependencies with `-S`; that invocation failed and is superseded by the exact passing ten-case runs above.
- No manually dispatched workflow, live service, private archive, publication, ADR ratification or merge. Hosted CI is reported independently after push.

[Draft #152](https://github.com/egohygiene/mindgarden/pull/152) pins functional source `b097abdff28b4ce1dff19879e7830a84b67002e6`; its documentation-only handoff is separate. Next exact action: implement #32 on the child `feature/32-incremental-cache`, preserving the unmerged stack. Hosted CI is pending; all parents stay open.


## Incremental query-cache checkpoint

Child `feature/32-incremental-cache` extends draft #152 (handoff `6679317`).
The unchanged version-1 port/logical backup now capability-gates refresh and
known schema migration. Database version 2 adds per-row canonical digests; version
1 remains readable. Refresh binds the current authorized index/session and exact
owned inventory. It updates only current changed rows, removes absent rows and
reconciles typed edges on a copied stage, then consolidates/vacuums and verifies the
complete result. Prior-only metadata is never returned or ranked. Session renewal
works without treating old cached authority as current permission.

Explicit version-1 → version-2 migration audits an exact current projection,
copies to a new separately locked cache, backfills row digests and verifies before
selection. Originals stay byte-identical. Unknown formats, stale/corrupt/unowned
state and incompatible confidential boundaries are rejected; no canonical data is
migrated. Logical backup/restore remains independent from database layout.

An additional reproduced recovery gap existed in replacement cleanup: if both
publication and rollback failed, cleanup could delete the retained prior cache.
Cleanup now preserves it and reports `QUERY_STORE_RECOVERY`; tests inspect the
retained bytes and restore their ordinary readability. Exact retry and normal
rollback are independently covered. See [the operator guide](query-stores.md).

Realm #25 was refreshed: ordinary replaceable query stores are a Mindgarden
contract; encryption, broker and confidential host assurance remain Realm/Hygiene
work. This optional adapter does not select the permanent store or ratify ADR-0016.

Verification: `python -m unittest tests.test_query_store_evolution tests.test_query_store tests.test_v1_contracts tests.test_standalone_integration --verbose` passes **30 cases per Python**, zero skips (3.12 16.315s; 3.13 15.177s). Eleven new evolution cases cover actual canonical/session change via CLI, deltas/reference/typed parity, nonleaking plans, both migration interfaces, retained rollback, interruption, restore, unknown/corrupt state and expiry/revocation before cache access. New schema passes both validators and malformed-plan cases. Selected lint/format and whitespace pass. Hosted CI and packaging are separate.

Initial schema checks exposed a wrong schema ID, then the intentionally closed
registry inventory needed its new entry/valid fixture. Those failing invocations
are not passing evidence. The first benchmark correctly rejected a workspace
inside Git; its retry uses an explicit new private `/tmp` workspace. No denied
boundary was weakened. The final measured observation is recorded separately.

The committed [256-note instrumented observation](../tests/fixtures/query-store/observed-refresh-linux.json) reports exact parity under renewed authority: build 14.133780 s, refresh apply 13.932253 s, current authorized view 22.300901 s and peak Python allocation 20,244,021 bytes. Timings include `tracemalloc`; no speed win or RSS/scale guarantee is claimed. Exact command: `python scripts/query_store_benchmark.py --workspace /tmp/mindgarden-query-refresh-20261114 --notes 256 --refresh --report tests/fixtures/query-store/observed-refresh-linux.json`.

[Draft #153](https://github.com/egohygiene/mindgarden/pull/153) pins functional source `369dc1366623c338d44efa24b0da5a0d43606aed` on #152. Its documentation-only handoff is separate. Next exact action: #44 supported public relationships on the child `feature/44-public-decision-relationships`, using the delivered shared collector contracts. No merge or parent closure.


## Public decision-relationship checkpoint

Child `feature/44-public-decision-relationships` extends #153 (docs handoff
`1a71927`). `decisions --include-related` adds current public one-hop artifact
metadata, typed source-backed edges/backlinks and explained untrusted context on
the existing read-model boundary. Cross-repository decision sources retain their
own commit/owner, while provider observations retain explicit time/null revisions.
Organization-scoped reference labels grant no inherited runtime/policy authority.

Live Relay #115 is closed/delivered; the current collector/build is available and
was not rebuilt. The actual supported Hygiene/Observatory/Relay contracts were
refreshed at exact revisions and source hashes. The native offline proof validates
the synthetic Hygiene graph, rebuilds the exact Observatory snapshot, compares the
Mindgarden golden, and exercises Relay's existing validator/Decisions renderer on
the same data. See [the guide and receipt](adr-projections.md).

The full parent still owns supported claim/component/projection relationship
contracts, private/inherited-authority integration and actual consumer acceptance.
No canonical ADR body is copied, status changed or proposal ratified. New output is
explicitly selected public metadata, with no raw producer counts or denied-target
IDs/snippets. Unsupported/stale/private targets remain withheld; ambiguous current
sources, incompatible versions and budget overflow fail closed.

Focused verification: `python -m unittest tests.test_decision_relationships tests.test_decisions tests.test_v1_contracts --verbose` passes **19 cases per Python**, zero skips (3.12 1.074s / 3.13 1.143s) before the final fixture's producer-contract/order correction. Final combined verification follows. Native owner proof initially rejected the synthetic fixture's missing generator contract, then its unsorted graph arrays; both fixture defects were corrected to the actual owner contract without weakening validation. The final explicit pinned-owner command passes, recording exact graph/snapshot/output digests. No real consumer publication or manually dispatched workflow.


Combined artifact inspection found the test SQL fixture's `.sql` extension was outside the established source-distribution manifest. It is now named `legacy-v1.sql.txt` (identical SQL bytes), using the existing supported text-fixture convention. The source-distribution inventory explicitly requires it. No release, manifest/version policy or runtime code changes; this correction propagates normally from #153 to #154 before final packaged qualification.


Hosted Test run 43648300397 at #152 docs head `6679317` completed with two stale nested goldens (650 passed/two failed of 652 on Python 3.12); native macOS jobs passed. The exact constrained correction is in the archive-version note. It changes only derived metadata-view hashes, preserving every source/vault/public/authority fact, and propagates to the children by normal merges. The follow-up five-case pipeline/reading tests and new exact-head CI are recorded separately.

Correction verification: `PYTHONPATH=src python -m unittest tests.test_pipeline_completion tests.test_reading_journey --verbose` passes five cases per Python, zero skips (3.12 75.947s / 3.13 72.789s). No runtime code changed; exact nested golden comparisons pass again.
