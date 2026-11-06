# Release preparation and immutable delivery

Mindgarden is an unreleased pre-1.0 Python package. `pyproject.toml` owns its
version. Source imports derive it from PEP 621; installed imports use distribution
metadata. The CLI and generated provenance derive the same value. The prepared
0.1.0 changelog entry is a candidate, not a claim that it shipped. Do not change
the version to 1.0.0 merely to make a release check green.

Read [.egohygiene/release.json](../.egohygiene/release.json),
[the source pins](../.egohygiene/release-sources.json), CHANGELOG.md and
[the batch ledger](release-checkpoints.md) before changing release behavior.
The source declaration uses Aether `repository-release/v1` and the Hygiene
incubating Python profile. Hygiene's policy and ADR remain proposed/null approval;
their closed implementation issues do not establish ratification.

## Prepare from a clean checkout

Use Python 3.12 or 3.13. Build tools are separate from the dependency-free runtime.
Network is needed only for explicit tool/bootstrap installation. Local preparation
does not contact a model, Drive, PyPI publisher or signing service.

```bash
python3 -m pip install --requirement requirements/release.txt
python3 scripts/release.py bootstrap
python3 scripts/release.py plan --release-version v0.1.0
python3 scripts/release.py prepare --release-version v0.1.0 \
  --source-revision "<full-reviewed-source-sha>" \
  --output-directory .cache/release-candidate
python3 scripts/release.py verify --release-version v0.1.0 \
  --output-directory .cache/release-candidate --artifact-only
```

The equivalent Taskfile handoffs are `release:plan`, `release:prepare` and
`release:verify`; pass the same long arguments after `--`. Bootstrap is explicit
read-only acquisition of exact public owner revisions. Offline operation reuses
those verified clean tool checkouts. Owner code is consumed in place, not copied
into Mindgarden's domain or reimplemented as organization policy.

Preparation reads only `git archive` of the exact source commit. Untracked files,
credentials and local caches cannot enter through a working-tree build. It builds
twice in separate temporary trees with pinned tools and `SOURCE_DATE_EPOCH`,
normalizes archive metadata, and requires identical distribution hashes. Existing
output destinations are refused. No canonical garden or vault is mutated.

The bundle contains source/wheel distributions, exact `SHA256SUMS`,
`python-package.json`, source/build provenance, SPDX 2.3 package inventory,
signature status, changelog and rollback guidance. The local provenance is an
unsigned record, not a hosted attestation. Optional PDF/Quartz tools are not
runtime Python dependencies or bundled vendor executables.

## Qualification and known contract gap

The workflow and helpers pin Aether, Hygiene, Relay and EgoLint by full SHA.
Aether validates the declaration; EgoLint's pinned input validator verifies its
own immutable contract sources. This latter check is not a claim that every
EgoLint #29 Python-consumer conformance/dogfood criterion is complete. Relay's
Python profile verifies the complete artifact checksum inventory and package
metadata. Repository checks compare PEP 621, tag, sdist and wheel versions.

At Relay `b4a88db20bc26f9ddefbee174baa8162cbe94ff2`, the reference bundle validator
accepts `version_authority.path = "pyproject.toml"`, but its public JSON Schema's
pattern requires a prefix before that filename. The root declaration is correct;
do not invent another authority path or weaken the schema. The candidate report
preserves `RELEASE_UPSTREAM_SCHEMA_PARITY` and `handoff_ready: false`.
`verify --artifact-only` checks the supported artifact boundary while retaining
that blocked gate. Strict `verify` fails, so publication cannot bypass it.
The owner must correct and review the schema, followed by an explicit pin update
and rerun of the exact conformance scenario.

## Manual publication and external evidence

`release:publish` hands an already reviewed current-main version/revision to
`.github/workflows/release.yml`; it does not publish locally. Normal PR/push checks
are read-only. The manual workflow prepares artifacts, performs strict checks and
delegates immutable GitHub evidence to pinned Relay semantic-release. No workflow
is manually launched as part of this checkpoint.

PyPI remains a separate unavailable repository-owned adapter. No long-lived token
is introduced. 1.0 requires an approved private-pilot report, actual pinned Empathy
acceptance, protected workflow/OIDC configuration and all prepublication checks.
PyPI clean installation and the final released-version consumer pin are verified
after publication; they cannot be prerequisites for the first publication itself.
The [batch ledger](release-checkpoints.md) records this proposed staging correction.

## Compatibility and rollback

The v0 CLI/library remain supported. V1 uses additive contracts and explicit
bindings/session authority. A supported incompatible change at 1.0 or later needs
a reviewed major-version decision and changelog callout. Deprecation names the
replacement and removal horizon; immutable historical artifacts remain intact.
See [v0/v1 compatibility](v0-v1-compatibility.md),
[migration and rollback](initialization-migration.md) and [CLI/library](cli.md).

Restore a prior verified install and its matching canonical/source backup after
a failed upgrade. Never move an immutable tag, replace release assets, rewrite a
published version or run destructive source migration as rollback. Revert the
source, review a corrective successor and update consumers deliberately. A future
registry yank/revocation uses its separately authorized owner adapter.
