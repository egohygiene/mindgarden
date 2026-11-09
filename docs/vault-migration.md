# Reviewed local vault adapter migration

Refs #45. This extends the existing content port and machine-local bindings;
canonical source records, logical vault IDs and immutable content IDs do not
change. The source store is retained. Encryption, remote providers, destructive
retention and full parent acceptance remain unavailable.

## Contract and control boundary

`mindgarden.vault-migration-plan/v1` binds both configuration files, both adapter
capability descriptions, every inventoried source object and represented garden
revisions. Its output contains hashes and logical identities, never machine
paths, credentials, original filenames or source text. The plan is private
owner control state with `publication: never-exportable`.

Both configurations name the same logical vault ID. The target must already be
initialized at a distinct private local root. Configurations use the existing
owner-only controls (0700 directories, 0600 regular files), without symlinks,
canonical garden overlap or Git-tracked storage. No target is initialized or
provider installed implicitly. Registration/capabilities alone grant no runtime
or publication authority. Restricted gardens and remote/encrypted ports are
refused; no local flag is a confidential-runtime proof.

The source must support complete audit and reads; the target must support
immutable put and reads. The core checks actual bytes against their SHA-256 and
size independently of provider checksum claims. Advertised audit/export/restore
capabilities require the corresponding callable methods. Factory arguments are
isolated from the caller's binding dictionary. Provider implementations remain
explicit trusted code, not a plugin sandbox.

## Plan, apply and recovery

Prepare a target through its existing explicit initialization workflow, then:

```bash
mindgarden vault migrate --local-config "/private/controls/source.json" \
  --target-local-config "/private/controls/target.json" \
  --vault-id "source-vault" --plan
mindgarden vault migrate --local-config "/private/controls/source.json" \
  --target-local-config "/private/controls/target.json" \
  --vault-id "source-vault" --apply --plan-digest "REVIEWED_PLAN_SHA256"
mindgarden vault audit --local-config "/private/controls/source.json" \
  --vault-id "source-vault"
```

Copy every source-inventoried object, including unreferenced originals. Existing
target objects are verified and retained, including unrelated originals; they do
not become canonical evidence. Reopen the target independently and verify every
required object before switching the source configuration. The registry writer
lease, stale checks, private history and durable configuration replacement reuse
existing controls. Gardens, sessions, sources and the target configuration are
not rewritten. Refresh the query context after rebinding.

A failed partial copy leaves original bindings and source bytes intact. With
unchanged inputs/capabilities, rebuilding the plan produces the same digest;
repeating apply verifies existing target objects and resumes missing ones.
Corruption, changed inputs or changed authority require inspection and a new
review. There is no automatic cleanup or fallback to another adapter. An
uncertain binding commit preserves both stores; the retained application plan
can inspect/replay the exact commit and verify without opening the old provider.
After a fully committed CLI migration, use `vault audit`; rebuilding against the
already-selected target is refused rather than inventing the old reviewed plan.
The old binding remains in the existing private registry history for separately
reviewed recovery. No source store or history is deleted.

The reference supports the single-writer local baseline. Per-provider durability,
complete inventory conformance, concurrent remote transactions, actual power-loss
testing and wider native hosts require their own evidence. No cryptographic or
cloud backend is selected. Approved media copies/publication remain a different
rights/review contract from private backup and storage migration.

## Extension and synthetic proof

Application callers pass an explicit `StorageAdapters` registry to
`build_vault_migration_plan`. The CLI installs only filesystem by default.
[The synthetic extension](../tests/migration_fixture.py) wraps actual local
filesystem storage with a different adapter ID, proving the boundary without
modifying the core domain. It is not a Google/S3/encrypted-provider implementation.

```bash
python scripts/vault_migration_demo.py --workspace /tmp/new-migration-proof \
  --require-source --report /tmp/migration-proof.json
```

The [committed golden](../tests/fixtures/assets/migration-proof.json) covers a
partial copy, same-digest retry, exact canonical/index/context/source reference,
return to the original adapter, extension removal and a clean backup restore.
Networking, HTTP and external process entry points are blocked in-process;
Google/models are unused. This is application behavior, not host isolation.
Exact qualification is in [the sprint ledger](privacy-storage-followthrough.md).
