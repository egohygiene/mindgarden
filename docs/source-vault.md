# Local immutable source vault

The #45 filesystem checkpoint implements `mindgarden.domain.storage.BlobStorage`
and the optional `BackupStorage` port through shared application services.
It stores immutable bytes independently from garden/source identities and never
fetches remote content, calls a model, handles credentials or deletes originals.

## Identity and compatibility

A source retains `{garden, id}`. Its immutable bytes use `sha256:<digest>`.
Physical location comes only from an explicit machine-local binding. Existing
v1 `artifact.path` references remain garden-relative. The additive alternative is:

```json
{
  "vault": {"id": "synthetic-vault", "content_id": "sha256:..."},
  "sha256": "...",
  "size_bytes": 123
}
```

Real values require complete lowercase hashes. Exactly one of `path` or `vault`
is allowed, and the content identity must agree with the artifact checksum.
The example is illustrative, not a valid fixture. Vault identifiers and private
content hashes are not public projection metadata.

`vault.json` binds the logical vault identity, filesystem adapter and format
version. Object paths are owned internal layout, never portable source locators.
Identical bytes have one stored object. Distinct proven conversation/message
identities remain distinct evidence even when they share physical bytes.

## CLI checkpoint

Use a private external `mindgarden.local-bindings/v1` file as described in
[scope and local bindings](scopes-and-local-bindings.md):

```bash
mindgarden vault init --local-config "/private/bindings.json" \
  --vault-id "private-sources" --plan
mindgarden vault init --local-config "/private/bindings.json" \
  --vault-id "private-sources" --apply --plan-digest "REVIEWED_SHA256"
mindgarden vault capabilities --local-config "/private/bindings.json" \
  --vault-id "private-sources"
mindgarden vault audit --local-config "/private/bindings.json" \
  --vault-id "private-sources"
mindgarden vault resolve --local-config "/private/bindings.json" \
  --vault-id "private-sources" --content-id "sha256:CONTENT_SHA256"
mindgarden validate --repository-root "/private/garden" \
  --local-config "/private/bindings.json" --format "json"
```

Initialization is previewed and digest-bound, refuses unowned nonempty roots,
and is idempotent. Objects are staged and linked into place without replacing
existing content, then checked on reads. Symlinks, conflicting checksums and
unknown formats fail closed. Missing bindings produce incomplete general source
validation, not successful integrity verification.

Capabilities are runtime-discovered: immutable put/read/checksums, audit,
deterministic export, clean restore and copy/verify/rebind relocation exist.
Encryption, remote storage and destructive deletion remain false. Linux is the
verified platform; other platform branches are not conformance claims. Owner-only
permissions are not encryption or runtime assurance.

## Portable backup and relocation

```sh
mindgarden vault export --local-config "/private/bindings.json" \
  --vault-id "private-sources" --output "/private/backups/sources.zip" --plan
mindgarden vault export --local-config "/private/bindings.json" \
  --vault-id "private-sources" --output "/private/backups/sources.zip" \
  --apply --plan-digest "REVIEWED_SHA256"
mindgarden vault restore --local-config "/private/bindings.json" \
  --vault-id "private-sources" --input "/private/backups/sources.zip" \
  --destination "/private/restored-sources" --plan
mindgarden vault relocate --local-config "/private/bindings.json" \
  --vault-id "private-sources" --destination "/private/relocated-sources" --plan
```

Restore and relocate apply with the same arguments plus `--apply --plan-digest`.
Preview is the default. Destination paths remain explicit local arguments; the
portable preview binds their SHA-256 descriptor, input bundle, bindings and
canonical garden revisions without emitting physical paths. Re-preview changed
inputs. Parent directories must exist and targets must be clean or identical
owned restores. Backups and original storage cannot overlap registered gardens
or other vault ownership. Existing backups and human files are never overwritten.

The `mindgarden.vault-export/v1` inventory lists content identities and sizes.
The deterministic stored ZIP contains `vault.json`, `EXPORT.json`, objects and
`MANIFEST.sha256`. The inventory covers every payload except itself; it never
self-hashes or embeds the final ZIP hash. Every completed backup is independently
reopened, member-checked, CRC-checked and checksum-checked. Links, traversal,
case/Unicode collisions, file/directory conflicts, duplicate identities, missing
and extra members, wrong vault identities and corrupt objects fail closed.

Bounds are 100 MiB/object, 4,093 objects and 256 MiB of object payload per export,
with a 264 MiB compressed-container bound. These limits are declared by the
adapter. Larger vault migration is unsupported in this checkpoint, not silently
truncated. The backup is private plaintext and includes immutable original bytes.
Keep the portable garden records alongside it: this source bundle does not back
up knowledge, review decisions or local bindings for the user.

Restore stages a complete new vault, verifies an independent re-export, then
selects it atomically at the clean destination. It does not rebind automatically;
review an external binding to the restored location. A vault-only bindings file
can restore into a clean machine without requiring the old gardens to exist.
When gardens are supplied, their declared source identities must all be present.

Relocation copies and verifies the same logical vault, then atomically updates
only the machine-local binding. Garden records and exact evidence references stay
byte-identical; the original vault remains. A failed binding update leaves both
verified copies and the original binding, allowing the same reviewed plan to retry.
An already completed identical operation is a no-op. Reload query context after a
binding change; its portable session revision can remain unchanged.

Kernel-held writer leases serialize puts and recovery operations and release on
process exit. Their private empty lease files remain beside vault roots and are
not exported. Reads verify immutable objects. Audit distinguishes a verified empty
inventory from missing expected objects by checking supplied garden references.
Unrecognized inventory state fails export; no automatic garbage collection runs.
Process-level failure and retry are tested; power-loss/filesystem recovery and
broader platform assurance remain unverified.

The tests in `tests/test_vault_recovery.py` cover reproducibility, relocation,
restore, missing/corrupt states, stale plans, unsafe/occupied targets, writer
contention and failed-rebind retry. The full #45 asset/triage, retention,
encryption/provider migration and runtime assurance criteria remain open, together
with #30 registry lifecycle and #35 confidential PDF/document conformance.
