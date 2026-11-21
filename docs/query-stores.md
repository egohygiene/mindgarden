# Optional local query stores

The dependency-free JSON/reference engine stays the default. `query-store` is an
opt-in SQLite FTS5 conformance candidate under proposed ADR-0016, not permanent
store adoption. Canonical Markdown/JSON and original source vaults never live in
this database. Removing a cache cannot remove knowledge.

The `mindgarden.query-store/v1` port accepts an already authorized v1 index, its
exact scope digest and live-authority callback. It exposes rebuild plans, lexical
query, typed traversal, backlinks, audit and portable logical backup. Capabilities
explicitly report no vectors or encryption. The optional SQLite adapter now supports
reviewed incremental refresh and copy-and-verify migration from known database
version 1 to version 2; unknown formats require a separate rebuild. The public `QueryStore` Protocol is independent of SQLite locations.

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
large-corpus guarantee. Broader workloads/resources, native platforms, confidential
Realm runtime and accepted permanent-store disposition remain later work; they
are not additional gates for #32's ordinary local baseline. The
[acceptance reconciliation](acceptance-reconciliation.md) includes the original
incremental-refresh/migration requirements. No new runtime dependency is installed.

The optional [CozoDB evaluation](evaluations/cozodb.md) uses this port in a
removable lab. Its native dependency, recommendations and unsupported installed
restore dispatch do not alter the default reference/SQLite contract.


## Reviewed refresh and schema evolution

Use `--operation refresh-plan`, inspect its `plan_sha256`, then repeat with
`--operation refresh --plan-digest SHA256`. The plan binds the complete current
authorized index, current session digest, exact prior owned-cache inventory and
operation. Renewed session/revision authority is checked before opening the cache.
Prior records are disposable acceleration material, never authority: the adapter
selects old row digests only for currently authorized IDs and verifies the complete
staged result against the freshly built reference view. It returns no prior-only
record IDs, titles or counts. Changed plans and changed caches fail closed.

Refresh copies the verified owned database, leaves unchanged record/lexical rows
untouched, updates changed rows, removes absent rows, reconciles typed edges and
replaces represented metadata. It consolidates FTS segments and vacuums the staged
copy before verification/publication. This is not a forensic erasure guarantee for
storage media, retained backups or operating-system snapshots. Every query still
uses live reference authority and exact audit; neither a cache nor its former
session can grant access. Expired/revoked authority is denied before cache access.

Database version 2 adds canonical per-record content digests. Version 1 remains
readable; explicit rebuilds can always replace known owned generated state. To
migrate without overwriting the original, use a **new** cache directory:

```bash
mindgarden query-store --local-config "/private/bindings.json" \
  --scope "/private/current-session.json" \
  --previous-cache-directory "/private/old-query-cache" \
  --cache-directory "/private/new-query-cache" --operation migration-plan
```

Review its digest, then use `--operation migrate --plan-digest SHA256` with the
same inputs. The source must match the current authorized projection and known
version-1 layout exactly. Unknown schemas, stale inputs, corrupt/unowned/symlinked
state and incompatible private boundaries are retained and rejected. Source and
destination are separately locked. The stage adds/backfills row digests, upgrades
the database version and passes exact integrity/reference verification before it
is selected. The source remains byte-identical; exact successful retry is a no-op.

Both operations prepare separately, recheck live authority and source/cache
inventory before publication, and preserve prior state on failure. A replacement
failure normally restores the prior cache. If restoration also fails, a fixed
`QUERY_STORE_RECOVERY` diagnostic leaves the `.query-store-prior-*` directory
beside the destination intact for explicit local recovery; it is never deleted by
cleanup. Inspect it with the ordinary adapter, or rebuild/restore into a new
location. No automated recovery overwrites unknown files or canonical gardens.

Logical backups stay independent of physical schema versions. A current authorized
backup restores through the reviewed normal build path into a clean version-2
cache. Cache plans have their own closed [schema](../contracts/v1/query-store-plan.schema.json).
The port extension is capability-gated; other optional adapters can continue to
report refresh/migration unsupported.

`tests/test_query_store_evolution.py` covers actual canonical change/session
renewal through CLI, deltas, reference/typed parity, withheld historical canaries,
plan/source staleness, interruption, failed rollback, version-1 migration and retry,
logical restore, corruption/unknown versions/files, expiry and revocation. The
[sprint ledger](pipeline-integration-sprint.md) records exact current verification.

The [new instrumented Linux observation](../tests/fixtures/query-store/observed-refresh-linux.json) covers 256 notes plus one claim and one canonical title change. With `tracemalloc` enabled, build took 14.133780 s, refresh planning 0.090788 s, refresh apply 13.932253 s, and Python peak allocation was 20,244,021 bytes. Current authorization/index generation took 22.300901 s. These timings include tracing and full input/audit work; they are not directly comparable to the older uninstrumented observation and do not establish a speed improvement, RSS limit or scaling guarantee. Reproduce with `python3 scripts/query_store_benchmark.py --workspace /tmp/new-private-query-proof --notes 256 --refresh`.
