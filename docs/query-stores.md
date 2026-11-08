# Optional local query stores

The dependency-free JSON/reference engine stays the default. `query-store` is an
opt-in SQLite FTS5 conformance candidate under proposed ADR-0016, not permanent
store adoption. Canonical Markdown/JSON and original source vaults never live in
this database. Removing a cache cannot remove knowledge.

The `mindgarden.query-store/v1` port accepts an already authorized v1 index, its
exact scope digest and live-authority callback. It exposes rebuild plans, lexical
query, typed traversal, backlinks, audit and portable logical backup. Capabilities
explicitly report no vectors, encryption or incremental updates. A new incompatible
store version needs a separate cache/rebuild; in-place database migrations are not
supported. The public `QueryStore` Protocol is independent of SQLite locations.

Use a new absolute private directory outside Git and canonical gardens:

```bash
mindgarden query-store --local-config "/private/bindings.json" \
  --scope "/private/session.json" --cache-directory "/private/query-cache" \
  --operation plan
```

Inspect its `plan_sha256`, then repeat with `--operation build --plan-digest` and
that exact digest. Search uses `--operation search --query "procedure"`; graph
uses `--operation graph --target "garden/knowledge-id" --depth 2`; backlinks use
`--operation backlinks --target "garden/knowledge-id"`. Every operation opens live
session authority and rebuilds the authorized reference view before opening cache
bytes. Expiration/revocation or changed authorized records deny reuse. Generated
results retain exact sources, review, effective scope, represented inputs and the
reference scoring reasons. Final output rechecks authority and byte budgets.

FTS stores hex-encoded reference tokens so Unicode/hyphen behavior matches the
reference tokenizer. It finds candidates; the existing explainable scoring formula
and stable tie-break produce final order. The typed view and backlinks preserve
the already filtered edges. No provider/model/network service is involved.

`audit` checks ownership, exact scope/input, database checksum, SQLite integrity,
metadata, records, lexical tokens and typed edges. Missing, unavailable FTS,
unowned, stale, incompatible, corrupted and locked states use fixed diagnostics.
Unknown files and corrupted databases are retained. Builds prepare a separate
database, verify live inputs again, then replace only a verified owned cache;
replacement failure restores prior state.

`backup --backup-file "/private/query-backup.json"` writes a new private logical
backup, never overwriting one. `restore` requires that backup to equal the current
explicitly authorized projection and applies a freshly reviewed normal build
plan into the selected cache. A stale/revoked backup cannot regain authority.
`reset-plan` / `reset --plan-digest` quarantine the exact owned cache under a stable
recovery identity. They never delete unknown files or canonical content. Recovery
can rebuild from sources or restore the logical backup into a new location.

Ten focused tests pass in the final combined suite on Python 3.12/3.13, including exact ranking/evidence,
Unicode, graph/backlinks, scope/plan staleness, pre-cache expiration denial,
backup/restore/reset, corruption, symlinks, unowned files and failed replacement. The compatibility follow-up also proves that missing
SQLite preserves unrelated CLI commands and a conforming store factory can be
injected without changing the core domain.

```bash
python3 scripts/query_store_benchmark.py \
  --workspace "/tmp/new-synthetic-query-proof" --notes 256
```

The committed [Linux observation](../tests/fixtures/query-store/observed-linux.json)
uses 256 notes plus one claim: authorized index 1.814206 s, cache build 0.900269 s,
reference ranking 0.000487 s, audited SQLite search 0.050309 s and 1,261,568 database
bytes. This bounded adapter is slower when every request fully audits/reconstructs
its authorized view; it is parity/recovery evidence, not a performance win or
large-corpus guarantee. Incremental invalidation, broader workloads/resources,
native platforms, confidential Realm runtime and accepted store disposition
remain parent #32 scope. No new runtime dependency is installed.
