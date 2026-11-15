---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-14T23:01:21Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: 'Implement the authorized bounded #15 → #32 → #44 integration sprint while local setup stays parked.'
  includes:
  - listed-criteria acceptance audit
  - bounded ready integration checkpoints and tested merges
  - synthetic fixtures and exact recovery evidence
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
  - AGENTS.md
  - README.md
  - AI_CONSTITUTION.md
  - ARCHITECTURE.md
  - SYSTEM.md
  - ROADMAP.md
  - docs/open-issue-coverage.md
  - docs/decisions/README.md
  - docs/repository-audit-followthrough.md
  - docs/remaining-acceptance-audit.md
  - docs/consultation-packets.md
  - docs/drive-normalization.md
  - docs/pipeline-integration-sprint.md
work:
  objective: 'Implement the authorized bounded #15 → #32 → #44 integration sprint while local setup stays parked.'
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#32
    url: https://github.com/egohygiene/mindgarden/issues/32
  next:
    kind: action
    id: integration-sprint
    description: 'Push the #32 reviewed refresh/migration checkpoint on #152, then extend #44 supported public relationships
      using the delivered Relay #115 and pinned Observatory/Hygiene contracts. No draft merge; local setup stays
      parked.'
    readiness: ready
    references:
    - docs/pipeline-integration-sprint.md
    - docs/conversation-archive-compatibility.md
    depends_on: []
state:
  base:
    revision: c28738d13858aceccef11f9773ced48c7c35365c
    ref: refs/heads/feature/15-delivery-privacy
    verified_at: '2026-11-14T23:01:21Z'
  candidate:
    branch: feature/32-incremental-cache
    revision: 369dc1366623c338d44efa24b0da5a0d43606aed
    pull_request:
      provider: github
      id: egohygiene/mindgarden#153
      url: https://github.com/egohygiene/mindgarden/pull/153
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-14T22:27:50Z'
    default_branch_revision: 270ced6a5d6ea0d4c07298fdcfebcae2363b7c8a
    issue_state: open
    pull_request_state: draft
    notes: 'Main remains 270ced6. #152 functional b097abd / docs 6679317 is a pushed draft. The #32 child adds scoped
      incremental refresh, known migration and retained rollback. Thirty cases pass per Python; benchmark/combined
      artifact verification follows. #44 owner refresh found Relay #115 closed/delivered; historical authority and
      actual consumer acceptance remain distinct. Draft #153 is pushed at 369dc13; current exact-head CI and final
      artifact qualification are separate. Parent #152 c28738d corrects the two hosted nested goldens; five cases
      pass per Python. Query fixture packaging correction e48cf65 and continuity observation timestamps are preserved.
      Exact-head CI remains separate.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-14T22:27:50Z'
  reviewed_by: codex
  evidence:
  - command: Python 3.12/3.13 -m unittest tests.test_archive_delivery tests.test_archive_continuation tests.test_archive_v2
      tests.test_conversation_archives tests.test_archive_selection tests.test_archive_diagrams --verbose
    outcome: passed
    observed_at: '2026-11-14T22:27:50Z'
    notes: 29 cases per Python, zero skips (11.576s / 11.899s). Ten workflow/schema cases pass per Python, zero
      skips (48.760s / 46.644s).
  - command: python -m unittest tests.test_query_store_evolution tests.test_query_store tests.test_v1_contracts
      tests.test_standalone_integration --verbose
    outcome: passed
    notes: 30 per Python, zero skips; 3.12 16.315s / 3.13 15.177s.
    observed_at: '2026-11-14T22:59:23Z'
  - command: PYTHONPATH=src python -m unittest tests.test_pipeline_completion tests.test_reading_journey --verbose
    outcome: passed
    observed_at: '2026-11-14T23:00:51Z'
    notes: Hosted Test 43648300397 at 6679317 found two stale nested metadata goldens; native macOS passed. Constrained
      pipeline/reading correction preserves source/vault/public facts. Five follow-up cases pass per Python (75.947s
      / 72.789s); no runtime or validation weakening. New exact-head CI remains separate.
  environment_limitations:
  - Mac setup, actual private paths/collection/credentials/consumer authority, live OAuth/Drive/Codex/model quality,
    approved private pilot and confidential runtime remain unperformed.
  - Long shell sessions without completion records are not passing evidence; durable module logs and actively polled
    artifact runs supersede them.
  - Full local/act and manual accessibility remain separate. One unchanged scoped lint finding remains. Process-level
    fixture network blocks do not certify host isolation.
  - 'No status/approval changes: eighteen indexed ADR proposals and six legacy Accepted labels preserved. #19/#27
    and #88/#91 stay deferred.'
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

Local setup is parked. The maintainer authorized the next repository batch. Existing draft ancestry remains explicit; no new merge authority or ADR disposition is inferred.

## Resume protocol

Refresh live PR/issues/comments and owner inputs; read the sprint ledger and preserve all existing worktrees and four root WIP entries. Work from the reproducible combined child.

## Current objective and success conditions

Implement the authorized bounded #15 → #32 → #44 integration sprint while local setup stays parked.

## State snapshot

Main remains 270ced6. #152 functional b097abd / docs 6679317 is a pushed draft. The #32 child adds scoped incremental refresh, known migration and retained rollback. Thirty cases pass per Python; benchmark/combined artifact verification follows. #44 owner refresh found Relay #115 closed/delivered; historical authority and actual consumer acceptance remain distinct.

## Completed and material changes

#152 projects recognized delivery facts while withholding free-text/runtime extensions in portable metadata. The private immutable ZIP stays complete. Known v2/v3 continuation evidence remains summary-derived/unreviewed. Adapter 1.2.1 changes only permitted metadata-view golden hashes; exact source/vault evidence stays equal.

## Validation and review evidence

39 archive/workflow/schema cases pass per Python, zero skips; full exact golden journeys pass (including relocation/restore). Commands/times and corrected initial attempts are in the sprint ledger. The previous 184-case qualification belongs to #151, not this changed source. Initial test helper and invocation mistakes are corrected before success is claimed; CI remains separate.

## Blockers, risks, unknowns, and deferred work

Untested archive profiles and actual private/Empathy proof stay explicit. #32 requires incremental/migration evidence. #44 must use actual supported owner read-model contracts. Historical ADR authority/human disposition, confidential runtime and real model/provider acceptance remain independent. Releases and local setup stay parked.

## Next dependency-ready work

Push the #32 reviewed refresh/migration checkpoint on #152, then extend #44 supported public relationships using the delivered Relay #115 and pinned Observatory/Hygiene contracts. No draft merge; local setup stays parked.

## Parallel changes and reconciliation

Use small draft children on #151 without force-push, reset or automatic merge. The final child is the combined checkout. Earlier stack tests do not qualify new runtime changes.

## Privacy and redaction

Synthetic committed inputs only. Private spec bodies, real archives, credentials, source locations and actual consultation packets stay outside the repository. Delivery projection is not a general source-text sanitizer or host isolation guarantee.

## Handoff update protocol

At each checkpoint record branch/PR, commits, exact tests and CI, met/unmet criteria, blockers and next action. Preserve all 44 coverage rows and the eighteen proposed/null-approval ADRs plus six original legacy labels.

## Compaction and supersession

Keep these twelve headings and 16384-byte/240-line bounds. The active sprint supersedes the previous suggested next batch, not its immutable qualification history.
