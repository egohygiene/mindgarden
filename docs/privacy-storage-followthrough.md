# Privacy and storage follow-through — 2026-11-09

The maintainer selected #10, #29, #31, #35 and #45 after the overnight stack
merged at `7594921`. #10 is closed against its listed engine-validation criteria;
verify that evidence rather than reopen it or conflate later runtime assurance.
Keep Python/v0, canonical garden ownership and all proposed ADR approval states.

## Dependency reconciliation

Hygiene #39 and #40 are still open without comments. Its complete main tree at
`92195e49b50778517ef670a7ec97c922dbdf9cec` supplies no classification,
information-flow, declassification or confidential-assurance specification.
The existing pinned local policy is a proposed reference implementation, not
accepted organization policy. No alternate policy ID or fabricated contract is
introduced here.

Realm #25 remains the broader program. Correction to earlier shorthand: #60
consolidates platform/distribution and environment acceptance; encrypted-vault
selection, implementation and confidential processing are still owned directly
by Realm #28, #29 and #30. These are integration prerequisites for confidential
assurance, not blanket gates for ordinary synthetic local checkpoints.

Execute four bounded checkpoints: #29 destination-policy consumption; #31
whole-bundle output/session enforcement; #35 local parser process containment;
#45 reviewed adapter migration and recovery. Each checkpoint opens a draft,
records exact source/tests and updates continuity/coverage. Keep an explicit
stack and one reproducible combined checkout. Missing owner contracts leave
their parent acceptance open; no encryption product, runtime or model is selected.

## Checkpoints

Final review stack: **#127 → #128 → #129 → #130**, all draft and unmerged. Combined branch: `feature/45-reviewed-adapter-migration`; qualified functional source: `e789c0c`. #10 stays closed; no parent issue is silently closed by these local proofs.

| Issue | Implemented checkpoint | Remaining parent scope | Verification / next action |
| --- | --- | --- | --- |
| #10 | Existing version-aware validation and reusable publication conformance | Future integrations retain their own criteria | Rerun the 80-case conformance and relevant v0/negative tests on the final combined source |
| #29 | Public federation and site profiles consume the shared destination-policy decision before body access and after inheritance | Accepted owner classification/declassification and runtime integration | Five new export/inheritance/diagnostic cases; qualify first draft, then #31 |
| #31 | Complete output/session limits, including ownership metadata and actual rendered artifacts | External assurance, provider/consumer acceptance | Draft #128; 98 focused cases per Python, final combined qualification below |
| #35 | Managed process-group cleanup, owner-only child defaults and bounded private temporary output | Confidential storage/runtime, approved restricted processing | Draft #129; 19 focused cases per Python plus actual six-state Poppler proof |
| #45 | Reviewed local copy/verify/rebind, private binding history, retained stores and same-digest partial retry | Approved-copy/GC policy and verified encrypted/provider/platform integration when selected | Draft #130; 35 focused cases per Python plus clean source/wheel migration goldens |

### #29 export policy

An approved public projection cannot weaken its contributors' persistence or
execution. Both federation and the site adapter now use the existing
`require_destination(..., operation="export")` service. Optional profile scope
is an explicit destination ceiling; without it the existing request scope is
used. Existing compatible output bytes and local policy IDs stay unchanged.
Unknown policies, publication restrictions and unverified encrypted destinations
remain fail-closed. Unsupported policy-operation diagnostics use a constant
sentinel rather than echoing supplied text. This adds no publication grant,
declassification implementation or organization assurance.

Verification: `python -m unittest tests.test_export_policy tests.test_scope_policy tests.test_federation tests.test_site --quiet` passes **39 cases, zero skips** on Python 3.12.14 (51.261s) and 3.13.5 (43.269s). Five new cases cover independent destination axes, unchanged compatible output, untrusted policy/publication, mixed-input joins and non-echoing diagnostics. Focused Ruff E9/F, new-file formatting and diff checks pass. Branch: `feature/29-export-policy-boundaries`, base `main`; hosted CI is separate.

