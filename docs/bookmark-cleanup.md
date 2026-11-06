# Private bookmark cleanup checkpoint

This local-only checkpoint consumes the bounded metadata subset of
`mindcap.chrome-bookmarks.normalized/v0.1`. The authoritative mapping is Mindcap
`ce5f709990e82f6e8bd14fe128fa2608c6a1d05b`,
[`normalizer.py`](https://github.com/egohygiene/mindcap/blob/ce5f709990e82f6e8bd14fe128fa2608c6a1d05b/src/mindcap/plugins/chrome_bookmarks/normalizer.py)
and its adjacent parser. Tests use authored synthetic metadata, not real profiles.
This is not a claim of full Mindcap archive verification or the #35 source-bundle/
delta contract. Raw capture verification and completeness remain unavailable.

## Compatibility and external gates

| Interface | Verified state |
| --- | --- |
| Mindcap normalized Chrome bookmark metadata v0.1 | Tested bounded fields: schema, provider, profile/provider identity, title, URL, folder list, source JSON locator; preserve complete input bytes |
| Mindcap #35 provider-neutral bundles/deltas | Unavailable; no invented manifest or delta support |
| Mindcap draft #37 at `d568285c3089f690b345029ed88eeda749327b99` | Separate capture/manual-review helper inspected; it explicitly leaves #35 handoff/incremental work open. No code copied |
| Local comparison catalog | Explicit `mindgarden.local-bookmark-catalog/v1` URL selection; exact-string comparison only, not an Akashic canonicalization contract |
| Akashic #173 freshness observations | Unavailable integration; observed-redirect proposals remain deferred, never guessed or fetched |
| Akashic #174–#176 sanitized publication / public Garden | No accepted packet schema delivered at inspected main `caeaf6bbe519701110ffda3888d2ee49898c52ec`; both approved and unapproved proposals stay local |

A stable local identity derives from supplied provider/profile identity. Missing
or conflicting identities require reconciliation. This does not promise the
cross-export or relocation identity guarantees still owned by Mindcap #35.
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
