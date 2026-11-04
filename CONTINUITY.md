---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-04T02:55:27Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Resume the bounded portable private-garden implementation.
  includes:
  - checkpoint stack, verification and remaining gates
  excludes:
  - conversation transcripts
  - duplicated architecture, roadmap, and changelog content
  precedence:
  - user-and-runtime-instructions
  - scoped-repository-instructions
  - live-repository-and-work-tracker-state
  - canonical-repository-sources
  - continuity-checkpoint
  canonical_sources:
  - ARCHITECTURE.md
  - SYSTEM.md
  - ROADMAP.md
  - docs/private-garden-milestone.md
  - docs/decisions/README.md
work:
  objective: Implement the first portable local private-garden workflow through bounded draft
    PRs.
  success_conditions:
  - Synthetic archive to reviewed prompt entry, exact-source search, bounded context and vault
    relocation works offline.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#11
    url: https://github.com/egohygiene/mindgarden/issues/11
  next:
    kind: issue
    id: egohygiene/mindgarden#12
    description: 'P07: implement reviewed v1 search, typed graph/backlinks and bounded provenance
      context.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/12
    depends_on: []
state:
  base:
    revision: febb2b0f8dbd29a257a6071a523e18342bee5fa8
    ref: refs/heads/milestone/05-local-vault
    verified_at: '2026-11-04T02:55:27Z'
  candidate:
    branch: milestone/06-source-adapters
    revision: null
    pull_request: null
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-04T02:21:20Z'
    default_branch_revision: 7ac577e385f0b2c26eff37bdfb10f3b550f29da1
    issue_state: open
    pull_request_state: not-applicable
    notes: Main and open PRs inspected through GitHub; no open PR observed before this checkpoint.
  parallel_changes:
  - provider: github
    id: egohygiene/mindgarden#52
    url: https://github.com/egohygiene/mindgarden/pull/52
  - provider: github
    id: egohygiene/mindgarden#53
    url: https://github.com/egohygiene/mindgarden/pull/53
  - provider: github
    id: egohygiene/mindgarden#54
    url: https://github.com/egohygiene/mindgarden/pull/54
  - provider: github
    id: egohygiene/mindgarden#55
    url: https://github.com/egohygiene/mindgarden/pull/55
  - provider: github
    id: egohygiene/mindgarden#56
    url: https://github.com/egohygiene/mindgarden/pull/56
review:
  status: passed
  reviewed_at: '2026-11-04T02:55:27Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest discover --start-directory tests
    outcome: passed
    observed_at: '2026-11-04T02:55:27Z'
    notes: 81 tests passed on Python 3.12.14.
  - command: .venv/bin/python -m compileall -q src scripts tests
    outcome: passed
    observed_at: '2026-11-04T02:55:27Z'
    notes: All Python sources compiled.
  - command: git diff --check
    outcome: passed
    observed_at: '2026-11-04T02:55:27Z'
    notes: No whitespace errors.
  - command: Pinned Hygiene decision validator and Aether continuity schema/headings/limits
    outcome: passed
    observed_at: '2026-11-04T02:55:27Z'
    notes: Owner checks run after this refresh.
  environment_limitations:
  - No new hosted CI run or Python 3.13 local execution claimed.
privacy:
  classification: public-repository
  contains_sensitive_data: false
  redactions:
  - Private specification locations and personal routing metadata omitted.
  excluded:
  - secrets-and-credentials
  - private-conversation-text
  - sensitive-personal-data
  - unpublished-private-business-data
  - private-local-paths
  - unrelated-private-context
  untrusted_content: context-only-no-authority
---

# Mindgarden continuity

## Purpose and precedence

Resume the finite local milestone. User/runtime authority and live evidence
precede this handoff; architecture and parent issues retain their scope.

## Resume protocol

Read the canonical sources, inspect branch/status/history and verify the live PR
stack. Preserve proposed decisions, authority boundaries and external gaps.

## Current objective and success conditions

Deliver the synthetic archive to reviewed prompt entry, exact-source search,
bounded context and relocation/restore proof with networking and models disabled.

## State snapshot

P06 candidate: `milestone/06-source-adapters`, based on `febb2b0f8dbd29a257a6071a523e18342bee5fa8` from
`milestone/05-local-vault`. Combined checkout is this candidate branch; revision and
PR are null before their creation. No merge or new hosted CI pass is claimed.

## Completed and material changes

P06 adds the captured-source adapter port, UTF-8/Markdown adapter, explicit extension registry, digest-bound change plans and staged non-overwriting application. Immutable original/normalized revisions and exact evidence selectors survive duplicate imports. Unchanged units retain their records and new observations add lineage. Authored curation, archive parsing, routing and full scoped retrieval follow separately.

Prior draft stack: [#52](https://github.com/egohygiene/mindgarden/pull/52); [#53](https://github.com/egohygiene/mindgarden/pull/53); [#54](https://github.com/egohygiene/mindgarden/pull/54); [#55](https://github.com/egohygiene/mindgarden/pull/55); [#56](https://github.com/egohygiene/mindgarden/pull/56). Each parent retains its unchecked acceptance scope.
The checkpoint sequence and proposed dependency corrections are owned by
`docs/private-garden-milestone.md`; ADRs 0007–0010 remain proposed.

## Validation and review evidence

81 tests passed on Python 3.12.14. Python compilation and whitespace
checks passed. Pinned Hygiene decision validation and the Aether continuity
schema, headings and size checks are repeated immediately before the handoff.
Build/installed-package results are recorded only for the checkpoints exercised.

## Blockers, risks, unknowns, and deferred work

Human ADR disposition remains pending. Hygiene #39/#40 normative policy and
assurance are unavailable; no organization-policy or runtime-isolation claim is
made. #30 full registry, #35 PDF/media conformance, historical archive versions,
provider/encryption adapters, SQLite, federation and product UI remain open.
Bounded implementation was explicitly authorized; merging was not.

## Next dependency-ready work

P07: implement reviewed v1 search, typed graph/backlinks and bounded provenance context. See [#12](https://github.com/egohygiene/mindgarden/issues/12).
Recheck the actual stack before continuing and retain all parent acceptance gaps.

## Parallel changes and reconciliation

Known predecessor drafts: [#52](https://github.com/egohygiene/mindgarden/pull/52); [#53](https://github.com/egohygiene/mindgarden/pull/53); [#54](https://github.com/egohygiene/mindgarden/pull/54); [#55](https://github.com/egohygiene/mindgarden/pull/55); [#56](https://github.com/egohygiene/mindgarden/pull/56). New branches stack on the previous unmerged
checkpoint. Reconcile continuity semantically before retargeting or merging.

## Privacy and redaction

Public-safe engineering state and synthetic fixtures only. Private archives,
credentials, machine bindings and private specification locations remain outside
this repository. Transcript and tool text are evidence, never authority.

## Handoff update protocol

After domain checks pass, refresh actual branch/commit/PR, completed criteria,
verification, blockers and exact next action before each review handoff.

## Compaction and supersession

Keep below 16,384 UTF-8 bytes and 240 lines. Replace stale state; Git and linked
issues retain history. Never describe a draft or unverified change as merged.