Draft [#127](https://github.com/egohygiene/mindgarden/pull/127) preserves functional `1cb3a60594a678862e5bd2d167218b12b21ea87b` above main `7594921`. The first local continuity check rejected a non-owner status enum; the corrected owner enum, schemas and bounds pass before push. New-head CI is separate.


### #31 complete output inventories

Federation and site content, actual rendered artifacts and all session-owned
private generated bundles now share `QueryContext.ensure_bundle`. The validator
sums the complete inventory and checks live authority before directory creation.
Generated ownership metadata counts too. Reuse/check/preview paths cannot select
an older oversized site under a smaller session. The authorized internal index
is not charged as an exported response when a reviewed projection selects only
a small subset. Default compatible bytes and session identities remain stable.

Eight new cases cover aggregate federation output, small selection over a larger
corpus, site metadata, oversized renderer output, mid-render revocation, generated
markers, authority-first errors and constant invalid-value diagnostics. Focused
and full verification results follow after their commands finish. Branch
`feature/31-bounded-generated-bundles` is stacked on draft #127.

Initial new-case verification: **8 pass, zero skips**, Python 3.12.14 (12.063s). Two initial fixture budgets were below the existing 256-byte schema minimum; corrected fixtures keep that contract unchanged. The first broader command also named nonexistent `tests.test_compaction_bundles`; it is not passing evidence. Corrected broader runs use `tests.test_source_compaction`, followed by final full discovery. Focused changed-code Ruff and diff checks pass.

Draft [#128](https://github.com/egohygiene/mindgarden/pull/128), functional `177dad83a4c54d47b57f5ba9ff8d7caed5e9eb45`, is based on #127. Corrected broader suites run from an immutable worktree; new implementation cannot change those tested bytes.


Corrected #31 command: `python -m unittest tests.test_scope_bundle_outputs tests.test_output_scope tests.test_federation tests.test_site tests.test_memory_validity tests.test_learning_queue tests.test_selected_builds tests.test_extraction tests.test_insights tests.test_source_compaction tests.test_local_federation --quiet` — **98 pass, zero skips** on frozen `177dad8`, Python 3.12.14 (205.507s) and 3.13.5 (195.094s). The superseded 88-case invocations each ended with three errors (two invalid test budgets and the nonexistent module); those attempts are not passing evidence.

### #35 bounded local process lifetime

Branch `fix/35-pdf-process-lifecycle`, based on #128. The runner now kills its
started process group in a bounded cleanup step even when the parent completes,
so children cannot keep the owned work files open after normal completion or
timeout. Child-created files use umask 077; standard home/temp/cache/config/data/
state locations are confined to the supplied vault work root. Parser output and
errors remain bounded private temporary files, with constant shareable failures.

`python -m unittest tests.test_pdf_process_lifecycle tests.test_documents tests.test_storage_adapters tests.test_mixed_vault_workflow --quiet` — **19 pass, zero skips**, Python 3.12.14 (28.681s) and 3.13.5 (28.293s).
Five new cases exercise normal-exit descendants, timeout descendants, environment/
permissions, resource failure and unavailable tools. The committed synthetic
probe contains no document or credential data. The two interpreter runs are
software behavior checks, not a confidential-runtime attestation.

Actual `python scripts/document_demo.py --workspace /tmp/mindgarden-privacy-pdf-native --tool-directory /usr/bin --require-source --report .cache/privacy-storage/35-native.json` also passes with Poppler 25.03.0: complete, encrypted, malformed, OCR-needed, partial and unsupported. [The native receipt](evidence/privacy-pdf-native.json) preserves exact original/page hashes, duplicate handling and removed owned temporary state. Focused Ruff/format and diff checks pass.

These controls govern the started process group. They cannot contain a hostile
executable that escapes that group or prove host/network/swap/encryption security.
Restricted processing still stops before parsing; no ordinary-file label grants
confidential authority. Additional formats remain separate adapters.

Draft [#129](https://github.com/egohygiene/mindgarden/pull/129), functional `6d31e75fd76fccaa27c82cf32eba81914815e30a`, is stacked on #128. Qualification and parent gates remain distinct from merge or acceptance.


### #45 reviewed initialized-adapter migration

Branch `feature/45-reviewed-adapter-migration`, based on draft #129. The new
`vault migrate --target-local-config` plan/apply and versioned private control
schema bind configurations, capabilities, complete inventoried objects and garden
revisions. Copy includes unreferenced originals; target extras are retained and
never adopted as knowledge. Independent target reopen and core checksums precede
private binding history and durable rebind. Partial retries keep the same digest;
stale, corrupt, unsupported or unavailable inputs fail without source loss.
See [the operation/recovery contract](vault-migration.md), including completed-CLI
verification and explicit single-writer/provider limits.

`python -m unittest tests.test_vault_migration tests.test_vault_recovery tests.test_storage_adapters tests.test_v1_contracts --quiet` — **35 pass, zero skips**, Python 3.12.14 (14.181s) and 3.13.5 (14.091s). Sixteen new cases include exact CLI review, retained source/target objects, private controls, partial retry, stale input, changed capabilities, dishonest read/put, absent adapters, unknown commit state, isolated factory bindings and complete golden recovery. The explicit schema inventory and valid fixture include the new contract.

`python scripts/vault_migration_demo.py --workspace /tmp/mindgarden-adapter-migration-source-v2 --require-source --report .cache/privacy-storage/45-migration-proof.json` passes with networking/HTTP/process entry points blocked. Two immutable objects (including an unreferenced original) survive migration, extension removal and clean restore. Exact index, context and source evidence match the committed golden. The extension uses actual filesystem bytes behind a synthetic adapter ID; no real provider is claimed.

The first 20-case migration run had one test expecting unavailable for an initialized target whose descriptor was removed; that is correctly corrupted. The corrected test proves both corrupted and genuinely absent states. The first standalone workflow reached its report serialization with a mistaken bytes index; the corrected complete workflow was rerun in a new workspace and is now covered by the golden test. Neither earlier attempt is passing qualification.

#127 head `5c267b5fbfc3f68b3b992b41c7644bbc51438919` has successful automatic Test **42599031839** and release-preparation **42599031929**. #128 head `5548976ba4fb3c2eb63c3d643faf45631d677fd2` has successful Test **42599887053** and release-preparation **42599886961**. No run was returned for current #129 head `3893c399e3b96cb56868b7f573c9de30b7d40cfd` when inspected; that is unavailable CI evidence, not a pass. Final combined and new-head qualification follows. No workflow was manually dispatched.


## Final combined qualification and resume action

The immutable combined functional source is
`e789c0c2a27f477b52f96529236966ad1c962ea4`. The final handoff commit changes
only documentation/evidence; compare runtime/contracts/scripts/tests/profiles to
that source before interpreting a newer branch tip. All four drafts preserve
explicit stack ancestry. Main remains `7594921`; all 44 coverage rows and 35 open
issues are retained.

| Verification | Actual result |
| --- | --- |
| Frozen Python 3.12.14 full discovery | **515 pass, zero skips**, 707.932s |
| Frozen Python 3.13.5 full discovery | **515 pass, zero skips**, 681.235s |
| Reusable source publication/preview conformance | **80 pass, zero skips**, all eight leak surfaces |
| Clean local wheel and unpacked source archive | Four exact migration/pipeline goldens; zero runtime dependencies |
| Installed v0 CLI/library | Version 0.1.0; three-note validation, three-note/one-context verification, two-note public verification and library validation pass |
| Ordinary native PDF | Poppler 25.03.0; six parser states pass; owned temporary work removed |
| Focused lint/format/compilation | Ruff E9/F on all 26 changed Python files; eight new-file format checks; compileall pass |
| Pinned owner contracts | 24 proposed/null-approval ADRs, exact 44 issue rows and bounded continuity schema/headings pass |

Full commands execute from the frozen checkout with its `src` first on
`PYTHONPATH`, using the corresponding prepared interpreter:

```bash
python -m unittest discover --start-directory tests --verbose
python scripts/publication_conformance.py --require-source --report /tmp/new-publication-report.json
python -m build --no-isolation --sdist --wheel --outdir .cache/dist
```

The test launcher must permit loopback for the public preview HTTP fixture. The
first conformance attempt and unqualified full runs lacked that permission:
conformance was incomplete and each full run had one `PermissionError` at socket
creation. They are not passing evidence. The corrected 80-case pack and both
full runs pass with the proper test permissions. The migration and pipeline
proofs independently block socket/HTTP/external process entry points in-process;
no Google, model service, real private archive or provider credential is used.

The wheel is installed into an empty venv with global pip using
`python -m pip --python EMPTY_VENV/bin/python install --no-index --no-deps LOCAL_WHEEL`.
Its module resolves inside that venv and metadata declares no runtime dependencies.
The sdist is extracted with the data filter and uses a separate empty venv.
Actual isolated commands from the repository root:

```bash
.cache/privacy-storage/wheel-proof/bin/python -I .cache/privacy-storage/unpacked-sdist/mindgarden-0.1.0/scripts/vault_migration_demo.py --workspace /tmp/mindgarden-privacy-wheel-migration --require-installed --report .cache/privacy-storage/wheel-migration.json
.cache/privacy-storage/wheel-proof/bin/python -I .cache/privacy-storage/unpacked-sdist/mindgarden-0.1.0/scripts/pipeline_completion_demo.py --workspace /tmp/mindgarden-privacy-wheel-pipeline --require-installed --report .cache/privacy-storage/wheel-pipeline.json
.cache/privacy-storage/source-proof/bin/python -I .cache/privacy-storage/unpacked-sdist/mindgarden-0.1.0/scripts/vault_migration_demo.py --workspace /tmp/mindgarden-privacy-sdist-migration --require-source --report .cache/privacy-storage/sdist-migration.json
.cache/privacy-storage/source-proof/bin/python -I .cache/privacy-storage/unpacked-sdist/mindgarden-0.1.0/scripts/pipeline_completion_demo.py --workspace /tmp/mindgarden-privacy-sdist-pipeline --require-source --report .cache/privacy-storage/sdist-pipeline.json
```

All four reports match committed fixture bytes. Migration retains original
objects, preserves exact evidence/index/context, recovers a partial copy using
the same digest, returns to filesystem after removing the extension and restores
into a clean root. The existing mixed conversation/PDF/image/audio pipeline still
produces reviewed prompt knowledge and the exact archive member/pointer, with a
**4,419-byte context inside 8,192**, relocation/restore and clean projection rebuild.

[The structured qualification](evidence/privacy-storage-qualification.json)
records source/wheel hashes, limits, failed attempts and exact functional-head CI.
The four functional/current parent heads have successful Test and
release-preparation runs; #129/#130 Decisions preview also passes. The earlier
empty #129 run listing was not passing evidence; subsequent runs are now
observed. No workflow was manually dispatched. Following documentation-head CI
is a separate observation recorded on #130, not substituted with earlier green CI.

Dependency correction: #35's first slice explicitly uses synthetic documents.
Real employment/personal records, an approved real-data pilot and OCR/office
adapters are not added acceptance gates for that synthetic slice. The remaining
confidential positive path does require the missing normative policy and actual
restricted storage/runtime. The real legacy-archive pilot remains #20 scope.
Likewise optional remote/encrypted providers need evidence when selected; the
filesystem baseline does not become dependent on those services.

Exact next action: refresh review/comments and current heads, review the four
bounded drafts in order **#127 → #128 → #129 → #130**, and qualify the final
handoff head separately before any merge. Then adopt an actual accepted
Hygiene/Realm policy/assurance contract when supplied. Keep #29/#31/#35/#45 open
for their unimplemented owner-dependent scope; do not ratify ADRs, activate
release/deferred context packages, process real private records, delete originals
or infer confidential assurance from adapter booleans.
