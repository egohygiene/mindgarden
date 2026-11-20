---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-20T06:44:57Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Prepare the first bookmark, selected Drive and scoped Codex workflows and consolidate the remaining
    issue queue.
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
  - docs/integration-readiness.md
  - docs/bookmark-cleanup.md
  - docs/drive-capture.md
  - docs/scoped-research.md
  - docs/decisions/README.md
  - docs/acceptance-reconciliation.md
work:
  objective: Prepare the first bookmark, selected Drive and scoped Codex workflows and consolidate the remaining
    issue queue.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#48
    url: https://github.com/egohygiene/mindgarden/issues/48
  next:
    kind: action
    id: review-and-rehearse-first-local-workflow
    description: 'Review the draft stack beginning with #155, then run the synthetic bookmark and private-pilot
      preflight with the maintainer. Select a small export and private destination for a separately scoped local
      session.'
    readiness: ready
    references:
    - docs/integration-readiness.md
    - docs/private-pilot.md
    depends_on: []
state:
  base:
    revision: b47c40adba113b3c82beb19456e7d4db1cba3509
    ref: refs/heads/test/16-32-90-15-acceptance
    verified_at: '2026-11-20T06:44:57Z'
  candidate:
    branch: integration/20261120-bookmark-drive-readiness
    revision: null
    pull_request: null
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-20T06:44:57Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2. Draft #155 at b47c40a is mergeable with Test 43753996698 and preparation 43753996726
      passing. GitHub shows 30 open issues across 44 tracked.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-20T06:44:57Z'
  reviewed_by: codex
  evidence:
  - command: PYTHONPATH="$PWD/src" python -m unittest tests.test_routing tests.test_routing_dispositions tests.test_routing_lifecycle
      tests.test_routing_transfers tests.test_routing_incoming tests.test_reference_repairs -q
    outcome: passed
    observed_at: '2026-11-20T06:44:57Z'
    notes: 42 tests each on Python 3.12.14 and 3.13.5. Wall times 61.971s and 60.331s. Zero skips.
  environment_limitations:
  - Public bookmark intake awaits Akashic owner contracts, and Mindcap owns recurring capture deltas. Drive/Codex
    need local selections and actual runtime authority. Public scope transitions, full manual accessibility, release,
    and proposed ADR dispositions retain their own acceptance.
  - Synthetic inputs only. No live account, real model or deployment was used.
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

Prepare the first bookmark, selected Drive and scoped Codex workflows and consolidate the remaining issue queue.

## Resume protocol

Refresh live issues and PRs, then follow the integration guide and existing local preflight. Verify the candidate against its listed base.

## Current objective and success conditions

Prove the first local operator flows on synthetic inputs and record each owner dependency and exact next action.

## State snapshot

Main 5cf24a2. Draft #155 at b47c40a is mergeable with Test 43753996698 and preparation 43753996726 passing. GitHub shows 30 open issues across 44 tracked.

## Completed and material changes

The new logical rename test resolves the exact previous knowledge reference to the reviewed successor. Search shows one home with the same source evidence. Replay, preserved bytes and the unrelated garden are checked.

## Validation and review evidence

The six routing test modules pass 42 cases per Python, zero skips. Exact command and results are in this file's metadata.

## Blockers, risks, unknowns, and deferred work

Public bookmark intake awaits Akashic owner contracts, and Mindcap owns recurring capture deltas. Drive/Codex need local selections and actual runtime authority. Public scope transitions, full manual accessibility, release, and proposed ADR dispositions retain their own acceptance.

## Next dependency-ready work

Review the draft stack beginning with #155, then run the synthetic bookmark and private-pilot preflight with the maintainer. Select a small export and private destination for a separately scoped local session.

## Parallel changes and reconciliation

The draft candidate stacks on #155. Preserve the four interrupted root worktree files and use the combined child checkout for the full batch.

## Privacy and redaction

Use synthetic fixtures in the repository. Keep credentials, actual bookmark and Drive captures, account-specific paths and private source content in the owner's private workspace.

## Handoff update protocol

After each checkpoint, record issue and PR references, exact tests and the next unmet acceptance item. Update the coverage ledger.

## Compaction and supersession

This checkpoint supersedes the previous waiting-for-sync observation. Prior merge and acceptance receipts retain their original evidence.
