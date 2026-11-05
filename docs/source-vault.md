# Local immutable source vault

The #45 filesystem checkpoint implements `mindgarden.domain.storage.BlobStorage`.
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

Capabilities are runtime-discovered and honest: immutable put/read/checksums and
audit exist. Encryption, remote storage, destructive deletion and the later
export/restore/relocation checkpoint are not claimed here. Owner-only permissions
are used on the tested Linux baseline; this is not encryption or host assurance.
The full #45 issue, #30 registry lifecycle and #35 document/media proof remain open.
