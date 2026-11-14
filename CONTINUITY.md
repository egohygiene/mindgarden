---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-14T22:27:50Z'
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
    id: egohygiene/mindgarden#15
    url: https://github.com/egohygiene/mindgarden/issues/15
  next:
    kind: action
    id: integration-sprint
    description: 'Push the #15 delivery/privacy draft on #151, then implement reviewed incremental query-cache refresh
      and known-version migration under #32; finish supported public ADR relationships under #44. Preserve the explicit
      unmerged stack.'
    readiness: ready
    references:
    - docs/pipeline-integration-sprint.md
    - docs/conversation-archive-compatibility.md
    depends_on: []
state:
  base:
    revision: ecaca37e0a21880bbf1996167ce0a99ca0dfcc96
    ref: refs/heads/test/15-16-acceptance-audit
    verified_at: '2026-11-14T22:27:50Z'
  candidate:
    branch: feature/15-delivery-privacy
    revision: null
    pull_request: null
    handoff_state: in-progress
  live:
    status: verified
    observed_at: '2026-11-14T22:27:50Z'
    default_branch_revision: 270ced6a5d6ea0d4c07298fdcfebcae2363b7c8a
    issue_state: open
    pull_request_state: draft
    notes: 'Main remains 270ced6. Draft base #148 → #149 → #150 → #151/ecaca37; new branch feature/15-delivery-privacy
      implements bounded delivery facts and known bootstrap evidence. No merge, closure or owner approval. Root
      four WIP entries remain untouched.'
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
    notes: 29 cases per Python, zero skips (11.576s / 11.899s). Ten workflow/schema cases pass per Python, zero skips (48.760s / 46.644s).
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

Main remains 270ced6. Draft base #148 → #149 → #150 → #151/ecaca37; new branch feature/15-delivery-privacy implements bounded delivery facts and known bootstrap evidence. No merge, closure or owner approval. Root four WIP entries remain untouched.

## Completed and material changes

The #15 child projects recognized delivery facts while withholding free-text/runtime extensions in portable metadata. The private immutable ZIP stays complete. Known v2/v3 continuation evidence remains summary-derived/unreviewed. Adapter 1.2.1 changes only permitted metadata-view golden hashes; exact source/vault evidence stays equal.

## Validation and review evidence

39 archive/workflow/schema cases pass per Python, zero skips; full exact golden journeys pass (including relocation/restore). Commands/times and corrected initial attempts are in the sprint ledger. The previous 184-case qualification belongs to #151, not this changed source. Initial test helper and invocation mistakes are corrected before success is claimed; CI remains separate.

## Blockers, risks, unknowns, and deferred work

Untested archive profiles and actual private/Empathy proof stay explicit. #32 requires incremental/migration evidence. #44 must use actual supported owner read-model contracts. Historical ADR authority/human disposition, confidential runtime and real model/provider acceptance remain independent. Releases and local setup stay parked.

## Next dependency-ready work

Push the #15 delivery/privacy draft on #151, then implement reviewed incremental query-cache refresh and known-version migration under #32; finish supported public ADR relationships under #44. Preserve the explicit unmerged stack.

## Parallel changes and reconciliation

Use small draft children on #151 without force-push, reset or automatic merge. The final child is the combined checkout. Earlier stack tests do not qualify new runtime changes.

## Privacy and redaction

Synthetic committed inputs only. Private spec bodies, real archives, credentials, source locations and actual consultation packets stay outside the repository. Delivery projection is not a general source-text sanitizer or host isolation guarantee.

## Handoff update protocol

At each checkpoint record branch/PR, commits, exact tests and CI, met/unmet criteria, blockers and next action. Preserve all 44 coverage rows and the eighteen proposed/null-approval ADRs plus six original legacy labels.

## Compaction and supersession

Keep these twelve headings and 16384-byte/240-line bounds. The active sprint supersedes the previous suggested next batch, not its immutable qualification history.
