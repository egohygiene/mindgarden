# Private bookmark cleanup checkpoint

The local private cleanup command accepts legacy normalized JSON and the pinned
Mindcap v1 captured-source handoff through the same explicit review workflow.
The captured-source adapter verifies exact package membership, bytes, checksums,
raw lineage and evidence selectors before bookmark cleanup reads normalized units.
It does not import Mindcap, visit a URL or mutate a browser.

```bash
mindgarden bookmarks --classification personal \
  --input-format captured-source-bundle \
  --input "/private/captured-bookmarks.zip" --catalog "/private/url-selection.json" \
  --inspect --plan-file "/private/review/inventory.json"
```

The format is selected explicitly; the default `normalized-json` preserves the
older command. The bounded normalized fields follow Mindcap
`ce5f709990e82f6e8bd14fe128fa2608c6a1d05b` and the captured bundle follows merged
[Mindcap #42](https://github.com/egohygiene/mindcap/pull/42), immutable source
`7ee766c1c34adad239fc602499f624979a2d9cac`. This is tested pinned compatibility,
not released-protocol adoption, producer authentication or complete #35 delta
support. Real personal execution still waits for the owning accepted contracts.

## Compatibility and external gates

| Interface | Verified state |
| --- | --- |
| Mindcap normalized Chrome bookmark metadata v0.1 | Tested bounded fields: schema, provider, profile/provider identity, title, URL, folder list, source JSON locator; preserve complete input bytes |
| Mindcap v1 provider-neutral bundle / #35 deltas | Verified exact bundle and metadata evidence; deltas/deletion remain unavailable |
| Mindcap draft #37 at `d568285c3089f690b345029ed88eeda749327b99` | Separate capture/manual-review helper inspected; it explicitly leaves #35 handoff/incremental work open. No code copied |
| Local comparison catalog | Explicit `mindgarden.local-bookmark-catalog/v1` URL selection; exact-string comparison only, not an Akashic canonicalization contract |
| Akashic #173 freshness observations | Unavailable integration; observed-redirect proposals remain deferred, never guessed or fetched |
| Akashic #174–#176 sanitized publication / public Garden | No accepted packet schema delivered at inspected main `caeaf6bbe519701110ffda3888d2ee49898c52ec`; both approved and unapproved proposals stay local |

A stable local identity derives from supplied provider/profile identity. Missing
or conflicting identities require reconciliation. Bundle IDs instead derive from the full producer-supplied source-unit identity;
normalized digests and raw observation lineage remain separate. Snapshot-local
identity stays labeled and is never promoted to a cross-export guarantee.
Bookmark metadata records a saved link, not a read, endorsement, factual claim or
captured page body. No URL, Chrome profile or Google account is visited or changed.

## Local review flow

The baseline requires explicit personal classification. The default is restricted
and denies processing before opening source bytes because confidential-runtime
assurance is unavailable. All controls and exports use owner-only private paths
outside Git/canonical gardens; ordinary CLI output contains only status/digests.

```bash
mindgarden bookmarks --classification personal \
  --input "/private/captured-normalized.json" --catalog "/private/url-selection.json" \
  --inspect --plan-file "/private/review/inventory.json"
```

The inventory supplies stable record IDs and exact source/catalog hashes. Author a
`mindgarden.bookmark-review-request/v1` with explicit human review, source/catalog/
policy digests, offset/limit (at most 50) and one disposition per selected record.
Keep, merge, move, rename, quarantine, defer, private-route, publish-proposal and
omit are explicit. Observed-redirect is retained as deferred until its actual
observation contract is integrated. URL safety screening is conservative and
offline; unknown availability never means a resource is dead or deletion-ready.

```bash
mindgarden bookmarks --classification personal \
  --input "/private/captured-normalized.json" --catalog "/private/url-selection.json" \
  --request "/private/review/request.json" --plan-file "/private/review/plan.json"
```

Inspect the private plan. Apply with `--apply --output-directory
"/private/new-cleaned-export" --plan-digest "<reviewed-exact-digest>"`. Changed
inputs, catalog, policy, request or prior receipt invalidate application. Exact
replay verifies output; existing different output and unknown files are retained.

Exports preserve the exact normalized input, reviewed decisions, source JSON
locators, quarantine/defer reasons and cleaned JSON/Netscape HTML for **manual**
browser import. Private/internal, credential/session and executable URLs remain
in private quarantine instead of the importable HTML. Moves/renames affect only
this export. Exact duplicates require explicit merge into one retained home.
Catalog membership is comparison evidence, not publication authority.

Resume using the emitted `review-receipt.json`, its exact digest in the next
request, `next_offset`, and `--previous-receipt`. The next human-reviewed digest
covers cumulative dispositions and complete regenerated exports. Changed source/
catalog requires fresh reconciliation. The original normalized file and prior
bundles remain available for rollback/re-export; no browser deletion is performed.

`akashic-handoff-status.json` contains a fixed unavailable/denied contract state
and no candidate identities, URLs, folders, profiles, counts or source hashes.
Per-item approval is recorded privately; it cannot manufacture an accepted public
packet. No Akashic branch, PR, catalog edit or upload is performed. Consumer-side
publication, canonical URL aliases/freshness, raw capture/delta verification and
actual ingestion/routing remain parent #48 scope.

Seven cases pass on both supported Pythons. Synthetic fixtures cover duplicates,
moves/renames, redirect and intermittent-failure deferrals, internal URLs,
bookmarklets, mixed publication approvals, malformed/ambiguous identity, staleness,
resumable batches, deterministic no-overwrite export, escaped HTML and redacted CLI
summaries. This is the explicit supported local checkpoint, not full #48 completion.
ADR impact: existing private capture/curation/publication ownership is preserved.


## Verified bundle and reviewed graph checkpoint

A private inventory/plan carries the exact package digest and capture status.
Each item retains logical source-unit identity, normalized byte digest, title/URL
JSON locators, the original normalized member selector and exact raw-member
checksums. The private export includes the **unchanged original ZIP**, cleaned
JSON/HTML, decisions, quarantine and receipt. Total output is bounded to 16 MiB;
larger exports fail at planning. No original is rewritten or deleted.

A later capture can have the same normalized identity/content and different raw
observation hashes. The old approval is still invalid because its exact package
changed. A partial capture never reports `complete_review: true`, even when all
available items have dispositions. Checksums verify byte integrity, not producer
identity or browser-capture completeness. Neither a saved URL nor its title is
proof of reading, endorsement or target-page truth. `page_content: not-captured`
is explicit; independently captured page text keeps its own source identity.

[The real producer receipt](evidence/bookmark-capture-cleanup-proof.json) uses two
actual Mindcap synthetic captures with networking blocked. Both observations
produce equal normalized bytes and stable cleanup IDs/evidence, while distinct
raw packages and observation lineage remain preserved. The optional experiment
imports the pinned producer only in its disposable verification environment;
ordinary engine/tests need no Mindcap installation.

Seven new regression cases cover exact inert evidence, overlapping observations,
malformed/wrong-kind/missing-selector packages and format spoofing, partial
capture, private CLI apply/replay/staleness and denial before source access.
A source→curation→graph case proposes a bookmark topic alongside a conversation
item, keeps it unreviewed, then explicitly approves a typed `references` link and
rebuilds exact graph/index output. The link is an authored topical connection;
it asserts no uncaptured page claim and leaves original vault bytes unchanged.

#48 remains open for accepted Akashic identity/intake/public projection contracts,
a complete independently approved public journey and producer-owned deltas.
There is no synthesized Akashic packet or remote draft-PR write. Next action:
provide the accepted owner wire contract, then add a separate sanitized exporter.


Producer reproduction (supply the pinned Mindcap checkout/environment, not a real
browser profile):

```bash
PYTHONPATH="<mindcap-checkout>/src:src" "<mindcap-env>/bin/python" \
  experiments/capture_handoff/check.py \
  --fixture-directory "<mindcap-checkout>/tests/fixtures/chrome_bookmarks/multiple_profiles/User Data" \
  --report "<new-private-report.json>"
```

Verification used the exact producer commit above, two synthetic records per
observation and no model/Google access. Core regression command and timings are
recorded in [the overnight ledger](overnight-sprint.md).
