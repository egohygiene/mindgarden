# Deterministic initialization and migration

Mindgarden lifecycle mutations use a review-gated file plan. Planning and
checking are read-only. Applying requires the exact `plan_sha256` produced from
the current inputs and complete output manifest; changed inputs invalidate the
reviewed digest.

The commands have no network or model dependency.

## Initialize a garden

Initialization supports repository, personal, and organization identities
through the same manifest contract. Omitted identity fields use stable local
defaults: the repository directory becomes the garden id, that id becomes the
owner, `general` becomes the domain, and the canonical URI becomes
`urn:mindgarden:garden:<id>`.

Review a public-garden plan without writing:

```bash
mindgarden init \
  --repository-root "/path/to/consumer" \
  --visibility "public" \
  --garden-id "example-garden" \
  --title "Example Garden" \
  --kind "repository" \
  --owner "egohygiene" \
  --canonical-uri "urn:mindgarden:garden:example-garden" \
  --repository-uri "https://github.com/example/example-garden" \
  --domain "software-engineering" \
  --topic "knowledge-systems"
```

The JSON response lists every directory, file, byte count, and content digest.
Apply only the reviewed result:

```bash
mindgarden init \
  --repository-root "/path/to/consumer" \
  --visibility "public" \
  --garden-id "example-garden" \
  --title "Example Garden" \
  --kind "repository" \
  --owner "egohygiene" \
  --canonical-uri "urn:mindgarden:garden:example-garden" \
  --repository-uri "https://github.com/example/example-garden" \
  --domain "software-engineering" \
  --topic "knowledge-systems" \
  --apply \
  --plan-digest "<reviewed-plan-sha256>"
```

Check the initialized baseline later:

```bash
mindgarden init \
  --repository-root "/path/to/consumer" \
  --check
```

The initial tree contains a v1 manifest, an empty home/map seed, role-aware
templates, canonical content roots, context-pack and provenance directories,
and a local ignore rule for `.generated/`. It never creates
`../.garden.local`; private overlays remain outside committed public content.

## Migrate v0 to v1

Migration first validates v0 and hashes its complete `.garden` tree. Domains
and topics are explicit migration inputs; a deliberately broad `general`
domain is used when no domain is supplied. Folder names never become semantic
classification.

Review the complete plan:

```bash
mindgarden migrate \
  --repository-root "/path/to/consumer" \
  --plan \
  --domain "software-engineering"
```

Apply the unchanged plan:

```bash
mindgarden migrate \
  --repository-root "/path/to/consumer" \
  --apply \
  --domain "software-engineering" \
  --plan-digest "<reviewed-plan-sha256>"
```

Verify the selected v1 tree and rollback boundary:

```bash
mindgarden migrate \
  --repository-root "/path/to/consumer" \
  --check
```

Apply writes the complete v1 tree to a private sibling stage, checks its
lifecycle invariants, atomically renames the untouched v0 tree to `.garden.v0`,
and selects v1 as `.garden`. If cutover fails, v0 is restored. The migration
never merges versions in place.

Stable note identifiers and exact Markdown bytes are preserved. V0 source
notes become v1 Source records rather than Knowledge. Verified source
relationships retain exact hashes; ambiguous locators become explicit deferred
mappings. A legacy `reviewed: true` becomes `in-review` with the fact retained
in `x-v0-reviewed`; migration never invents reviewer identity or review time.
All mechanically migrated records remain excluded from publication.

Because v0 records dates but not event timestamps, migrated history derives a
UTC midnight timestamp from the latest preserved v0 update date and declares
`x-timestamp-precision: v0-date`. This is deterministic date-precision evidence,
not a claim that cutover happened at that wall-clock instant.

The CLI plan's top-level `plan_sha256` binds the complete file manifest used for
review and apply. The applied Migration record's `plan_sha256` separately binds
the validated v0 tree, explicit classification inputs, and migrator version;
this avoids a self-referential digest while preserving both review and history
evidence.

## Refusal and rollback

Both lifecycle operations refuse:

- path traversal and non-portable identifiers;
- symlinked roots or symlinks inside canonical trees;
- existing conflicting files or rollback paths;
- malformed or stale plan digests.

Initialization installs `.garden` with one atomic directory rename. Migration
retains the exact v0 tree at `.garden.v0` and writes rollback instructions into
the new v1 tree. Human review is required before deleting either version.

`init --check` and `migrate --check` enforce only the lifecycle invariants
implemented here. General hardened v1 validation, leak inspection, and
cross-record policy enforcement remain issue #10.
