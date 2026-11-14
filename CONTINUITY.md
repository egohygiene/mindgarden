---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-14T22:53:43Z'
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
    id: egohygiene/mindgarden#44
    url: https://github.com/egohygiene/mindgarden/issues/44
  next:
    kind: action
    id: integration-sprint
    description: 'Push the #44 public-relationship draft on #153, qualify the combined checkout from source/installed
      artifacts, update live issue/CI evidence and hand off for maintainer review. No automatic merge or local/private
      setup.'
    readiness: ready
    references:
    - docs/pipeline-integration-sprint.md
    - docs/adr-projections.md
    - docs/query-stores.md
    depends_on: []
state:
  base:
    revision: 1a71927baa6f485a3b16a92ebae9e73a440ca822
    ref: refs/heads/feature/32-incremental-cache
    verified_at: '2026-11-14T22:53:43Z'
  candidate:
    branch: feature/44-public-decision-relationships
    revision: null
    pull_request: null
    handoff_state: in-progress
  live:
    status: verified
    observed_at: '2026-11-14T22:53:43Z'
    default_branch_revision: 270ced6a5d6ea0d4c07298fdcfebcae2363b7c8a
    issue_state: open
    pull_request_state: draft
    notes: 'Main stays 270ced6. Draft stack #148 → #149 → #150 → #151 → #152 → #153, with #44 child on #153 handoff
      1a71927. Archive delivery and cache evolution are tested/pushed, not merged. Public related ADR metadata and
      actual pinned Hygiene/Observatory/Relay native synthetic composition now pass. Complete combined artifact/CI
      observation before handoff.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-14T22:53:43Z'
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
  - command: python scripts/verify_decision_relationships.py --owner-sources .cache/decision-owner-sources --require-source
      --report tests/fixtures/decisions/owner-proof.json
    outcome: passed
    notes: Hash-pinned Hygiene schema/semantics → byte-identical Observatory snapshot → Mindgarden golden and existing
      Relay validator/Decisions renderer. Three decisions/six artifacts/eight typed edges and context entries. Synthetic
      approval only.
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

Main stays 270ced6. Draft stack #148 → #149 → #150 → #151 → #152 → #153, with #44 child on #153 handoff 1a71927. Archive delivery and cache evolution are tested/pushed, not merged. Public related ADR metadata and actual pinned Hygiene/Observatory/Relay native synthetic composition now pass. Complete combined artifact/CI observation before handoff.

## Completed and material changes

#152 confines delivery runtime details to private originals and proves known bootstrap evidence. #153 adds live-authority incremental refresh and known SQLite schema migration; failed rollback now retains prior cache bytes. The #44 child adds explicit public related artifacts, typed provenance/context and cross-owner revisions, using the delivered Relay #115 contracts. No canonical ADR/source is rewritten.

## Validation and review evidence

#152: 39 archive/workflow/schema cases per Python. #153: 30 evolution/query/schema/v0 cases per Python. #44: 19 relationship/decision/schema cases per Python; exact pinned native owner composition passes. Zero skips. Timings, commands, initial failures and limits are in the sprint ledger; combined final artifacts/CI are still separate.

## Blockers, risks, unknowns, and deferred work

Unknown archive profiles and actual private/Empathy acceptance remain separate. Query stores remain optional ordinary generated caches; broader workload/native/confidential/runtime assurance is unperformed. Unsupported claim/component/projection relationship kinds and private/inherited ADR authority need actual contracts. Historical ADR dispositions, real providers/models and release/local setup stay parked.

## Next dependency-ready work

Push the #44 public-relationship draft on #153, qualify the combined checkout from source/installed artifacts, update live issue/CI evidence and hand off for maintainer review. No automatic merge or local/private setup.

## Parallel changes and reconciliation

New draft stack #152 → #153 → #44 child extends the unmerged #148–#151 ancestry. Preserve all old worktrees and four root WIP entries. The final child is the combined checkout; no force-push, reset or automatic merge.

## Privacy and redaction

Synthetic committed inputs only. Private spec bodies, real archives, credentials, source locations and actual consultation packets stay outside the repository. Delivery projection is not a general source-text sanitizer or host isolation guarantee.

## Handoff update protocol

At each checkpoint record branch/PR, commits, exact tests and CI, met/unmet criteria, blockers and next action. Preserve all 44 coverage rows and the eighteen proposed/null-approval ADRs plus six original legacy labels.

## Compaction and supersession

Keep these twelve headings and 16384-byte/240-line bounds. The active sprint supersedes the previous suggested next batch, not its immutable qualification history.
