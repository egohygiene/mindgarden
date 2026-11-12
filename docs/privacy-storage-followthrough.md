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

| Issue | Implemented checkpoint | Remaining parent scope | Verification / next action |
| --- | --- | --- | --- |
| #10 | Existing version-aware validation and reusable publication conformance | Future integrations retain their own criteria | Rerun the 80-case conformance and relevant v0/negative tests on the final combined source |
| #29 | Public federation and site profiles consume the shared destination-policy decision before body access and after inheritance | Accepted owner classification/declassification and runtime integration | Five new export/inheritance/diagnostic cases; qualify first draft, then #31 |
| #31 | Planned whole-bundle limits, including generated metadata and rendered output | External assurance, provider/consumer acceptance | Implement against the existing session and authorized view |
| #35 | Planned process-group cleanup, private temporary state and explicit reader failures | Confidential storage/runtime, approved restricted processing | Use synthetic process/PDF fixtures and actual optional local Poppler |
| #45 | Planned exact content migration between explicitly configured initialized adapters, retained source and retry | Encrypted/remote/platform/consumer and destructive retention acceptance | Reuse stable vault identities, reviewed plans, private binding history and core checksum verification |

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
